"""Replace an existing listing's digital files, photos and "WHAT YOU GET" text via the Etsy API.

Etsy allows at most five digital files per listing and a digital listing must
always keep at least one, so new files are uploaded first and old ones removed
only as space is needed. New photos are uploaded at the front (ranks 1..n)
before the old photos are deleted, so the listing is never left without images.
Videos are not touched.
"""

import re
import sys
from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from peracolor.etsy_api import EtsyClient
from peracolor.sizes import ETSY_MAX_FILES

WHAT_YOU_GET = re.compile(r"WHAT YOU GET\n[\s\S]*?\n\nPERFECT FOR")

SET_WHAT_YOU_GET = """WHAT YOU GET
• Instant download: 5 high-resolution 300 DPI files (zips of JPGs), ready to print
• One zip per map with ISO A sizes (A1, A2, A3, A4, A5) and the 2:3 ratio (4x6", 8x12", 12x18", 16x24", 20x30", 24x36")
• One zip with all three maps at 3:4 (6x8", 9x12", 12x16", 18x24")
• One zip with all three maps at 4:5 (8x10", 16x20")
• Need 11x14" or 5x7"? Message us after purchase and we will send them free of charge"""


class ReplacementPlan(BaseModel):
    listing_id: int
    files: list[Path]
    images: list[Path]
    what_you_get: str


class ReplacementResult(BaseModel):
    listing_id: int
    files: list[str]
    image_count: int
    description_updated: bool


def replace_files(client: EtsyClient, shop_id: int, plan: ReplacementPlan) -> None:
    if len(plan.files) > ETSY_MAX_FILES:
        raise ValueError(f"Listing {plan.listing_id}: {len(plan.files)} files exceeds Etsy's limit of {ETSY_MAX_FILES}")
    old_ids = [existing.listing_file_id for existing in client.listing_files(shop_id, plan.listing_id)]
    total = len(old_ids)
    for path in plan.files:
        while total >= ETSY_MAX_FILES:
            client.delete_listing_file(shop_id, plan.listing_id, old_ids.pop(0))
            total -= 1
        client.upload_listing_file(shop_id, plan.listing_id, path)
        total += 1
        logger.info("Listing {}: uploaded {}", plan.listing_id, path.name)
    for file_id in old_ids:
        client.delete_listing_file(shop_id, plan.listing_id, file_id)


def replace_images(client: EtsyClient, shop_id: int, plan: ReplacementPlan) -> None:
    old_ids = [image.listing_image_id for image in client.listing_images(plan.listing_id)]
    for rank, path in enumerate(plan.images, start=1):
        client.upload_listing_image(shop_id, plan.listing_id, path, rank)
    for image_id in old_ids:
        client.delete_listing_image(shop_id, plan.listing_id, image_id)
    logger.info("Listing {}: replaced {} photos with {}", plan.listing_id, len(old_ids), len(plan.images))


def update_what_you_get(client: EtsyClient, shop_id: int, plan: ReplacementPlan) -> bool:
    description = client.request("GET", f"/listings/{plan.listing_id}")["description"]
    updated = WHAT_YOU_GET.sub(plan.what_you_get + "\n\nPERFECT FOR", description, count=1)
    if updated == description:
        return False
    client.update_listing(shop_id, plan.listing_id, {"description": updated})
    return True


def replace_listing(client: EtsyClient, shop_id: int, plan: ReplacementPlan) -> ReplacementResult:
    replace_files(client, shop_id, plan)
    replace_images(client, shop_id, plan)
    description_updated = update_what_you_get(client, shop_id, plan)
    return ReplacementResult(
        listing_id=plan.listing_id,
        files=[existing.filename for existing in client.listing_files(shop_id, plan.listing_id)],
        image_count=len(client.listing_images(plan.listing_id)),
        description_updated=description_updated,
    )


def set_plan(listing_id: int, set_dir: Path) -> ReplacementPlan:
    return ReplacementPlan(
        listing_id=listing_id,
        files=sorted((set_dir / "files").glob("*.zip")),
        images=sorted((set_dir / "images").glob("*.jpg")),
        what_you_get=SET_WHAT_YOU_GET,
    )


if __name__ == "__main__":
    listing, folder = int(sys.argv[1]), Path(sys.argv[2])
    etsy = EtsyClient()
    print(replace_listing(etsy, etsy.shop_id(), set_plan(listing, folder)).model_dump_json(indent=2))
