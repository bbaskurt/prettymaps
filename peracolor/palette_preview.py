"""Render one place in every palette and lay the posters side by side for comparison."""

from pathlib import Path

from loguru import logger
from PIL import Image, ImageDraw

from peracolor.palettes import PALETTES, PaletteName, style_for
from peracolor.poster import compose_poster
from peracolor.render import render_place_with_style
from peracolor.models import Place
from peracolor.style import FONT_BODY, INK
from peracolor.typography import draw_tracked_centred, load_font

POSTER_PREVIEW_SIZE = (1200, 1800)
LABEL_BAND = 160
SHEET_GAP = 60
SHEET_BACKGROUND = (246, 243, 237)


def render_palette_posters(place: Place, cache_dir: Path, out_dir: Path) -> dict[PaletteName, Image.Image]:
    posters = {}
    for name, palette in PALETTES.items():
        raw_path = render_place_with_style(place, cache_dir, style_for(palette), cache_dir / "palettes" / name / f"{place.slug}.png")
        with Image.open(raw_path) as opened:
            raw_map = opened.convert("RGBA")
        poster = compose_poster(raw_map, place, place.centre, POSTER_PREVIEW_SIZE)
        poster.save(out_dir / f"{place.slug}-{name}.jpg", quality=90)
        posters[name] = poster
        logger.info("Rendered {} in palette {}", place.slug, name)
    return posters


def comparison_sheet(posters: dict[PaletteName, Image.Image]) -> Image.Image:
    width, height = POSTER_PREVIEW_SIZE
    sheet = Image.new("RGB", (len(posters) * (width + SHEET_GAP) + SHEET_GAP, height + LABEL_BAND + SHEET_GAP), SHEET_BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = load_font(FONT_BODY, 64)
    for index, (name, poster) in enumerate(posters.items()):
        left = SHEET_GAP + index * (width + SHEET_GAP)
        draw_tracked_centred(draw, name.upper(), font, left + width / 2, LABEL_BAND - 50, 8, INK)
        sheet.paste(poster, (left, LABEL_BAND))
    return sheet


def preview_palettes(place: Place, cache_dir: Path, output_dir: Path) -> Path:
    out_dir = output_dir / "palettes" / place.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = out_dir / f"{place.slug}-palettes.jpg"
    comparison_sheet(render_palette_posters(place, cache_dir, out_dir)).save(sheet_path, quality=88)
    logger.info("Wrote {}", sheet_path)
    return sheet_path
