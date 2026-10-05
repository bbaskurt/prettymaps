"""Sets of three posters sold as one listing (e.g. London: Big Ben, Buckingham Palace, Tower Bridge).

Etsy allows five files of up to 20 MB each, and one map's ISO A and 2:3 masters
together are ~16 MB. Each set therefore ships five files:

    one zip per map with its ISO A and 2:3 masters   (3 files)
    one zip with all three maps at 3:4                (1 file)
    one zip with all three maps at 4:5                (1 file)

The individual places must already be rendered (see render.py).
"""

import zipfile
from pathlib import Path

import yaml
from loguru import logger
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from peracolor.export import FileTooLargeError, poster_jpeg
from peracolor.mockup import CANVAS_SIZE, draw_sideboard, drop_shadow, framed_poster, sizes_guide, wall_background
from peracolor.models import LatLon, Place, Slug
from peracolor.poster import compose_poster
from peracolor.render import load_render_meta, raw_png_path
from peracolor.sizes import ETSY_MAX_FILE_BYTES, PRINT_SPECS, PrintFormat

SET_SIZE = 3
PER_MAP_FORMATS = (PrintFormat.ISO_A, PrintFormat.RATIO_2X3)
BUNDLE_FORMATS = (PrintFormat.RATIO_3X4, PrintFormat.RATIO_4X5)
SET_FORMATS = PER_MAP_FORMATS + BUNDLE_FORMATS
# Each set zip must fit Etsy's per-file limit; the budget is split evenly between entries.
SET_FILE_BUDGET_BYTES = ETSY_MAX_FILE_BYTES
SET_JPEG_QUALITIES = (92, 88, 84, 80)
PREVIEW_SIZE = (1200, 1500)
TRIPTYCH_SIDE_MARGIN = 0.06
TRIPTYCH_MAX_HEIGHT = 0.5


