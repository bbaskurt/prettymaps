"""Package one place in three colour versions (Original, Mono, Sage & Terracotta) as a single listing.

Every buyer receives all three colourways. Etsy allows five files of up to 20 MB,
so the download is laid out like a set:

    one zip per colourway with its ISO A and 2:3 masters   (3 files)
    one zip with all three colourways at 3:4                 (1 file)
    one zip with all three colourways at 4:5                 (1 file)

Listing photos: a labelled mockup of all three framed side by side, one flat
poster per colourway, and the sizes guide.
"""

from pathlib import Path

from PIL import Image, ImageDraw

from peracolor.export import FLAT_PREVIEW_SIZE
from peracolor.mockup import CANVAS_SIZE, sizes_guide
from peracolor.models import Place
from peracolor.palettes import PaletteName, palette_variant
from peracolor.poster import compose_poster
from peracolor.sets import (
    BUNDLE_FORMATS,
    PER_MAP_FORMATS,
    PREVIEW_SIZE,
    SET_FILE_BUDGET_BYTES,
    SET_FORMATS,
    SetMember,
    load_member,
    member_entry,
    triptych_with_centres,
    write_zip,
)
from peracolor.sizes import PRINT_SPECS
from peracolor.style import FONT_BODY, FONT_TITLE, INK
from peracolor.typography import draw_tracked_centred, load_font

COLOURWAYS: tuple[PaletteName, ...] = (PaletteName.ORIGINAL, PaletteName.MONO, PaletteName.SAGE_TERRACOTTA)
COLOURWAY_LABELS: dict[PaletteName, str] = {
    PaletteName.MONO: "Mono",
    PaletteName.ORIGINAL: "Original",
    PaletteName.SAGE_TERRACOTTA: "Sage & Terracotta",
}
HEADLINE = "3 COLOUR VERSIONS INCLUDED"


def colourway_members(place: Place, raw_dir: Path) -> list[SetMember]:
    return [load_member(palette_variant(place, name), raw_dir) for name in COLOURWAYS]


def file_label(name: PaletteName) -> str:
    return COLOURWAY_LABELS[name].lower().replace(" & ", "-and-").replace(" ", "-")


def write_colourway_files(place: Place, members: list[SetMember], files_dir: Path) -> None:
    files_dir.mkdir(parents=True, exist_ok=True)
    per_map_budget = (SET_FILE_BUDGET_BYTES - 10_000) // len(PER_MAP_FORMATS)
    bundle_budget = (SET_FILE_BUDGET_BYTES - 10_000) // len(members)
    for name, member in zip(COLOURWAYS, members, strict=True):
        entries = [member_entry(member, print_format, per_map_budget) for print_format in PER_MAP_FORMATS]
        write_zip(files_dir / f"{place.slug}-{file_label(name)}-a-sizes-and-2x3.zip", entries)
    for print_format in BUNDLE_FORMATS:
        entries = [member_entry(member, print_format, bundle_budget) for member in members]
        write_zip(files_dir / f"{place.slug}-all-colours-{PRINT_SPECS[print_format].file_stem}.zip", entries)


def labelled_triptych(posters: list[Image.Image]) -> Image.Image:
    """Three framed colourways with a headline on the wall and a label under each frame."""
    canvas, centres = triptych_with_centres(posters)
    draw = ImageDraw.Draw(canvas)
    width, height = CANVAS_SIZE
    draw_tracked_centred(draw, HEADLINE, load_font(FONT_TITLE, 96), width / 2, round(height * 0.16), 22, INK)
    label_font = load_font(FONT_BODY, 56)
    label_y = round(height * 0.93)
    for name, centre_x in zip(COLOURWAYS, centres, strict=True):
        draw_tracked_centred(draw, COLOURWAY_LABELS[name].upper(), label_font, centre_x, label_y, 6, INK)
    return canvas


def write_colourway_images(members: list[SetMember], images_dir: Path) -> None:
    images_dir.mkdir(parents=True, exist_ok=True)
    previews = [compose_poster(member.raw_map, member.place, member.centre, PREVIEW_SIZE) for member in members]
    labelled_triptych(previews).save(images_dir / "01-all-colours.jpg", quality=90)
    for index, (name, member) in enumerate(zip(COLOURWAYS, members, strict=True), start=2):
        poster = compose_poster(member.raw_map, member.place, member.centre, FLAT_PREVIEW_SIZE)
        poster.save(images_dir / f"{index:02d}-{file_label(name)}.jpg", quality=90)
    sizes_guide([PRINT_SPECS[print_format] for print_format in SET_FORMATS]).save(images_dir / "05-sizes.jpg", quality=90)


def compose_colourways(place: Place, raw_dir: Path, output_dir: Path) -> Path:
    members = colourway_members(place, raw_dir)
    place_dir = output_dir / "colourways" / place.slug
    write_colourway_files(place, members, place_dir / "files")
    write_colourway_images(members, place_dir / "images")
    return place_dir
