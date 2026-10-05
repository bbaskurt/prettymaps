import pytest

from peracolor.listing import (
    TAG_COUNT,
    TAG_MAX_CHARS,
    TITLE_MAX_CHARS,
    build_description,
    build_listing,
    build_tags,
    build_title,
)
from peracolor.models import LatLon, Place


@pytest.fixture
def place() -> Place:
    return Place(
        slug="lisbon-bairro-alto",
        query="Bairro Alto, Lisbon, Portugal",
        title="Lisbon",
        city="Lisbon",
        country="Portugal",
        osm_region="europe/portugal",
        subtitle="Bairro Alto",
        centre=LatLon(lat=38.717, lon=-9.148),
        tag_hints=["portugal map"],
    )


class TestTitle:
    def test_title_leads_with_city_keyword(self, place: Place) -> None:
        """Given a place, when the title is built, then it starts with '<City> Map Print'."""
        assert build_title(place).startswith("Lisbon Map Print, Bairro Alto Circle City Map")

    def test_long_names_are_trimmed_to_etsy_limit(self, place: Place) -> None:
        """Given very long names, when the title is built, then it fits in 140 characters and keeps the city keyword."""
        long_place = place.model_copy(
            update={"city": "Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch", "subtitle": "X" * 40}
        )
        title = build_title(long_place)
        assert len(title) <= TITLE_MAX_CHARS
        assert title.startswith("Llanfairpwll")


class TestTags:
    def test_exactly_thirteen_short_unique_tags(self, place: Place) -> None:
        """Given a place, when tags are built, then there are 13 unique tags of at most 20 characters."""
        tags = build_tags(place)
        assert len(tags) == TAG_COUNT
        assert len(set(tags)) == TAG_COUNT
        assert all(len(tag) <= TAG_MAX_CHARS for tag in tags)

    def test_accents_are_folded_and_overlong_tags_dropped(self, place: Place) -> None:
        """Given accented and overlong hints, when tags are built, then accents are stripped and long hints skipped."""
        accented = place.model_copy(update={"subtitle": "Gràcia", "tag_hints": ["a" * 21, "señorita café"]})
        tags = build_tags(accented)
        assert "gracia map" in tags
        assert "senorita cafe" in tags
        assert "a" * 21 not in tags


class TestDescription:
    def test_description_mentions_only_this_place(self, place: Place) -> None:
        """Given a Lisbon place, when the description is built, then it names Lisbon and no other shop city."""
        description = build_listing(place).description
        assert "Bairro Alto, Lisbon, Portugal" in description
        assert "Eiffel" not in description and "New York" not in description

    def test_description_lists_iso_and_us_sizes_and_digital_notice(self, place: Place) -> None:
        """Given any place, when the description is built, then it lists A-series and US sizes and says digital only."""
        description = build_listing(place).description
        assert "A4" in description and '24x36"' in description
        assert "No physical item will be shipped" in description


def test_description_leaves_map_data_credit_to_the_shop_page(place: Place) -> None:
    """Given any place, when its description is built, then it does not mention OpenStreetMap (credited on the shop page)."""
    assert "OpenStreetMap" not in build_description(place)
