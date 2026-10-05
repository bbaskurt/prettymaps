"""Etsy listing copy (title, tags, description) built only from place data.

Copy is generated per place, never copy-pasted between listings, so a New York
listing can't mention the Eiffel Tower. Etsy limits: titles up to 140
characters, exactly 13 tags of up to 20 characters each.
"""

import unicodedata

from pydantic import BaseModel

from peracolor.models import Place
from peracolor.sizes import PRINT_SPECS

TITLE_MAX_CHARS = 140
TAG_COUNT = 13
TAG_MAX_CHARS = 20

# Ordered by priority, not alphabetically: place-specific tags come first and
# this list tops the set up to 13. Search keywords use US spelling ("colorful")
# because that is what most Etsy buyers type.
GENERIC_TAGS = [
    "circle map",
    "city map print",
    "digital download",
    "housewarming gift",
    "map poster",
    "map wall art",
    "printable map",
    "printable wall art",
    "street map art",
    "travel gift",
    "travel poster",
    "colorful map print",
    "gallery wall print",
]


class ListingCopy(BaseModel):
    slug: str
    title: str
    tags: list[str]
    description: str


def ascii_fold(text: str) -> str:
    """Strip accents: Etsy tags reject many non-ASCII characters."""
    normalised = unicodedata.normalize("NFKD", text)
    return normalised.encode("ascii", "ignore").decode("ascii")


def build_title(place: Place) -> str:
    """Keyword-first title; trailing segments are dropped until it fits."""
    segments = [f"{place.city} Map Print"]
    if place.subtitle:
        segments.append(f"{place.subtitle} Circle City Map")
    else:
        segments.append(f"{place.city} Circle City Map")
    segments += [
        f"{place.country} Wall Art",
        "Printable Travel Poster",
        "Colorful Map Gift",
        "Digital Download",
    ]
    while len(", ".join(segments)) > TITLE_MAX_CHARS:
        segments.pop(-2 if len(segments) > 2 else -1)
    return ", ".join(segments)


def place_tags(place: Place) -> list[str]:
    city = place.city.lower()
    candidates = [*place.tag_hints, f"{city} map", f"{city} print", f"{city} poster", f"{city} wall art"]
    if place.subtitle:
        candidates.append(f"{place.subtitle.lower()} map")
    candidates.append(f"{place.country.lower()} gift")
    return candidates


def build_tags(place: Place) -> list[str]:
    tags: list[str] = []
    for candidate in [*place_tags(place), *GENERIC_TAGS]:
        tag = ascii_fold(candidate).lower().strip()
        if tag and len(tag) <= TAG_MAX_CHARS and tag not in tags:
            tags.append(tag)
    if len(tags) < TAG_COUNT:
        raise ValueError(f"Only {len(tags)} valid tags for {place.slug}; add tag_hints")
    return tags[:TAG_COUNT]


def sizes_section() -> str:
    lines = [f"● {spec.label} ratio: {', '.join(spec.printable_sizes)}" for spec in PRINT_SPECS.values()]
    return "\n".join(lines)


def build_description(place: Place) -> str:
    area = f"{place.subtitle}, {place.city}" if place.subtitle else place.city
    return f"""A colourful circle street map of {area}, {place.country}, drawn from real street and building data. Every street, park, river and building block of the area is shown in our warm PeraColor palette, with the place name and coordinates printed beneath.

🎁 A thoughtful gift for anyone who lives in, grew up in, or fell in love with {place.city}: housewarmings, birthdays, anniversaries and leaving presents.
🏠 Looks great in living rooms, hallways, offices and gallery walls.

📂 INSTANT DOWNLOAD: high-resolution 300 DPI JPG files, ready to print at home, at a local print shop or with an online printing service.

SIZES INCLUDED
{sizes_section()}

🗺️ Would you like a different place, such as your home, your wedding venue or where you first met? Search our shop for "Custom Circle Map" and we'll make it for you.

PLEASE NOTE
● This is a digital file only. No physical item will be shipped, and frames are not included.
● Colours may vary slightly between screens and printers.
● For personal use only. Please don't resell the files."""


def build_listing(place: Place) -> ListingCopy:
    return ListingCopy(
        slug=place.slug,
        title=build_title(place),
        tags=build_tags(place),
        description=build_description(place),
    )
