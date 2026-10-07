from pathlib import Path

import pytest

from peracolor.models import Place, load_places
from peracolor.publish_places import COUNTRY_SECTION_IDS, EUROPE_SECTION_ID, record_listing, section_for

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def place() -> Place:
    return load_places(REPO_ROOT / "places.yaml")[0]


class TestSectionFor:
    @pytest.mark.parametrize(
        ("country", "expected"),
        [
            ("France", COUNTRY_SECTION_IDS["France"]),
            ("Italy", EUROPE_SECTION_ID),
            ("South Korea", None),
            ("USA", COUNTRY_SECTION_IDS["USA"]),
        ],
    )
    def test_country_maps_to_shop_section(self, place: Place, country: str, expected: int | None) -> None:
        """Given a place in a country, when its section is chosen, then it lands in the matching shop section."""
        assert section_for(place.model_copy(update={"country": country})) == expected


class TestRecordListing:
    def test_new_listing_is_added_sorted_with_header_kept(self, tmp_path: Path) -> None:
        """Given the listings file, when a new listing is recorded, then it is inserted in slug order and comments survive."""
        path = tmp_path / "etsy_listings.yaml"
        path.write_text("# Listing ids.\nathens: 2\nzurich: 3\n")

        record_listing(path, "venice", 1)

        assert path.read_text() == "# Listing ids.\nathens: 2\nvenice: 1\nzurich: 3\n"
