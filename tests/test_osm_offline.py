from pathlib import Path

import pytest

from peracolor.models import LatLon
from peracolor.render import MalformedRenderError, check_circle_shape
from peracolor.osm_offline import (
    METRES_PER_DEGREE_LAT,
    bbox_around,
    region_pbf_path,
    region_url,
    street_filter,
)


class TestBboxAround:
    def test_box_is_centred_and_covers_the_circle(self) -> None:
        """Given a centre and radius, when the extract box is computed, then it is centred and larger than the circle."""
        centre = LatLon(lat=38.717, lon=-9.148)

        box = bbox_around(centre, radius_m=900, margin=1.0)

        assert (box.min_lat + box.max_lat) / 2 == pytest.approx(centre.lat)
        assert (box.min_lon + box.max_lon) / 2 == pytest.approx(centre.lon)
        assert (box.max_lat - box.min_lat) * METRES_PER_DEGREE_LAT == pytest.approx(1800)

    def test_longitude_span_widens_away_from_the_equator(self) -> None:
        """Given a northern city, when the box is computed, then it spans more degrees of longitude than latitude."""
        box = bbox_around(LatLon(lat=55.95, lon=-3.19), radius_m=1100)

        assert (box.max_lon - box.min_lon) > (box.max_lat - box.min_lat)

    def test_osmium_argument_order(self) -> None:
        """Given a box, when formatted for osmium, then it reads min_lon,min_lat,max_lon,max_lat."""
        box = bbox_around(LatLon(lat=0.0, lon=0.0), radius_m=1000, margin=1.0)

        min_lon, min_lat, max_lon, max_lat = (float(part) for part in box.osmium_arg().split(","))

        assert min_lon < 0 < max_lon and min_lat < 0 < max_lat


class TestRegions:
    def test_region_url_points_at_latest_geofabrik_pbf(self) -> None:
        """Given a region path, when the download URL is built, then it is Geofabrik's latest PBF."""
        assert region_url("europe/portugal") == "https://download.geofabrik.de/europe/portugal-latest.osm.pbf"

    def test_region_file_name_is_flat(self) -> None:
        """Given a nested region path, when the cache file is named, then slashes do not create directories."""
        path = region_pbf_path(Path("cache/pbf"), "europe/united-kingdom/england/greater-london")

        assert path == Path("cache/pbf/europe--united-kingdom--england--greater-london.osm.pbf")


def test_street_filter_lists_every_drawn_street_type() -> None:
    """Given the poster's street widths, when the osmium filter is built, then it keeps exactly those highway types."""
    assert street_filter() == "w/highway=motorway,primary,residential,secondary,tertiary,trunk"


class TestCircleShape:
    def test_square_render_passes(self) -> None:
        """Given a near-square render, when its shape is checked, then it is accepted."""
        check_circle_shape(4965, 4970, Path("ok.png"))

    def test_flat_strip_is_rejected(self) -> None:
        """Given a render collapsed into a strip (meridian-crossing bug), when checked, then it fails loudly."""
        with pytest.raises(MalformedRenderError):
            check_circle_shape(5465, 53, Path("greenwich.png"))
