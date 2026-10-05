"""Alternative map colour palettes, used to compare lighter looks against the original.

A palette sets the colours of each map layer; the layer structure (what is
drawn) stays the same as the original lite style, so palettes can be compared
like for like on the same place.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from peracolor.models import Place
from peracolor.style import LITE_STYLE


class PaletteName(StrEnum):
    BLUSH = "blush"
    MONO = "mono"
    ORIGINAL = "original"
    PASTEL = "pastel"
    SAGE_TERRACOTTA = "sage-terracotta"


class Palette(BaseModel):
    model_config = ConfigDict(frozen=True)

    land: str
    buildings: tuple[str, ...]
    building_edge: str
    streets: str
    water: str
    water_hatch: str | None
    green: str
    forest: str
    outline: str
    land_hatch: bool


PALETTES: dict[PaletteName, Palette] = {
    PaletteName.BLUSH: Palette(
        land="#FFFDFB",
        buildings=("#F2D0C9", "#E9B7AE", "#CFE0E8"),
        building_edge="#B9A8A4",
        streets="#4A5560",
        water="#D6E9F2",
        water_hatch=None,
        green="#E3EEDD",
        forest="#C7DCC0",
        outline="#9AA3AA",
        land_hatch=False,
    ),
    PaletteName.MONO: Palette(
        land="#FAF7F2",
        buildings=("#E8E1D6", "#DCD3C5", "#CDC2B2"),
        building_edge="#B3A897",
        streets="#3A3A3A",
        water="#DCE6EA",
        water_hatch=None,
        green="#E4E8DC",
        forest="#D2D9C8",
        outline="#8E8E8E",
        land_hatch=False,
    ),
    PaletteName.ORIGINAL: Palette(
        land="#F2F4CB",
        buildings=("#C5283D", "#E9724C", "#FFC857"),
        building_edge="#2F3737",
        streets="#2F3737",
        water="#a1e3ff",
        water_hatch="#85c9e6",
        green="#D0F1BF",
        forest="#64B96A",
        outline="#2F3737",
        land_hatch=True,
    ),
    PaletteName.PASTEL: Palette(
        land="#FBF8F1",
        buildings=("#F4C7AB", "#EFA8A0", "#F9E2AE", "#B8D8D0"),
        building_edge="#A8968A",
        streets="#6B6B6B",
        water="#CFE8F3",
        water_hatch=None,
        green="#DCEBD5",
        forest="#BFD9B5",
        outline="#8C8C8C",
        land_hatch=False,
    ),
    PaletteName.SAGE_TERRACOTTA: Palette(
        land="#F6F1E7",
        buildings=("#D9A48F", "#C98B6B", "#E6CBA8", "#A9B8A0"),
        building_edge="#8F7A6A",
        streets="#5E5A54",
        water="#BFD7DA",
        water_hatch=None,
        green="#C9D6BF",
        forest="#A9BD9C",
        outline="#7A746C",
        land_hatch=False,
    ),
}


def style_for(palette: Palette) -> dict[str, dict]:
    """prettymaps style dict for a palette, keeping every non-colour setting of the original."""
    water = {"fc": palette.water, "ec": palette.outline, "lw": 1, "hatch": "ooo..." if palette.water_hatch else ""}
    if palette.water_hatch:
        water["hatch_c"] = palette.water_hatch
    return {
        "background": dict(LITE_STYLE["background"]),
        "perimeter": {**LITE_STYLE["perimeter"], "fc": palette.land, "hatch": "ooo..." if palette.land_hatch else ""},
        "green": {"fc": palette.green, "ec": palette.outline, "lw": 1},
        "forest": {"fc": palette.forest, "ec": palette.outline, "lw": 1},
        "water": water,
        "parking": {"fc": palette.land, "ec": palette.outline, "lw": 1},
        "streets": {**LITE_STYLE["streets"], "fc": palette.streets, "ec": palette.streets},
        "building": {"palette": list(palette.buildings), "ec": palette.building_edge, "lw": 0.5},
    }


def palette_variant(place: Place, palette: PaletteName) -> Place:
    """The place under a palette-specific slug, so variant files never overwrite the original's."""
    if palette == PaletteName.ORIGINAL:
        return place
    return place.model_copy(update={"slug": f"{place.slug}-{palette.value}"})
