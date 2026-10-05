"""Offline OpenStreetMap data for rendering.

Rendering used to query the public Overpass API, which is often overloaded and
blocks clients that make many requests. Instead we download a Geofabrik
regional extract once per region, cut a small XML extract around each place
with osmium, and point prettymaps' two data calls at those local files. After
the regional download, rendering needs no network at all.
"""

import math
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import requests
from loguru import logger
from pydantic import BaseModel, ConfigDict
from shapely.geometry.base import BaseGeometry

import prettymaps.fetch
from peracolor.models import LatLon
from peracolor.style import STREET_WIDTHS

GEOFABRIK_BASE = "https://download.geofabrik.de"
# Geofabrik asks automated clients to identify themselves.
USER_AGENT = "peracolor-prettymaps/0.1 (circle map poster renderer)"
DOWNLOAD_TIMEOUT_S = 60
DOWNLOAD_CHUNK_BYTES = 1 << 20
# Extract a little beyond the circle so ways crossing its edge are complete.
BBOX_MARGIN = 1.15
METRES_PER_DEGREE_LAT = 111_320
WGS84 = "EPSG:4326"


class BoundingBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def osmium_arg(self) -> str:
        return f"{self.min_lon:.6f},{self.min_lat:.6f},{self.max_lon:.6f},{self.max_lat:.6f}"


class AreaExtract(BaseModel):
    """Local OSM XML files covering one place."""

    model_config = ConfigDict(frozen=True)

    all_features: Path
    streets: Path


def bbox_around(centre: LatLon, radius_m: int, margin: float = BBOX_MARGIN) -> BoundingBox:
    half_side_m = radius_m * margin
    delta_lat = half_side_m / METRES_PER_DEGREE_LAT
    delta_lon = half_side_m / (METRES_PER_DEGREE_LAT * math.cos(math.radians(centre.lat)))
    return BoundingBox(
        min_lon=centre.lon - delta_lon,
        min_lat=centre.lat - delta_lat,
        max_lon=centre.lon + delta_lon,
        max_lat=centre.lat + delta_lat,
    )


def region_url(region: str) -> str:
    return f"{GEOFABRIK_BASE}/{region}-latest.osm.pbf"


def region_pbf_path(pbf_dir: Path, region: str) -> Path:
    return pbf_dir / f"{region.replace('/', '--')}.osm.pbf"


def download(url: str, destination: Path) -> None:
    """Stream to a temporary file so an interrupted download never looks complete."""
    partial = destination.with_suffix(destination.suffix + ".part")
    with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT_S, headers={"User-Agent": USER_AGENT}) as response:
        response.raise_for_status()
        with partial.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_BYTES):
                handle.write(chunk)
    partial.rename(destination)


def ensure_region_pbf(region: str, pbf_dir: Path) -> Path:
    path = region_pbf_path(pbf_dir, region)
    if path.exists():
        return path
    pbf_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading OSM region {} (one-off)", region)
    download(region_url(region), path)
    logger.info("Downloaded {} ({:.0f} MB)", path.name, path.stat().st_size / 1e6)
    return path


def run_osmium(args: list[str]) -> None:
    subprocess.run(["osmium", *args], check=True, capture_output=True, text=True)


def street_filter() -> str:
    """osmium tag filter for the street types the poster style draws."""
    return "w/highway=" + ",".join(sorted(STREET_WIDTHS))


def extract_area(region_pbf: Path, bbox: BoundingBox, out_dir: Path, slug: str) -> AreaExtract:
    """Cut the place's surroundings out of the regional extract as OSM XML."""
    out_dir.mkdir(parents=True, exist_ok=True)
    extract = AreaExtract(all_features=out_dir / f"{slug}.osm", streets=out_dir / f"{slug}-streets.osm")
    # "smart" completes multipolygon relations (parks, lakes) that cross the box edge.
    run_osmium(["extract", "--bbox", bbox.osmium_arg(), "--strategy", "smart", "--overwrite", "-o", str(extract.all_features), str(region_pbf)])
    run_osmium(["tags-filter", str(extract.all_features), street_filter(), "--overwrite", "-o", str(extract.streets)])
    return extract


class OfflineOsmnx:
    """Stands in for the osmnx module inside prettymaps.fetch, serving local extracts.

    Only the two data-fetching calls prettymaps makes are replaced; everything
    else (projection helpers etc.) is delegated to the real osmnx module.
    """

    def __init__(self, extract: AreaExtract) -> None:
        self._extract = extract

    def __getattr__(self, name: str) -> object:
        return getattr(ox, name)

    def graph_from_polygon(self, polygon: BaseGeometry, custom_filter: str | None = None, truncate_by_edge: bool = False) -> object:
        if custom_filter is not None:
            raise NotImplementedError("Offline rendering only supports the default street network (no custom_filter)")
        graph = ox.graph_from_xml(self._extract.streets, simplify=True, retain_all=True)
        return ox.truncate.truncate_graph_polygon(graph, polygon, retain_all=True, truncate_by_edge=truncate_by_edge)

    def geometries_from_polygon(self, polygon: BaseGeometry, tags: dict) -> gpd.GeoDataFrame:
        features = ox.geometries_from_xml(self._extract.all_features, polygon=polygon, tags=tags)
        if features.empty:
            # A layer with no matching features (e.g. no forest in central Lisbon) comes back
            # without a geometry column, which prettymaps cannot intersect with the circle.
            return gpd.GeoDataFrame(geometry=[], crs=WGS84)
        return features


@contextmanager
def offline_prettymaps(extract: AreaExtract) -> Iterator[None]:
    original = prettymaps.fetch.ox
    prettymaps.fetch.ox = OfflineOsmnx(extract)
    try:
        yield
    finally:
        prettymaps.fetch.ox = original
