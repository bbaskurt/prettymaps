"""Write everything one listing needs into output/<slug>/.

    files/   up to five Etsy digital files (JPGs, or a zip for small sizes)
    images/  listing photos: framed mockup, flat poster, sizes guide
    listing.json   title, tags and description
"""

import io
import zipfile
from pathlib import Path

from loguru import logger
from PIL import Image

from peracolor.listing import build_listing
from peracolor.mockup import framed_mockup, sizes_guide
from peracolor.models import LatLon, Place
from peracolor.poster import compose_poster
from peracolor.render import load_render_meta, raw_png_path
from peracolor.sizes import (
    DELIVERABLES,
    ETSY_MAX_FILE_BYTES,
    ETSY_MAX_FILES,
    PRINT_DPI,
    PRINT_SPECS,
    Deliverable,
    PrintFormat,
)

JPEG_QUALITIES = (92, 88, 84, 80)
PREVIEW_SIZE = (1600, 2000)
FLAT_PREVIEW_SIZE = (1600, 2400)


class FileTooLargeError(RuntimeError):
    """A deliverable cannot be squeezed under Etsy's 20 MB per-file limit."""


def encode_jpeg(
    image: Image.Image,
    label: str,
    max_bytes: int = ETSY_MAX_FILE_BYTES,
    qualities: tuple[int, ...] = JPEG_QUALITIES,
) -> bytes:
    """Highest quality that fits `max_bytes`; fail loudly if none does."""
    for quality in qualities:
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=quality, dpi=(PRINT_DPI, PRINT_DPI), optimize=True)
        if buffer.tell() <= max_bytes:
            return buffer.getvalue()
        logger.warning("{} is {:.1f} MB at quality {}", label, buffer.tell() / 1e6, quality)
    raise FileTooLargeError(f"{label} exceeds {max_bytes} bytes at every quality")


def poster_jpeg(
    raw_map: Image.Image,
    place: Place,
    centre: LatLon,
    print_format: PrintFormat,
    max_bytes: int = ETSY_MAX_FILE_BYTES,
    qualities: tuple[int, ...] = JPEG_QUALITIES,
) -> bytes:
    spec = PRINT_SPECS[print_format]
    poster = compose_poster(raw_map, place, centre, spec.pixels)
    return encode_jpeg(poster, f"{place.slug}/{spec.file_stem}", max_bytes, qualities)


def write_deliverable(deliverable: Deliverable, raw_map: Image.Image, place: Place, centre: LatLon, files_dir: Path) -> Path:
    stem = f"{place.slug}-{deliverable.name}"
    if not deliverable.is_zip:
        path = files_dir / f"{stem}.jpg"
        path.write_bytes(poster_jpeg(raw_map, place, centre, deliverable.formats[0]))
    else:
        path = files_dir / f"{stem}.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
            for print_format in deliverable.formats:
                name = f"{place.slug}-{PRINT_SPECS[print_format].file_stem}.jpg"
                archive.writestr(name, poster_jpeg(raw_map, place, centre, print_format))
    if path.stat().st_size > ETSY_MAX_FILE_BYTES:
        raise FileTooLargeError(f"{path} exceeds Etsy's per-file limit")
    logger.info("Wrote {} ({:.1f} MB)", path.name, path.stat().st_size / 1e6)
    return path


def write_images(raw_map: Image.Image, place: Place, centre: LatLon, images_dir: Path) -> None:
    images_dir.mkdir(parents=True, exist_ok=True)
    preview = compose_poster(raw_map, place, centre, PREVIEW_SIZE)
    framed_mockup(preview).save(images_dir / "01-mockup.jpg", quality=90)
    compose_poster(raw_map, place, centre, FLAT_PREVIEW_SIZE).save(images_dir / "02-poster.jpg", quality=90)
    sizes_guide().save(images_dir / "03-sizes.jpg", quality=90)


def compose_place(place: Place, raw_dir: Path, output_dir: Path) -> Path:
    if len(DELIVERABLES) > ETSY_MAX_FILES:
        raise ValueError(f"Etsy allows at most {ETSY_MAX_FILES} digital files per listing")
    place_dir = output_dir / place.slug
    files_dir = place_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    centre = load_render_meta(raw_dir, place.slug).centre
    with Image.open(raw_png_path(raw_dir, place.slug)) as opened:
        raw_map = opened.convert("RGBA")
    for deliverable in DELIVERABLES:
        write_deliverable(deliverable, raw_map, place, centre, files_dir)
    write_images(raw_map, place, centre, place_dir / "images")
    return place_dir


def write_listing(place: Place, output_dir: Path) -> Path:
    path = output_dir / place.slug / "listing.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_listing(place).model_dump_json(indent=2))
    return path
