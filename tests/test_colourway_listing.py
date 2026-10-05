from pathlib import Path

import pytest

from peracolor.colourway_listing import (
    ALL_VERSIONS_LINE,
    COLOURWAY_WHAT_YOU_GET,
    CopyRewriteError,
    colourway_description,
    colourway_title,
    new_listing_copy,
)
from peracolor.models import Place, load_places
from peracolor.colourways import COLOURWAY_LABELS, COLOURWAYS, file_label
from peracolor.palettes import PaletteName

REPO_ROOT = Path(__file__).resolve().parent.parent

DESCRIPTION = (
    "A colourful circle map of Tower Bridge, London, drawn from real data.\n\n"
    "WHAT YOU GET\n• old sizes\n\nPERFECT FOR\n• gifts"
)


class TestColourwayTitle:
    def test_adds_colour_versions_before_gift_phrase(self) -> None:
        """Given a 'Colorful' title, when rewritten, then the adjective goes and '3 Colour Versions' is its own phrase."""
        title = "London Map Print, Tower Bridge Circle City Map, Colorful London Wall Art, Travel Gift (Digital Download)"

        assert colourway_title(title) == (
            "London Map Print, Tower Bridge Circle City Map, London Wall Art, 3 Colour Versions, Travel Gift (Digital Download)"
        )

    def test_is_idempotent(self) -> None:
        """Given an already rewritten title, when rewritten again, then it is unchanged."""
        title = "Paris Map Print, Louvre Circle City Map, France Wall Art, 3 Colour Versions, Travel Gift (Digital Download)"

        assert colourway_title(title) == title

    def test_unexpected_title_fails_loudly(self) -> None:
        """Given a title without 'Colorful', when rewritten, then it raises instead of guessing."""
        with pytest.raises(CopyRewriteError):
            colourway_title("Some Other Product")


class TestColourwayDescription:
    def test_leads_with_all_versions_line_and_new_block(self) -> None:
        """Given an existing description, when rewritten, then buyers first read that all 3 versions are included."""
        result = colourway_description(DESCRIPTION)

        assert result.startswith(ALL_VERSIONS_LINE)
        assert "A circle map of Tower Bridge" in result
        assert COLOURWAY_WHAT_YOU_GET in result
        assert "old sizes" not in result
        assert result.endswith("PERFECT FOR\n• gifts")

    def test_is_idempotent(self) -> None:
        """Given an already rewritten description, when rewritten again, then it is unchanged."""
        once = colourway_description(DESCRIPTION)

        assert colourway_description(once) == once


def test_every_colourway_has_a_label_and_distinct_file_name() -> None:
    """Given the three colourways, when file labels are built, then each is unique and readable."""
    labels = [file_label(name) for name in COLOURWAYS]

    assert set(COLOURWAYS) == {PaletteName.ORIGINAL, PaletteName.MONO, PaletteName.SAGE_TERRACOTTA}
    assert set(COLOURWAYS) <= set(COLOURWAY_LABELS)
    assert labels == ["original", "mono", "sage-and-terracotta"]


class TestNewListingCopy:
    @pytest.mark.parametrize("place", load_places(REPO_ROOT / "places.yaml"), ids=lambda p: p.slug)
    def test_every_place_fits_etsy_limits(self, place: Place) -> None:
        """Given any place, when its new listing copy is built, then it fits Etsy's title and tag rules."""
        copy = new_listing_copy(place)

        assert len(copy.title) <= 140
        assert "3 Colour Versions" in copy.title
        assert len(copy.tags) == 13
        assert len(set(copy.tags)) == 13
        assert all(len(tag) <= 20 for tag in copy.tags)

    def test_description_leads_with_all_versions(self) -> None:
        """Given a place, when its description is built, then buyers first read that all 3 versions are included."""
        place = load_places(REPO_ROOT / "places.yaml")[0]

        description = new_listing_copy(place).description

        assert description.startswith(ALL_VERSIONS_LINE)
        assert COLOURWAY_WHAT_YOU_GET in description
        assert "OpenStreetMap" not in description
