from pathlib import Path

import pytest

from peracolor.etsy_api import ListingFile, UnsupportedFileTypeError, content_type
from peracolor.replace_listing import SET_WHAT_YOU_GET, WHAT_YOU_GET, ReplacementPlan, replace_files
from peracolor.sizes import ETSY_MAX_FILES


class FakeEtsy:
    """Records file operations and enforces Etsy's five-file and at-least-one-file rules."""

    def __init__(self, existing: int) -> None:
        self.files = [ListingFile(listing_file_id=i, filename=f"old-{i}.pdf", filesize="1 MB") for i in range(existing)]
        self.next_id = 100

    def listing_files(self, shop_id: int, listing_id: int) -> list[ListingFile]:
        return list(self.files)

    def delete_listing_file(self, shop_id: int, listing_id: int, file_id: int) -> None:
        assert len(self.files) > 1, "a digital listing must keep at least one file"
        self.files = [f for f in self.files if f.listing_file_id != file_id]

    def upload_listing_file(self, shop_id: int, listing_id: int, path: Path) -> ListingFile:
        assert len(self.files) < ETSY_MAX_FILES, "Etsy allows at most five files"
        self.next_id += 1
        new = ListingFile(listing_file_id=self.next_id, filename=path.name, filesize="1 MB")
        self.files.append(new)
        return new


@pytest.fixture
def plan() -> ReplacementPlan:
    return ReplacementPlan(listing_id=1, files=[Path(f"new-{i}.zip") for i in range(5)], images=[], what_you_get=SET_WHAT_YOU_GET)


class TestReplaceFiles:
    @pytest.mark.parametrize("existing", [1, 3, 5])
    def test_swaps_all_files_within_etsy_limits(self, plan: ReplacementPlan, existing: int) -> None:
        """Given a listing with old files, when files are replaced, then only the new files remain and limits are never broken."""
        fake = FakeEtsy(existing)

        replace_files(fake, shop_id=9, plan=plan)  # pyright: ignore[reportArgumentType]

        assert sorted(f.filename for f in fake.files) == sorted(p.name for p in plan.files)

    def test_refuses_more_than_five_files(self, plan: ReplacementPlan) -> None:
        """Given six new files, when files are replaced, then it fails before touching the listing."""
        fake = FakeEtsy(3)
        too_many = plan.model_copy(update={"files": [Path(f"f{i}.zip") for i in range(6)]})

        with pytest.raises(ValueError, match="exceeds"):
            replace_files(fake, shop_id=9, plan=too_many)  # pyright: ignore[reportArgumentType]

        assert len(fake.files) == 3


class TestContentType:
    @pytest.mark.parametrize(("name", "expected"), [("a.zip", "application/zip"), ("a.jpg", "image/jpeg"), ("a.pdf", "application/pdf")])
    def test_known_types(self, name: str, expected: str) -> None:
        """Given a deliverable file name, when its content type is resolved, then Etsy gets the right MIME type."""
        assert content_type(Path(name)) == expected

    def test_unknown_type_fails_loudly(self) -> None:
        """Given a file without a recognisable extension, when its content type is resolved, then it raises."""
        with pytest.raises(UnsupportedFileTypeError):
            content_type(Path("mystery"))


def test_what_you_get_block_is_replaced_only_once() -> None:
    """Given a description, when the WHAT YOU GET block is swapped, then the rest of the text is untouched."""
    description = "Intro\n\nWHAT YOU GET\n• old\n\nPERFECT FOR\n• gifts"

    updated = WHAT_YOU_GET.sub(SET_WHAT_YOU_GET + "\n\nPERFECT FOR", description, count=1)

    assert updated.startswith("Intro\n\nWHAT YOU GET\n• Instant download")
    assert updated.endswith("PERFECT FOR\n• gifts")
