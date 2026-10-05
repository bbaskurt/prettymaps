"""PeraColor "lite" map style and poster palette.

Layers and colours mirror the `lite` branch of sample_live_colors.py so new
listings match the existing shop. The background patch is made transparent
and the circle itself (the perimeter layer) carries the land fill, so the raw
render can be composited onto any poster colour.
"""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONT_TITLE = ASSETS_DIR / "Montserrat-SemiBold.ttf"
FONT_BODY = ASSETS_DIR / "Montserrat-Medium.ttf"
FONT_SMALL = ASSETS_DIR / "Montserrat-Regular.ttf"

LAND_COLOUR = "#F2F4CB"
POSTER_BACKGROUND = (237, 231, 218)
INK = (47, 55, 55)
MUTED_INK = (110, 112, 105)

STREET_WIDTHS = {
    "motorway": 5,
    "trunk": 5,
    "primary": 4.5,
    "secondary": 4,
    "tertiary": 3.5,
    "residential": 3,
}

LITE_LAYERS: dict[str, dict] = {
    "building": {"tags": {"building": True}},
    "forest": {"tags": {"landuse": "forest"}},
    "green": {
        "tags": {
            "landuse": "grass",
            "leisure": "park",
            "natural": ["island", "wood"],
        }
    },
    "parking": {
        "tags": {
            "amenity": "parking",
            "highway": "pedestrian",
            "man_made": "pier",
        }
    },
    "streets": {"width": STREET_WIDTHS},
    "water": {"tags": {"natural": ["bay", "water"]}},
}

LITE_STYLE: dict[str, dict] = {
    "background": {"fc": "none", "ec": "none", "lw": 0, "hatch": ""},
    "perimeter": {
        "fill": True,
        "fc": LAND_COLOUR,
        "ec": "#dadbc1",
        "lw": 0,
        "hatch": "ooo...",
        "zorder": 0,
    },
    "green": {"fc": "#D0F1BF", "ec": "#2F3737", "lw": 1},
    "forest": {"fc": "#64B96A", "ec": "#2F3737", "lw": 1},
    "water": {
        "fc": "#a1e3ff",
        "ec": "#2F3737",
        "hatch": "ooo...",
        "hatch_c": "#85c9e6",
        "lw": 1,
    },
    "parking": {"fc": LAND_COLOUR, "ec": "#2F3737", "lw": 1},
    "streets": {"fc": "#2F3737", "ec": "#475657", "alpha": 1, "lw": 0},
    "building": {
        "palette": ["#C5283D", "#E9724C", "#FFC857"],
        "ec": "#2F3737",
        "lw": 0.5,
    },
}
