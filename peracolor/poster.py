"""Compose print-ready posters: circle map, title block and brand mark.

All measurements scale with the poster width so every print ratio shares the
same look. The OpenStreetMap attribution is given in the shop and listing
descriptions rather than printed on the poster.
"""

from pydantic import BaseModel, ConfigDict
from PIL import Image, ImageDraw

from peracolor.models import LatLon, Place
from peracolor.style import FONT_BODY, FONT_SMALL, FONT_TITLE, INK, MUTED_INK, POSTER_BACKGROUND
from peracolor.typography import cap_height, draw_tracked, draw_tracked_centred, load_font, tracked_width

BRAND = "PERACOLOR"


class PosterLayout(BaseModel):
    """Pixel geometry of one poster, derived from its width and height."""

    model_config = ConfigDict(frozen=True)

    width: int
    height: int
    circle_diameter: int
    circle_top: int
    title_size: int
    subtitle_size: int
    coords_size: int
    credit_size: int


def plan_layout(width: int, height: int) -> PosterLayout:
    """Centre the circle-plus-text block, nudged slightly above the middle."""
    diameter = round(min(0.74 * width, 0.62 * height))
    title_size = round(0.075 * width)
    subtitle_size = round(0.024 * width)
    coords_size = round(0.018 * width)
    block = diameter + 0.06 * width + title_size + 0.05 * width + subtitle_size + coords_size
    top = round(max((height - block) / 2 - 0.02 * height, (width - diameter) / 2))
    return PosterLayout(
        width=width,
        height=height,
        circle_diameter=diameter,
        circle_top=top,
        title_size=title_size,
        subtitle_size=subtitle_size,
        coords_size=coords_size,
        credit_size=max(round(0.011 * width), 8),
    )


def format_coordinates(centre: LatLon) -> str:
    lat_hemisphere = "N" if centre.lat >= 0 else "S"
    lon_hemisphere = "E" if centre.lon >= 0 else "W"
    return f"{abs(centre.lat):.4f}° {lat_hemisphere}   {abs(centre.lon):.4f}° {lon_hemisphere}"


def subtitle_line(place: Place) -> str:
    parts = [place.subtitle, place.country] if place.subtitle else [place.country]
    return "  ·  ".join(part.upper() for part in parts if part)


def paste_circle(poster: Image.Image, raw_map: Image.Image, layout: PosterLayout) -> None:
    size = layout.circle_diameter
    circle = raw_map.resize((size, size), Image.Resampling.LANCZOS)
    left = (layout.width - size) // 2
    poster.paste(circle, (left, layout.circle_top), circle)


def draw_title_block(draw: ImageDraw.ImageDraw, place: Place, centre: LatLon, layout: PosterLayout) -> None:
    mid_x = layout.width / 2
    title_font = load_font(FONT_TITLE, layout.title_size)
    title_baseline = layout.circle_top + layout.circle_diameter + 0.06 * layout.width + cap_height(title_font)
    draw_tracked_centred(draw, place.title.upper(), title_font, mid_x, title_baseline, 0.25 * layout.title_size, INK)

    subtitle_font = load_font(FONT_BODY, layout.subtitle_size)
    subtitle_baseline = title_baseline + 0.045 * layout.width + cap_height(subtitle_font)
    draw_tracked_centred(draw, subtitle_line(place), subtitle_font, mid_x, subtitle_baseline, 0.3 * layout.subtitle_size, INK)

    coords_font = load_font(FONT_SMALL, layout.coords_size)
    coords_baseline = subtitle_baseline + 0.022 * layout.width + cap_height(coords_font)
    draw_tracked_centred(draw, format_coordinates(centre), coords_font, mid_x, coords_baseline, 0.15 * layout.coords_size, MUTED_INK)


def draw_brand(draw: ImageDraw.ImageDraw, layout: PosterLayout) -> None:
    font = load_font(FONT_SMALL, layout.credit_size)
    margin = 0.045 * layout.width
    baseline = layout.height - margin
    brand_tracking = 0.35 * layout.credit_size
    brand_x = layout.width - margin - tracked_width(BRAND, font, brand_tracking)
    draw_tracked(draw, BRAND, font, brand_x, baseline, brand_tracking, MUTED_INK)


def compose_poster(raw_map: Image.Image, place: Place, centre: LatLon, size: tuple[int, int]) -> Image.Image:
    layout = plan_layout(*size)
    poster = Image.new("RGB", size, POSTER_BACKGROUND)
    paste_circle(poster, raw_map, layout)
    draw = ImageDraw.Draw(poster)
    draw_title_block(draw, place, centre, layout)
    draw_brand(draw, layout)
    return poster
