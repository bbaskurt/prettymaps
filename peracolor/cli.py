"""Command-line entry point: `uv run python -m peracolor <command>`."""

import argparse
from enum import StrEnum
from pathlib import Path
from typing import assert_never

import yaml
from loguru import logger

from peracolor.colourways import compose_colourways
from peracolor.export import compose_place, write_listing
from peracolor.models import Place, load_places, select_places
from peracolor.palette_preview import preview_palettes
from peracolor.pins import write_pins, write_pins_csv
from peracolor.pins_extra import write_custom_pins, write_set_pins
from peracolor.etsy_api import EtsyClient
from peracolor.publish_places import publish_place
from peracolor.palettes import PALETTES, PaletteName, palette_variant, style_for
from peracolor.render import configure_osmnx, render_place
from peracolor.sets import compose_set, load_sets

REPO_ROOT = Path(__file__).resolve().parent.parent


class Command(StrEnum):
    ALL = "all"
    COLOURWAYS = "colourways"
    COMPOSE = "compose"
    EXTRA_PINS = "extra-pins"
    LISTING = "listing"
    PALETTES = "palettes"
    PINS = "pins"
    PUBLISH = "publish"
    RENDER = "render"
    SETS = "sets"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="peracolor", description="PeraColor map poster pipeline")
    parser.add_argument("command", type=Command, choices=list(Command))
    parser.add_argument("--places", type=Path, default=REPO_ROOT / "places.yaml")
    parser.add_argument("--sets", type=Path, default=REPO_ROOT / "sets.yaml")
    parser.add_argument("--listings", type=Path, default=REPO_ROOT / "etsy_listings.yaml")
    parser.add_argument("--only", nargs="+", metavar="SLUG", help="Process only these place slugs")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "output")
    parser.add_argument("--cache", type=Path, default=REPO_ROOT / "cache")
    parser.add_argument("--force", action="store_true", help="Re-render even if a cached map exists")
    parser.add_argument("--palette", type=PaletteName, choices=list(PaletteName), default=PaletteName.ORIGINAL, help="Colour palette for render/compose/listing/all")
    return parser.parse_args(argv)


def run_place(command: Command, place: Place, args: argparse.Namespace) -> None:
    raw_dir = args.cache / "raw"
    style = style_for(PALETTES[args.palette])
    place = palette_variant(place, args.palette)
    match command:
        case Command.RENDER:
            render_place(place, args.cache, style, force=args.force)
        case Command.COMPOSE:
            compose_place(place, raw_dir, args.output)
        case Command.LISTING:
            write_listing(place, args.output)
        case Command.COLOURWAYS:
            compose_colourways(place, raw_dir, args.output)
        case Command.PALETTES:
            preview_palettes(place, args.cache, args.output)
        case Command.EXTRA_PINS | Command.PINS | Command.PUBLISH | Command.SETS:
            raise ValueError(f"The {command} command runs once for all places, not per place")
        case Command.ALL:
            render_place(place, args.cache, style, force=args.force)
            compose_place(place, raw_dir, args.output)
            write_listing(place, args.output)
        case _:
            assert_never(command)


def run_sets(args: argparse.Namespace) -> None:
    places = {place.slug: place for place in load_places(args.places)}
    for poster_set in load_sets(args.sets):
        if args.only and poster_set.slug not in args.only:
            continue
        compose_set(poster_set, places, args.cache / "raw", args.output)
        logger.info("Finished set {}", poster_set.slug)


def run_pins(args: argparse.Namespace) -> None:
    """Pins for every listed place (or --only), plus one combined CSV of pin text."""
    listing_ids: dict[str, int] = yaml.safe_load(args.listings.read_text())
    places = select_places(load_places(args.places), args.only or sorted(listing_ids))
    copies = [copy for place in places for copy in write_pins(place, args.cache / "raw", args.output, listing_ids.get(place.slug))]
    write_pins_csv(copies, args.output / "pins" / "pins.csv")
    logger.info("Wrote {} pins for {} places", len(copies), len(places))


def run_extra_pins(args: argparse.Namespace) -> None:
    """Pins for the Custom Map and set listings, with their own CSV of pin text."""
    places = {place.slug: place for place in load_places(args.places)}
    pins_dir = args.output / "pins"
    raw_dir = args.cache / "raw"
    copies = write_custom_pins(places, raw_dir, pins_dir) + write_set_pins(load_sets(args.sets), places, raw_dir, pins_dir)
    write_pins_csv(copies, pins_dir / "extra-pins.csv")
    logger.info("Wrote {} custom map and set pins", len(copies))


def run_publish(args: argparse.Namespace) -> None:
    """Publish the --only places as Etsy listings; each costs Etsy's listing fee."""
    if not args.only:
        raise ValueError("publish needs --only with the place slugs to publish")
    client = EtsyClient()
    shop_id = client.shop_id()
    for place in select_places(load_places(args.places), args.only):
        publish_place(client, shop_id, place, args.output, args.listings)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == Command.PUBLISH:
        run_publish(args)
        return
    if args.command == Command.EXTRA_PINS:
        run_extra_pins(args)
        return
    if args.command == Command.SETS:
        run_sets(args)
        return
    if args.command == Command.PINS:
        run_pins(args)
        return
    places = select_places(load_places(args.places), args.only)
    configure_osmnx()
    logger.info("Running '{}' for {} place(s)", args.command, len(places))
    for place in places:
        run_place(args.command, place, args)
        logger.info("Finished {}", place.slug)
