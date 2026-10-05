"""Create new digital listings via the Etsy API, starting as free drafts.

Drafts cost nothing; Etsy charges the listing fee only when a listing is made
active, so `publish` is a separate, explicit step.
"""

from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from peracolor.etsy_api import EtsyClient

# Etsy's "when was it made" bucket covering the current period.
WHEN_MADE = "2020_2026"
WHO_MADE = "i_did"


class DraftSpec(BaseModel):
    title: str
    description: str
    price: float
    quantity: int
    taxonomy_id: int
    tags: list[str]
    shop_section_id: int | None
    files: list[Path]
    images: list[Path]


def draft_fields(spec: DraftSpec) -> dict[str, str]:
    fields = {
        "title": spec.title,
        "description": spec.description,
        "price": f"{spec.price:.2f}",
        "quantity": str(spec.quantity),
        "taxonomy_id": str(spec.taxonomy_id),
        "who_made": WHO_MADE,
        "when_made": WHEN_MADE,
        "is_supply": "false",
        "type": "download",
        "should_auto_renew": "true",
        "tags": ",".join(spec.tags),
    }
    if spec.shop_section_id is not None:
        fields["shop_section_id"] = str(spec.shop_section_id)
    return fields


def create_draft(client: EtsyClient, shop_id: int, spec: DraftSpec) -> int:
    """Create the draft, then attach its files and photos (photos in the given order)."""
    listing_id = int(client.request("POST", f"/shops/{shop_id}/listings", data=draft_fields(spec))["listing_id"])
    logger.info("Created draft listing {} ({})", listing_id, spec.title[:50])
    for path in spec.files:
        client.upload_listing_file(shop_id, listing_id, path)
    for rank, path in enumerate(spec.images, start=1):
        client.upload_listing_image(shop_id, listing_id, path, rank)
    return listing_id


def publish(client: EtsyClient, shop_id: int, listing_id: int) -> str:
    """Make a draft active. Etsy charges the listing fee at this point."""
    return client.update_listing(shop_id, listing_id, {"state": "active"})["state"]
