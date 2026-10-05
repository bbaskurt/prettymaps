import pytest

from peracolor.models import LatLon, Place
from peracolor.palettes import PALETTES, PaletteName, palette_variant, style_for
from peracolor.style import LITE_STYLE


@pytest.fixture
def place() -> Place:
    return Place(
        slug="london-tower-bridge",
        query="Tower Bridge, London",
        title="London",
        city="London",
        country="United Kingdom",
        osm_region="europe/united-kingdom/england/greater-london",
        subtitle="Tower Bridge",
        centre=LatLon(lat=51.5055, lon=-0.0754),
    )


class TestPaletteVariant:
    def test_original_keeps_the_production_slug(self, place: Place) -> None:
        """Given the original palette, when the variant is built, then the place is unchanged."""
        assert palette_variant(place, PaletteName.ORIGINAL) == place

    def test_other_palettes_get_their_own_slug(self, place: Place) -> None:
        """Given a lighter palette, when the variant is built, then its slug is suffixed so files never collide."""
        variant = palette_variant(place, PaletteName.SAGE_TERRACOTTA)

        assert variant.slug == "london-tower-bridge-sage-terracotta"
        assert variant.centre == place.centre


class TestStyleFor:
    @pytest.mark.parametrize("name", list(PaletteName))
    def test_every_palette_styles_every_layer(self, name: PaletteName) -> None:
        """Given any palette, when its style is built, then it covers exactly the original style's layers."""
        assert set(style_for(PALETTES[name])) == set(LITE_STYLE)

    def test_original_palette_matches_shop_colours(self) -> None:
        """Given the original palette, when its style is built, then buildings use the shop's red, orange and yellow."""
        assert style_for(PALETTES[PaletteName.ORIGINAL])["building"]["palette"] == LITE_STYLE["building"]["palette"]