class PosterSet(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: Slug
    title: str
    places: list[Slug] = Field(min_length=SET_SIZE, max_length=SET_SIZE)


class SetsFile(BaseModel):
    sets: list[PosterSet]


class SetMember(BaseModel):
    """A rendered place ready to be composed into posters."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    place: Place
    centre: LatLon
    raw_map: Image.Image


def load_sets(path: Path) -> list[PosterSet]:
    return SetsFile.model_validate(yaml.safe_load(path.read_text())).sets


def load_member(place: Place, raw_dir: Path) -> SetMember:
    with Image.open(raw_png_path(raw_dir, place.slug)) as opened:
        raw_map = opened.convert("RGBA")
    return SetMember(place=place, centre=load_render_meta(raw_dir, place.slug).centre, raw_map=raw_map)


def write_zip(path: Path, entries: list[tuple[str, bytes]]) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        for name, data in entries:
            archive.writestr(name, data)
    if path.stat().st_size > SET_FILE_BUDGET_BYTES:
        raise FileTooLargeError(f"{path} exceeds the {SET_FILE_BUDGET_BYTES} byte set file budget")
    logger.info("Wrote {} ({:.1f} MB)", path.name, path.stat().st_size / 1e6)
    return path


def member_entry(member: SetMember, print_format: PrintFormat, max_bytes: int) -> tuple[str, bytes]:
    name = f"{member.place.slug}-{PRINT_SPECS[print_format].file_stem}.jpg"
    return name, poster_jpeg(member.raw_map, member.place, member.centre, print_format, max_bytes, SET_JPEG_QUALITIES)


def write_set_files(poster_set: PosterSet, members: list[SetMember], files_dir: Path) -> None:
    files_dir.mkdir(parents=True, exist_ok=True)
    # Leave a little room for zip headers when splitting the budget.
    per_map_budget = (SET_FILE_BUDGET_BYTES - 10_000) // len(PER_MAP_FORMATS)
    bundle_budget = (SET_FILE_BUDGET_BYTES - 10_000) // len(members)
    for member in members:
        entries = [member_entry(member, print_format, per_map_budget) for print_format in PER_MAP_FORMATS]
        write_zip(files_dir / f"{member.place.slug}-a-sizes-and-2x3.zip", entries)
    for print_format in BUNDLE_FORMATS:
        entries = [member_entry(member, print_format, bundle_budget) for member in members]
        write_zip(files_dir / f"{poster_set.slug}-{PRINT_SPECS[print_format].file_stem}.zip", entries)


def triptych_frame_height(posters: list[Image.Image], gap: int) -> int:
    """Tallest frame height at which all three frames fit inside the canvas margins."""
    usable_width = CANVAS_SIZE[0] * (1 - 2 * TRIPTYCH_SIDE_MARGIN) - gap * (len(posters) - 1)
    width_per_unit_height = sum(framed_poster(poster, 1000).width for poster in posters) / 1000
    return min(round(CANVAS_SIZE[1] * TRIPTYCH_MAX_HEIGHT), int(usable_width / width_per_unit_height))


def triptych_with_centres(posters: list[Image.Image]) -> tuple[Image.Image, list[float]]:
    """Three framed posters side by side on a sideboard, plus each frame's horizontal centre."""
    canvas = wall_background(CANVAS_SIZE)
    sideboard_top = draw_sideboard(canvas)
    gap = round(CANVAS_SIZE[0] * 0.035)
    frames = [framed_poster(poster, frame_height=triptych_frame_height(posters, gap)) for poster in posters]
    left = (CANVAS_SIZE[0] - sum(frame.width for frame in frames) - gap * (len(frames) - 1)) // 2
    centres = []
    for frame in frames:
        top = sideboard_top - frame.height + 6
        drop_shadow(canvas, (left, top, left + frame.width, top + frame.height), (16, 14))
        canvas.paste(frame, (left, top))
        centres.append(left + frame.width / 2)
        left += frame.width + gap
    return canvas, centres


def triptych_mockup(posters: list[Image.Image]) -> Image.Image:
    return triptych_with_centres(posters)[0]


def flat_trio(posters: list[Image.Image]) -> Image.Image:
    canvas = Image.new("RGB", CANVAS_SIZE, (246, 243, 237))
    poster_height = round(CANVAS_SIZE[1] * 0.78)
    scaled = [poster.resize((round(poster_height * poster.width / poster.height), poster_height), Image.Resampling.LANCZOS) for poster in posters]
    gap = round(CANVAS_SIZE[0] * 0.03)
    left = (CANVAS_SIZE[0] - sum(image.width for image in scaled) - gap * (len(scaled) - 1)) // 2
    top = (CANVAS_SIZE[1] - poster_height) // 2
    for image in scaled:
        drop_shadow(canvas, (left, top, left + image.width, top + image.height), (10, 10))
        canvas.paste(image, (left, top))
        left += image.width + gap
    return canvas


def write_set_images(members: list[SetMember], images_dir: Path) -> None:
    images_dir.mkdir(parents=True, exist_ok=True)
    posters = [compose_poster(member.raw_map, member.place, member.centre, PREVIEW_SIZE) for member in members]
    triptych_mockup(posters).save(images_dir / "01-mockup.jpg", quality=90)
    flat_trio(posters).save(images_dir / "02-posters.jpg", quality=90)
    sizes_guide([PRINT_SPECS[print_format] for print_format in SET_FORMATS]).save(images_dir / "03-sizes.jpg", quality=90)


def compose_set(poster_set: PosterSet, places: dict[str, Place], raw_dir: Path, output_dir: Path) -> Path:
    unknown = [slug for slug in poster_set.places if slug not in places]
    if unknown:
        raise ValueError(f"Set {poster_set.slug} refers to unknown places: {unknown}")
    members = [load_member(places[slug], raw_dir) for slug in poster_set.places]
    set_dir = output_dir / "sets" / poster_set.slug
    write_set_files(poster_set, members, set_dir / "files")
    write_set_images(members, set_dir / "images")
    return set_dir

