"""Publish rendered single-place colourway packages as Etsy listings.

Each place becomes a free draft first (files and photos attached), then is made
active, which is when Etsy charges the listing fee. New listing IDs are added to
etsy_listings.yaml so pins and later updates can find them. Places that already
have a listing are refused rather than duplicated.
"""

from pathlib import Path

import yaml
from loguru import logger

from peracolor.colourway_listing import new_listing_copy
from peracolor.create_listing import DraftSpec, create_draft, publish
from peracolor.etsy_api import EtsyClient
from peracolor.models import Place

SINGLE_PRICE_GBP = 3.35
# Digital downloads never run out; matches the existing city listings.
DIGITAL_QUANTITY = 99
# Etsy category "Prints" used by every existing city listing.
PRINTS_TAXONOMY_ID = 2078
EUROPE_SECTION_ID = 60726250
# Countries with their own shop section; other European countries go to Europe.
COUNTRY_SECTION_IDS = {
    "France": 49638492,
    "Spain": 49648151,
    "USA": 60726248,
    "United Kingdom": 49638488,
}
EUROPEAN_COUNTRIES = {
    "Austria", "Belgium", "Czech Republic", "Denmark", "Germany", "Greece", "Hungary", "Ireland",
    "Italy", "Netherlands", "Poland", "Portugal", "Turkey",
}


class AlreadyListedError(ValueError):
    """Raised when a place already has a listing in etsy_listings.yaml."""


def section_for(place: Place) -> int | None:
    """Shop section by country; places outside the sectioned regions stay unsectioned."""
    if place.country in COUNTRY_SECTION_IDS:
        return COUNTRY_SECTION_IDS[place.country]
    if place.country in EUROPEAN_COUNTRIES:
        return EUROPE_SECTION_ID
    return None


def draft_spec(place: Place, package_dir: Path) -> DraftSpec:
    copy = new_listing_copy(place)
    return DraftSpec(
        title=copy.title,
        description=copy.description,
        price=SINGLE_PRICE_GBP,
        quantity=DIGITAL_QUANTITY,
        taxonomy_id=PRINTS_TAXONOMY_ID,
        tags=copy.tags,
        shop_section_id=section_for(place),
        files=sorted((package_dir / "files").glob("*.zip")),
        images=sorted((package_dir / "images").glob("*.jpg")),
    )


def record_listing(listings_path: Path, slug: str, listing_id: int) -> None:
    """Add the new listing to etsy_listings.yaml, keeping slugs sorted under the header comments."""
    text = listings_path.read_text()
    header = "".join(line for line in text.splitlines(keepends=True) if line.startswith("#"))
    listings = yaml.safe_load(text) | {slug: listing_id}
    body = "".join(f"{key}: {value}\n" for key, value in sorted(listings.items()))
    listings_path.write_text(header + body)


def publish_place(client: EtsyClient, shop_id: int, place: Place, output_dir: Path, listings_path: Path) -> int:
    if place.slug in yaml.safe_load(listings_path.read_text()):
        raise AlreadyListedError(f"{place.slug} already has an Etsy listing")
    spec = draft_spec(place, output_dir / "colourways" / place.slug)
    listing_id = create_draft(client, shop_id, spec)
    state = publish(client, shop_id, listing_id)
    record_listing(listings_path, place.slug, listing_id)
    logger.info("Published {} as listing {} ({})", place.slug, listing_id, state)
    return listing_id
