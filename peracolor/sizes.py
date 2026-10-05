"""Print formats delivered with every digital listing.

Each master file is rendered at the largest size of its aspect ratio, so the
buyer can print any smaller size of the same ratio without quality loss.
Etsy allows at most five digital files per listing (20 MB each), hence the
grouping into `DELIVERABLES`.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

PRINT_DPI = 300
MM_PER_INCH = 25.4
ETSY_MAX_FILES = 5
ETSY_MAX_FILE_BYTES = 20 * 1024 * 1024


class PrintFormat(StrEnum):
    ISO_A = "iso-a"
    RATIO_2X3 = "ratio-2x3"
    RATIO_3X4 = "ratio-3x4"
    RATIO_4X5 = "ratio-4x5"
    SIZE_11X14 = "size-11x14"
    SIZE_5X7 = "size-5x7"


class PrintSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    format: PrintFormat
    label: str
    width_in: float
    height_in: float
    printable_sizes: list[str]

    @property
    def pixels(self) -> tuple[int, int]:
        return inches_to_pixels(self.width_in), inches_to_pixels(self.height_in)

    @property
    def file_stem(self) -> str:
        return self.format.value


def inches_to_pixels(inches: float, dpi: int = PRINT_DPI) -> int:
    return round(inches * dpi)


def mm_to_inches(mm: float) -> float:
    return mm / MM_PER_INCH


PRINT_SPECS: dict[PrintFormat, PrintSpec] = {
    PrintFormat.ISO_A: PrintSpec(
        format=PrintFormat.ISO_A,
        label="ISO A",
        width_in=mm_to_inches(594),
        height_in=mm_to_inches(841),
        printable_sizes=["A1", "A2", "A3", "A4", "A5"],
    ),
    PrintFormat.RATIO_2X3: PrintSpec(
        format=PrintFormat.RATIO_2X3,
        label="2:3",
        width_in=24,
        height_in=36,
        printable_sizes=['4x6"', '8x12"', '12x18"', '16x24"', '20x30"', '24x36"'],
    ),
    PrintFormat.RATIO_3X4: PrintSpec(
        format=PrintFormat.RATIO_3X4,
        label="3:4",
        width_in=18,
        height_in=24,
        printable_sizes=['6x8"', '9x12"', '12x16"', '18x24"'],
    ),
    PrintFormat.RATIO_4X5: PrintSpec(
        format=PrintFormat.RATIO_4X5,
        label="4:5",
        width_in=16,
        height_in=20,
        printable_sizes=['8x10"', '16x20"'],
    ),
    PrintFormat.SIZE_11X14: PrintSpec(
        format=PrintFormat.SIZE_11X14,
        label="11x14",
        width_in=11,
        height_in=14,
        printable_sizes=['11x14"'],
    ),
    PrintFormat.SIZE_5X7: PrintSpec(
        format=PrintFormat.SIZE_5X7,
        label="5x7",
        width_in=5,
        height_in=7,
        printable_sizes=['5x7"'],
    ),
}


class Deliverable(BaseModel):
    """One file uploaded to Etsy: a single JPG, or a zip of several JPGs."""

    model_config = ConfigDict(frozen=True)

    name: str
    formats: list[PrintFormat]

    @property
    def is_zip(self) -> bool:
        return len(self.formats) > 1


DELIVERABLES: list[Deliverable] = [
    Deliverable(name="iso-a", formats=[PrintFormat.ISO_A]),
    Deliverable(name="ratio-2x3", formats=[PrintFormat.RATIO_2X3]),
    Deliverable(name="ratio-3x4", formats=[PrintFormat.RATIO_3X4]),
    Deliverable(name="ratio-4x5", formats=[PrintFormat.RATIO_4X5]),
    Deliverable(name="sizes-11x14-5x7", formats=[PrintFormat.SIZE_11X14, PrintFormat.SIZE_5X7]),
]


def all_printable_sizes() -> list[str]:
    return [size for spec in PRINT_SPECS.values() for size in spec.printable_sizes]
