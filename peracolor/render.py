"""Render raw circle maps from offline OpenStreetMap data and cache them on disk.

Map data comes from Geofabrik regional extracts (see osm_offline.py), so
rendering does not depend on the public Overpass API. Each render is cached
as a transparent, tightly cropped PNG plus a JSON sidecar holding the centre
coordinates used for the poster subtitle.
"""

import time
from copy import deepcopy
from pathlib import Path

import matplotlib
import osmnx as ox
from loguru import logger
from matplotlib import pyplot as plt
from PIL import Image

import prettymaps
from peracolor.models import LatLon, Place, RenderMeta
from peracolor.osm_offline import bbox_around, ensure_region_pbf, extract_area, offline_prettymaps
from peracolor.style import LITE_LAYERS, LITE_STYLE

matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "DejaVu Sans"

RAW_FIGSIZE_IN = 12
RAW_DPI = 500
# A rendered circle should be close to square once transparent margins are trimmed.
MIN_CIRCLE_ASPECT = 0.9


def configure_osmnx() -> None:
    ox.settings.log_console = False


def raw_png_path(raw_dir: Path, slug: str) -> Path:
    return raw_dir / f"{slug}.png"


def raw_meta_path(raw_dir: Path, slug: str) -> Path:
    return raw_dir / f"{slug}.json"


def draw_map(centre: LatLon, radius: int, output: Path, style: dict[str, dict]) -> None:
    """Draw the circle map in the given style and save it with a transparent background."""
    plot = prettymaps.plot(
        (centre.lat, centre.lon),
        layers=deepcopy(LITE_LAYERS),
        style=deepcopy(style),
        circle=True,
        radius=radius,
        dilate=0,
        credit=False,
        figsize=(RAW_FIGSIZE_IN, RAW_FIGSIZE_IN),
        show=False,
    )
    plot.fig.savefig(output, dpi=RAW_DPI, transparent=True)
    plt.close(plot.fig)


class MalformedRenderError(ValueError):
    """Raised when a render is not a full circle (e.g. a circle crossing the Prime Meridian)."""


def check_circle_shape(width: int, height: int, path: Path) -> None:
    ratio = width / height
    if not MIN_CIRCLE_ASPECT <= ratio <= 1 / MIN_CIRCLE_ASPECT:
        raise MalformedRenderError(f"Render {path.name} is {width}x{height}, not a circle; move the place's centre")


def crop_to_content(path: Path) -> None:
    """Trim transparent margins so the circle fills the cached image, and reject malformed renders."""
    with Image.open(path) as image:
        bounds = image.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError(f"Render {path} is fully transparent")
        cropped = image.crop(bounds)
    check_circle_shape(cropped.width, cropped.height, path)
    cropped.save(path)


def render_place(place: Place, cache_dir: Path, style: dict[str, dict], force: bool = False) -> Path:
    raw_dir = cache_dir / "raw"
    png_path = raw_png_path(raw_dir, place.slug)
    if png_path.exists() and raw_meta_path(raw_dir, place.slug).exists() and not force:
        logger.info("Using cached render for {}", place.slug)
        return png_path
    raw_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    region_pbf = ensure_region_pbf(place.osm_region, cache_dir / "pbf")
    extract = extract_area(region_pbf, bbox_around(place.centre, place.radius), cache_dir / "extracts", place.slug)
    logger.info("Rendering {} at {:.5f}, {:.5f} (r={} m)", place.slug, place.centre.lat, place.centre.lon, place.radius)
    with offline_prettymaps(extract):
        draw_map(place.centre, place.radius, png_path, style)
    crop_to_content(png_path)
    meta = RenderMeta(slug=place.slug, centre=place.centre, radius=place.radius)
    raw_meta_path(raw_dir, place.slug).write_text(meta.model_dump_json(indent=2))
    logger.info("Rendered {} in {:.0f}s", place.slug, time.monotonic() - started)
    return png_path


def render_place_with_style(place: Place, cache_dir: Path, style: dict[str, dict], output: Path) -> Path:
    """Render a place in an alternative style without touching the cached production render."""
    output.parent.mkdir(parents=True, exist_ok=True)
    region_pbf = ensure_region_pbf(place.osm_region, cache_dir / "pbf")
    extract = extract_area(region_pbf, bbox_around(place.centre, place.radius), cache_dir / "extracts", place.slug)
    with offline_prettymaps(extract):
        draw_map(place.centre, place.radius, output, style)
    crop_to_content(output)
    return output


def load_render_meta(raw_dir: Path, slug: str) -> RenderMeta:
    return RenderMeta.model_validate_json(raw_meta_path(raw_dir, slug).read_text())
