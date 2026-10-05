"""Letter-spaced text drawing helpers shared by posters, mockups and guides."""

from functools import lru_cache
from pathlib import Path

from PIL import ImageDraw, ImageFont

Colour = tuple[int, int, int]


@lru_cache(maxsize=64)
def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def tracked_width(text: str, font: ImageFont.FreeTypeFont, tracking: float) -> float:
    """Width of `text` with `tracking` extra pixels between characters."""
    if not text:
        return 0.0
    glyphs = sum(font.getlength(char) for char in text)
    return glyphs + tracking * (len(text) - 1)


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: float,
    baseline_y: float,
    tracking: float,
    fill: Colour,
) -> None:
    """Draw text starting at x with its baseline at `baseline_y`."""
    cursor = x
    for char in text:
        draw.text((cursor, baseline_y), char, font=font, fill=fill, anchor="ls")
        cursor += font.getlength(char) + tracking


def draw_tracked_centred(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    centre_x: float,
    baseline_y: float,
    tracking: float,
    fill: Colour,
) -> None:
    start = centre_x - tracked_width(text, font, tracking) / 2
    draw_tracked(draw, text, font, start, baseline_y, tracking, fill)


def cap_height(font: ImageFont.FreeTypeFont) -> int:
    left, top, right, bottom = font.getbbox("H", anchor="ls")
    return bottom - top
