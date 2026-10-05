"""Pinterest pins for the listings that are not single places: the Custom Map and the sets.

Custom Map pins show the personalised examples from the listing photos, because
gift searches ("wedding venue map", "first home gift") are where custom maps sell.
Set pins show the three maps together, aimed at gallery-wall searches.
"""

from pathlib import Path

from PIL import Image

from peracolor.custom_listing import CUSTOM_LISTING_ID, EXAMPLES, colour_example_posters, example_poster
from peracolor.models import Place
from peracolor.pins import (
    DESCRIPTION_MAX,
    ETSY_LISTING_URL,
    HEADLINE_TRACKING,
    PIN_SIZE,
    POSTER_PREVIEW,
    TITLE_MAX,
    PinCopy,
    area_name,
    framed_pin,
    member_posters,
    paste_trio,
    pin_canvas,
)
from peracolor.sets import PosterSet, load_member
from peracolor.style import FONT_BODY
from peracolor.typography import load_font, tracked_width

CUSTOM_BOARD = "Custom Map Gifts"
CUSTOM_HEADING = "Custom Map"
CUSTOM_SUBHEADING = "Any location · your words"
CUSTOM_HASHTAGS = "#CustomMapPrint #PersonalizedGift #WeddingGift #FirstHomeGift #AnniversaryGift"
SETS_BOARD = "Gallery Wall Sets"
SET_HEADLINE_MAX_SIZE = 26
HEADLINE_MAX_WIDTH = PIN_SIZE[0] * 0.9


def custom_description(occasion: str) -> str:
    text = (
        f"Personalized circle map of any city, neighbourhood or address, {occasion}. "
        "Add your own title and line of text; you receive all 3 colour versions (Original, Minimalist Mono "
        "and Sage & Terracotta) as printable files within 48 hours. "
        f"{CUSTOM_HASHTAGS}"
    )
    return text[:DESCRIPTION_MAX]


def write_custom_pins(places: dict[str, Place], raw_dir: Path, pins_dir: Path) -> list[PinCopy]:
    folder = pins_dir / "custom-map"
    folder.mkdir(parents=True, exist_ok=True)
    link = ETSY_LISTING_URL.format(listing_id=CUSTOM_LISTING_ID)
    copies = []
    for example in EXAMPLES:
        path = folder / f"custom-map-pin-{example.caption.lower().replace(' ', '-')}.jpg"
        poster = example_poster(places, raw_dir, example, POSTER_PREVIEW)
        framed_pin(CUSTOM_HEADING, CUSTOM_SUBHEADING, f"{example.caption.upper()}  ·  3 COLOURS INCLUDED", poster).save(path, quality=88)
        copies.append(PinCopy(
            image=str(path), board=CUSTOM_BOARD, link=link,
            title=f"Custom Map Print, Any Location | Personalized \"{example.title}\" Gift"[:TITLE_MAX],
            description=custom_description(f"shown here as \"{example.title}\" for {example.subtitle}"),
            alt_text=f"Framed personalized circle map poster titled {example.title}, {example.subtitle}",
        ))
    path = folder / "custom-map-pin-all-colours.jpg"
    canvas, _ = pin_canvas(CUSTOM_HEADING, CUSTOM_SUBHEADING, "3 COLOUR VERSIONS INCLUDED")
    paste_trio(canvas, colour_example_posters(places, raw_dir, POSTER_PREVIEW))
    canvas.save(path, quality=88)
    copies.append(PinCopy(
        image=str(path), board=CUSTOM_BOARD, link=link,
        title="Custom Map Print, Any Location | 3 Colour Versions Included"[:TITLE_MAX],
        description=custom_description("ideal for a wedding venue, first home or where you met"),
        alt_text="Three personalized circle map posters in original, mono and sage and terracotta colours",
    ))
    return copies


def fitting_headline_size(text: str, max_size: int) -> int:
    """Largest font size at or below max_size at which the headline fits the pin width."""
    size = max_size
    while size > 1 and tracked_width(text, load_font(FONT_BODY, size), HEADLINE_TRACKING) > HEADLINE_MAX_WIDTH:
        size -= 1
    return size


def set_pin(poster_set: PosterSet, posters: list[Image.Image], areas: list[str]) -> Image.Image:
    headline = "  ·  ".join(area.upper() for area in areas)
    size = fitting_headline_size(headline, SET_HEADLINE_MAX_SIZE)
    canvas, _ = pin_canvas(poster_set.title, "Set of 3 circle maps", headline, headline_size=size)
    paste_trio(canvas, posters)
    return canvas


def write_set_pins(poster_sets: list[PosterSet], places: dict[str, Place], raw_dir: Path, pins_dir: Path) -> list[PinCopy]:
    folder = pins_dir / "sets"
    folder.mkdir(parents=True, exist_ok=True)
    copies = []
    for poster_set in poster_sets:
        members = [load_member(places[slug], raw_dir) for slug in poster_set.places]
        areas = [area_name(member.place) for member in members]
        path = folder / f"{poster_set.slug}-pin.jpg"
        set_pin(poster_set, member_posters(members), areas).save(path, quality=88)
        link = ETSY_LISTING_URL.format(listing_id=poster_set.listing_id) if poster_set.listing_id else ""
        description = (
            f"Set of 3 circle street map prints: {', '.join(areas)}. Matching printable wall art for a gallery wall, "
            "instant download in ISO A sizes (A1-A5) and US sizes up to 24x36. "
            f"#{poster_set.title.replace(' ', '')}WallArt #GalleryWallSet #SetOf3Prints #CityMapPrint #PrintableWallArt"
        )
        copies.append(PinCopy(
            image=str(path), board=SETS_BOARD, link=link,
            title=f"{poster_set.title} Map Print Set of 3 | Circle City Maps Gallery Wall"[:TITLE_MAX],
            description=description[:DESCRIPTION_MAX],
            alt_text=f"Three circle map posters: {', '.join(areas)}",
        ))
    return copies
