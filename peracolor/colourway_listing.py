"""Listing copy and replacement plan for three-colourway single-place listings.

Buyers must understand before purchase that they receive all three colour
versions, so it is stated in the title, in the first line of the description
and in the WHAT YOU GET block.
"""

import html
import re
from pathlib import Path

from pydantic import BaseModel

from peracolor.etsy_api import EtsyClient
from peracolor.models import Place
from peracolor.replace_listing import WHAT_YOU_GET, ReplacementPlan, ReplacementResult, replace_files, replace_images

TITLE_COLOUR_WORD = "Colorful"
TITLE_COLOURWAYS = "3 Colour Versions"
INTRO_PATTERN = re.compile(r"^A colourful circle map of ")
INTRO_REPLACEMENT = "A circle map of "
ALL_VERSIONS_LINE = (
    "YOU RECEIVE ALL 3 COLOUR VERSIONS: Original (bold red, orange and yellow), "
    "Minimalist Mono (warm greys) and Sage & Terracotta (earthy greens and clay). See the photos for each one."
)

COLOURWAY_WHAT_YOU_GET = """WHAT YOU GET
• All 3 colour versions in one purchase: Original, Mono and Sage & Terracotta
• Instant download: 5 high-resolution 300 DPI files (zips of JPGs), ready to print
• One zip per colour with ISO A sizes (A1, A2, A3, A4, A5) and the 2:3 ratio (4x6", 8x12", 12x18", 16x24", 20x30", 24x36")
• One zip with all 3 colours at 3:4 (6x8", 9x12", 12x16", 18x24")
• One zip with all 3 colours at 4:5 (8x10", 16x20")
• Need 11x14" or 5x7"? Message us after purchase and we will send them free of charge"""


class CopyRewriteError(ValueError):
    """Raised when existing listing copy does not have the shape the rewrite expects."""


def colourway_title(title: str) -> str:
    """Drop the 'Colorful' adjective and add '3 Colour Versions' as its own phrase before the gift/format tail."""
    if TITLE_COLOURWAYS in title:
        return title
    if TITLE_COLOUR_WORD not in title:
        raise CopyRewriteError(f"Title has no '{TITLE_COLOUR_WORD}' to replace: {title!r}")
    title = title.replace(f"{TITLE_COLOUR_WORD} ", "", 1)
    for anchor in (", Travel Gift", " (Digital Download)"):
        if anchor in title:
            return title.replace(anchor, f", {TITLE_COLOURWAYS}{anchor}", 1)
    raise CopyRewriteError(f"Title has no place to add '{TITLE_COLOURWAYS}': {title!r}")


def colourway_description(description: str) -> str:
    """Lead with the all-versions line, neutral intro wording and the colourway WHAT YOU GET block."""
    if description.startswith(ALL_VERSIONS_LINE):
        body = description[len(ALL_VERSIONS_LINE):].lstrip("\n")
    else:
        body = INTRO_PATTERN.sub(INTRO_REPLACEMENT, description, count=1)
    if not WHAT_YOU_GET.search(body):
        raise CopyRewriteError("Description has no WHAT YOU GET ... PERFECT FOR block")
    body = WHAT_YOU_GET.sub(COLOURWAY_WHAT_YOU_GET + "\n\nPERFECT FOR", body, count=1)
    return f"{ALL_VERSIONS_LINE}\n\n{body}"


def colourway_plan(listing_id: int, place_dir: Path) -> ReplacementPlan:
    return ReplacementPlan(
        listing_id=listing_id,
        files=sorted((place_dir / "files").glob("*.zip")),
        images=sorted((place_dir / "images").glob("*.jpg")),
        what_you_get=COLOURWAY_WHAT_YOU_GET,
    )


def apply_colourways(client: EtsyClient, shop_id: int, plan: ReplacementPlan) -> ReplacementResult:
    """Swap in the three-colourway files and photos, then rewrite title and description."""
    listing = client.request("GET", f"/listings/{plan.listing_id}")
    # The API returns HTML-escaped text; unescape so entities are not sent back literally.
    title = colourway_title(html.unescape(listing["title"]))
    description = colourway_description(html.unescape(listing["description"]))
    replace_files(client, shop_id, plan)
    replace_images(client, shop_id, plan)
    client.update_listing(shop_id, plan.listing_id, {"title": title, "description": description})
    return ReplacementResult(
        listing_id=plan.listing_id,
        files=[existing.filename for existing in client.listing_files(shop_id, plan.listing_id)],
        image_count=len(client.listing_images(plan.listing_id)),
        description_updated=True,
    )


GENERIC_TAGS = (
    "city map print",
    "map wall art",
    "printable wall art",
    "travel gift",
    "housewarming gift",
    "map poster",
    "circle map",
    "travel poster",
)
MINIMALIST_TAG = "minimalist map"
TAG_LIMIT = 13
TAG_MAX_CHARS = 20
TITLE_MAX_CHARS = 140

NEW_LISTING_FOOTER = """PERFECT FOR
• Housewarming, birthday, anniversary and travel gifts
• Living rooms, bedrooms, offices and gallery walls

HOW TO PRINT
Print at home, at a local print shop or with an online printing service. Colours may vary slightly between screens and printers.

PLEASE NOTE
• This is a digital download only. No physical item will be shipped.
• The frame and props shown in the photos are not included.

Want a map of somewhere else? We can make a custom circle map of any city, neighbourhood or address, ideal for a wedding venue, first home or hometown. Just send us a message."""


class NewListingCopy(BaseModel):
    title: str
    description: str
    tags: list[str]


def new_listing_title(place: Place) -> str:
    """Same pattern as the live listings: city keyword first, area, wall art, colourways, gift, format."""
    area = f"{place.subtitle} Circle City Map" if place.subtitle else "Circle City Map Art"
    title = f"{place.city} Map Print, {area}, {place.city} Wall Art, {TITLE_COLOURWAYS}, Travel Gift (Digital Download)"
    if len(title) > TITLE_MAX_CHARS:
        raise CopyRewriteError(f"Title for {place.slug} is {len(title)} characters: {title!r}")
    return title


def new_listing_tags(place: Place) -> list[str]:
    city = place.city.lower()
    # "minimalist map" is a high-volume search that fits the Mono version; it replaces
    # "<city> poster", which mostly duplicates the generic "map poster" tag.
    candidates = [f"{city} map", f"{city} print", f"{city} wall art", MINIMALIST_TAG, f"{city} gift"]
    if place.subtitle:
        candidates.append(place.subtitle.lower())
    candidates += [hint.lower() for hint in place.tag_hints] + list(GENERIC_TAGS)
    tags = [tag for tag in dict.fromkeys(candidates) if len(tag) <= TAG_MAX_CHARS]
    return tags[:TAG_LIMIT]


def new_listing_description(place: Place) -> str:
    where = f"{place.subtitle}, {place.city}" if place.subtitle else f"central {place.city}"
    intro = (
        f"A circle map of {where}, drawn from real street and building data. Bright, modern city wall art "
        f"for anyone who lives in, loves or has travelled to {place.city}."
    )
    return f"{ALL_VERSIONS_LINE}\n\n{intro}\n\n{COLOURWAY_WHAT_YOU_GET}\n\n{NEW_LISTING_FOOTER}"


def new_listing_copy(place: Place) -> NewListingCopy:
    return NewListingCopy(title=new_listing_title(place), description=new_listing_description(place), tags=new_listing_tags(place))
