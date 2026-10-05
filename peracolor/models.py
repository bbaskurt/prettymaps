"""Typed configuration for the PeraColor poster pipeline.

A places file lists every map we sell. Each entry carries enough context to
render the map (query or explicit centre, radius) and to write accurate
listing copy (city, country, subtitle, extra tag hints).
"""

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class LatLon(BaseModel):
    model_config = ConfigDict(frozen=True)

    lat: Annotated[float, Field(ge=-90, le=90)]
    lon: Annotated[float, Field(ge=-180, le=180)]


OsmRegion = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9-]+(/[a-z0-9-]+)*$"),
    Field(description="Geofabrik region path, e.g. europe/united-kingdom/england/greater-london"),
]


class Place(BaseModel):
    """One sellable map.

    `centre` is required because rendering is offline (no geocoding). Keep it
    inland for waterfront cities: OSM does not map the sea as polygons, so open
    sea renders as a flat, clipped area.
    """

    model_config = ConfigDict(frozen=True)

    slug: Slug
    query: Annotated[str, Field(description="Human-readable description of the map centre")]
    title: Annotated[str, Field(description="Large text printed under the circle")]
    city: str
    country: str
    subtitle: Annotated[str | None, Field(description="Neighbourhood or landmark line")] = None
    radius: Annotated[int, Field(ge=300, le=4000, description="Circle radius in metres")] = 1100
    centre: LatLon
    osm_region: OsmRegion
    tag_hints: list[str] = []

    @property
    def area(self) -> str:
        """Neighbourhood/landmark name used in copy, or the city itself."""
        return self.subtitle or self.city


class PlacesFile(BaseModel):
    places: list[Place]


class RenderMeta(BaseModel):
    """Sidecar written next to each cached raw render."""

    slug: Slug
    centre: LatLon
    radius: int


def load_places(path: Path) -> list[Place]:
    places = PlacesFile.model_validate(yaml.safe_load(path.read_text())).places
    slugs = [place.slug for place in places]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    if duplicates:
        raise ValueError(f"Duplicate place slugs in {path}: {duplicates}")
    return places


def select_places(places: list[Place], only: list[str] | None) -> list[Place]:
    if not only:
        return places
    known = {place.slug for place in places}
    unknown = sorted(set(only) - known)
    if unknown:
        raise ValueError(f"Unknown place slugs: {unknown}")
    return [place for place in places if place.slug in only]
