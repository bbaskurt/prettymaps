"""Photos, order-info file and copy for the "Custom Map - Any Location" listing.

Custom orders are fulfilled by adding the buyer's place to places.yaml and running
the colourways pipeline, so the listing shows real renders with personalised text
rather than generic mock-ups.
"""

from pathlib import Path

from PIL import Image, ImageDraw
from pydantic import BaseModel

from peracolor.colourways import labelled_triptych
from peracolor.mockup import CANVAS_SIZE, sizes_guide
from peracolor.models import Place
from peracolor.palettes import PaletteName, palette_variant
from peracolor.poster import compose_poster
from peracolor.sets import PREVIEW_SIZE, SET_FORMATS, load_member, triptych_with_centres
from peracolor.sizes import PRINT_SPECS
from peracolor.style import FONT_BODY, FONT_SMALL, FONT_TITLE, INK, MUTED_INK, POSTER_BACKGROUND
from peracolor.typography import draw_tracked_centred, load_font

CUSTOM_LISTING_ID = 4589227423
A4_PIXELS = (2480, 3508)
DELIVERY_HOURS = 48


class CustomExample(BaseModel):
    """An existing render shown with buyer-style personalised text."""

    slug: str
    palette: PaletteName
    title: str
    subtitle: str
    caption: str


EXAMPLES = (
    CustomExample(slug="edinburgh-old-town", palette=PaletteName.ORIGINAL, title="Where We Met", subtitle="Edinburgh", caption="Where we met"),
    CustomExample(slug="paris-montmartre", palette=PaletteName.SAGE_TERRACOTTA, title="Our Wedding", subtitle="Montmartre, Paris", caption="Our wedding"),
    CustomExample(slug="brooklyn-park-slope", palette=PaletteName.MONO, title="Our First Home", subtitle="Park Slope, Brooklyn", caption="Our first home"),
)

STEPS = (
    ("1", "Add the address or place", "and the words you want printed"),
    ("2", "We draw your map", f"in all 3 colour versions within {DELIVERY_HOURS} hours"),
    ("3", "Download and print", "A1-A5 and US sizes up to 24x36\""),
)


def personalised_place(base: Place, example: CustomExample) -> Place:
    return palette_variant(base, example.palette).model_copy(update={"title": example.title, "subtitle": example.subtitle})


def example_poster(places: dict[str, Place], raw_dir: Path, example: CustomExample, size: tuple[int, int] = PREVIEW_SIZE) -> Image.Image:
    member = load_member(personalised_place(places[example.slug], example), raw_dir)
    return compose_poster(member.raw_map, member.place, member.centre, size)


def colour_example_posters(places: dict[str, Place], raw_dir: Path, size: tuple[int, int] = PREVIEW_SIZE) -> list[Image.Image]:
    """The "Our First Home" example in Original, Mono and Sage & Terracotta."""
    example = EXAMPLES[2]
    palettes = (PaletteName.ORIGINAL, PaletteName.MONO, PaletteName.SAGE_TERRACOTTA)
    return [example_poster(places, raw_dir, example.model_copy(update={"palette": palette}), size) for palette in palettes]


def examples_image(places: dict[str, Place], raw_dir: Path) -> Image.Image:
    posters = [example_poster(places, raw_dir, example) for example in EXAMPLES]
    canvas, centres = triptych_with_centres(posters)
    draw = ImageDraw.Draw(canvas)
    width, height = CANVAS_SIZE
    draw_tracked_centred(draw, "YOUR PLACE, YOUR WORDS", load_font(FONT_TITLE, 96), width / 2, round(height * 0.16), 22, INK)
    for example, centre_x in zip(EXAMPLES, centres, strict=True):
        draw_tracked_centred(draw, example.caption.upper(), load_font(FONT_BODY, 56), centre_x, round(height * 0.93), 6, INK)
    return canvas


def how_it_works_image() -> Image.Image:
    canvas = Image.new("RGB", CANVAS_SIZE, POSTER_BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    width = CANVAS_SIZE[0]
    draw_tracked_centred(draw, "HOW IT WORKS", load_font(FONT_TITLE, 120), width / 2, 360, 30, INK)
    for index, (number, heading, detail) in enumerate(STEPS):
        top = 760 + index * 480
        draw_tracked_centred(draw, number, load_font(FONT_TITLE, 140), width / 2, top, 0, MUTED_INK)
        draw_tracked_centred(draw, heading.upper(), load_font(FONT_BODY, 72), width / 2, top + 150, 10, INK)
        draw_tracked_centred(draw, detail, load_font(FONT_SMALL, 56), width / 2, top + 250, 4, MUTED_INK)
    return canvas


def colours_image(places: dict[str, Place], raw_dir: Path) -> Image.Image:
    return labelled_triptych(colour_example_posters(places, raw_dir))


def order_info_pdf(path: Path) -> Path:
    """Instant-download file explaining that the personalised map follows within 48 hours."""
    page = Image.new("RGB", A4_PIXELS, "white")
    draw = ImageDraw.Draw(page)
    width = A4_PIXELS[0]
    lines = [
        (FONT_TITLE, 110, "THANK YOU!", 500),
        (FONT_BODY, 64, "Your custom PeraColor map is being made.", 760),
        (FONT_SMALL, 52, f"We will send all 3 colour versions to you through Etsy", 1000),
        (FONT_SMALL, 52, f"messages within {DELIVERY_HOURS} hours, ready to download and print.", 1080),
        (FONT_SMALL, 52, "Any questions or changes? Just message us on Etsy.", 1300),
    ]
    for font, size, text, y in lines:
        draw_tracked_centred(draw, text, load_font(font, size), width / 2, y, 4, INK)
    page.save(path, "PDF", resolution=300)
    return path


def write_custom_listing_assets(places: dict[str, Place], raw_dir: Path, output_dir: Path) -> Path:
    folder = output_dir / "custom-map"
    (folder / "images").mkdir(parents=True, exist_ok=True)
    (folder / "files").mkdir(parents=True, exist_ok=True)
    examples_image(places, raw_dir).save(folder / "images" / "01-examples.jpg", quality=90)
    how_it_works_image().save(folder / "images" / "02-how-it-works.jpg", quality=90)
    colours_image(places, raw_dir).save(folder / "images" / "03-colours.jpg", quality=90)
    footer = f"DIGITAL FILES WITHIN {DELIVERY_HOURS} HOURS  ·  300 DPI  ·  NO PHYSICAL ITEM SHIPPED"
    sizes_guide([PRINT_SPECS[f] for f in SET_FORMATS], footer).save(folder / "images" / "04-sizes.jpg", quality=90)
    order_info_pdf(folder / "files" / "peracolor-custom-map-order-info.pdf")
    return folder
