import pytest

from peracolor.poster import format_coordinates, plan_layout
from peracolor.models import LatLon
from peracolor.sizes import (
    DELIVERABLES,
    ETSY_MAX_FILES,
    PRINT_SPECS,
    PrintFormat,
    inches_to_pixels,
)


class TestPixelMaths:
    @pytest.mark.parametrize(
        ("print_format", "expected"),
        [
            (PrintFormat.ISO_A, (7016, 9933)),
            (PrintFormat.RATIO_2X3, (7200, 10800)),
            (PrintFormat.RATIO_3X4, (5400, 7200)),
            (PrintFormat.RATIO_4X5, (4800, 6000)),
            (PrintFormat.SIZE_11X14, (3300, 4200)),
            (PrintFormat.SIZE_5X7, (1500, 2100)),
        ],
    )
    def test_master_files_are_300_dpi_at_largest_size(self, print_format: PrintFormat, expected: tuple[int, int]) -> None:
        """Given a print format, when its pixels are computed, then they match the largest size at 300 DPI."""
        assert PRINT_SPECS[print_format].pixels == expected

    def test_inches_round_to_nearest_pixel(self) -> None:
        """Given fractional inches, when converted, then the result rounds to the nearest pixel."""
        assert inches_to_pixels(1 / 3) == 100


class TestDeliverables:
    def test_every_format_ships_once_within_etsy_file_limit(self) -> None:
        """Given the deliverable plan, when inspected, then each format ships exactly once in at most five files."""
        shipped = [print_format for deliverable in DELIVERABLES for print_format in deliverable.formats]
        assert sorted(shipped) == sorted(PRINT_SPECS)
        assert len(DELIVERABLES) <= ETSY_MAX_FILES


class TestLayout:
    @pytest.mark.parametrize("print_format", list(PrintFormat))
    def test_circle_fits_inside_poster_margins(self, print_format: PrintFormat) -> None:
        """Given any print format, when the layout is planned, then the circle sits within the poster with side margins."""
        width, height = PRINT_SPECS[print_format].pixels
        layout = plan_layout(width, height)
        assert layout.circle_diameter < width
        assert layout.circle_top > 0
        assert layout.circle_top + layout.circle_diameter < height * 0.8

    def test_coordinates_use_hemisphere_letters(self) -> None:
        """Given a south-western point, when formatted, then latitude is S and longitude is W without minus signs."""
        assert format_coordinates(LatLon(lat=-33.8688, lon=-151.2093)) == "33.8688° S   151.2093° W"
