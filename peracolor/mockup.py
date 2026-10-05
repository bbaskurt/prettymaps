"""Listing images generated without stock photos.

* A framed poster leaning on a sideboard against a plain wall (image #1).
* A "sizes included" guide, which answers the most common buyer question.

Both are 3000x2400 (5:4), comfortably above Etsy's 2000 px recommendation and
safe for the cropped search thumbnail.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from peracolor.sizes import PRINT_SPECS, PrintSpec
from peracolor.style import FONT_BODY, FONT_SMALL, FONT_TITLE, INK, MUTED_INK, POSTER_BACKGROUND
from peracolor.typography import draw_tracked_centred, load_font

CANVAS_SIZE = (3000, 2400)
WALL_TOP = (236, 231, 223)
WALL_BOTTOM = (220, 213, 202)
SIDEBOARD = (191, 160, 122)
SIDEBOARD_EDGE = (171, 139, 102)
FRAME_OAK = (184, 150, 108)
MAT_WHITE = (250, 249, 246)
SIDEBOARD_TOP_RATIO = 0.83


def wall_background(size: tuple[int, int]) -> Image.Image:
    """Soft vertical gradient with faint noise, so the wall doesn't look digital."""
    width, height = size
    ramp = np.linspace(0, 1, height)[:, None, None]
    top, bottom = np.array(WALL_TOP), np.array(WALL_BOTTOM)
    gradient = top + (bottom - top) * ramp
    noise = np.random.default_rng(7).normal(0, 1.6, (height, width, 1))
    pixels = np.clip(np.broadcast_to(gradient, (height, width, 3)) + noise, 0, 255)
    return Image.fromarray(pixels.astype(np.uint8), "RGB")


def draw_sideboard(canvas: Image.Image) -> int:
    width, height = canvas.size
    top = round(height * SIDEBOARD_TOP_RATIO)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, top, width, height), fill=SIDEBOARD)
    draw.rectangle((0, top, width, top + 18), fill=SIDEBOARD_EDGE)
    return top


def framed_poster(poster: Image.Image, frame_height: int) -> Image.Image:
    """Oak frame with a white mat around the poster."""
    border = round(frame_height * 0.025)
    mat = round(frame_height * 0.06)
    inner_height = frame_height - 2 * (border + mat)
    inner_width = round(inner_height * poster.width / poster.height)
    frame_size = (inner_width + 2 * (border + mat), frame_height)
    frame = Image.new("RGB", frame_size, FRAME_OAK)
    ImageDraw.Draw(frame).rectangle(
        (border, border, frame_size[0] - border - 1, frame_height - border - 1), fill=MAT_WHITE
    )
    artwork = poster.resize((inner_width, inner_height), Image.Resampling.LANCZOS)
    frame.paste(artwork, (border + mat, border + mat))
    return frame


def drop_shadow(canvas: Image.Image, box: tuple[int, int, int, int], offset: tuple[int, int]) -> None:
    shadow = Image.new("L", canvas.size, 0)
    left, top, right, bottom = box
    dx, dy = offset
    ImageDraw.Draw(shadow).rectangle((left + dx, top + dy, right + dx, bottom + dy), fill=110)
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    canvas.paste((60, 50, 40), (0, 0), shadow)


def framed_mockup(poster: Image.Image) -> Image.Image:
    canvas = wall_background(CANVAS_SIZE)
    sideboard_top = draw_sideboard(canvas)
    frame = framed_poster(poster, frame_height=round(CANVAS_SIZE[1] * 0.74))
    left = (CANVAS_SIZE[0] - frame.width) // 2
    top = sideboard_top - frame.height + 6
    drop_shadow(canvas, (left, top, left + frame.width, top + frame.height), (22, 18))
    canvas.paste(frame, (left, top))
    return canvas


DEFAULT_SIZES_FOOTER = "INSTANT DIGITAL DOWNLOAD  ·  300 DPI  ·  NO PHYSICAL ITEM SHIPPED"


def sizes_guide(specs: list[PrintSpec] | None = None, footer: str = DEFAULT_SIZES_FOOTER) -> Image.Image:
    """Grid of included print sizes; defaults to every format a single listing ships."""
    specs = list(PRINT_SPECS.values()) if specs is None else specs
    canvas = Image.new("RGB", CANVAS_SIZE, POSTER_BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    width, height = CANVAS_SIZE
    draw_tracked_centred(draw, "SIZES INCLUDED", load_font(FONT_TITLE, 120), width / 2, 330, 30, INK)
    column_width = width / len(specs)
    heading_font, size_font = load_font(FONT_BODY, 58), load_font(FONT_SMALL, 64)
    for index, spec in enumerate(specs):
        centre_x = column_width * (index + 0.5)
        draw_tracked_centred(draw, spec.label, heading_font, centre_x, 700, 8, MUTED_INK)
        for row, size in enumerate(spec.printable_sizes):
            draw_tracked_centred(draw, size, size_font, centre_x, 860 + row * 130, 4, INK)
    draw_tracked_centred(draw, footer, load_font(FONT_BODY, 52), width / 2, height - 220, 10, INK)
    return canvas
