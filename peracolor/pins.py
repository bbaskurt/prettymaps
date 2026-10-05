"""Pinterest pin images and copy for each place.

Pinterest favours tall 2:3 images (1000x1500). Each place gets four pins:
one showing all three colourways together and one per colourway, each
linking to the place's Etsy listing. Pin text is written to a CSV so it can be
pasted into Pinterest (bulk upload needs hosted images, so images are uploaded
by hand from the pins folder).
"""

import csv
from pathlib import Path

from PIL import Image, ImageDraw
from pydantic import BaseModel

from peracolor.colourways import COLOURWAY_LABELS, COLOURWAYS, colourway_members, file_label
from peracolor.mockup import drop_shadow, framed_poster
from peracolor.models import Place
from peracolor.poster import compose_poster
from peracolor.sets import SetMember
from peracolor.style import FONT_BODY, FONT_SMALL, FONT_TITLE, INK, MUTED_INK
from peracolor.typography import draw_tracked_centred, load_font

PIN_SIZE = (1000, 1500)
PIN_BACKGROUND = (246, 243, 237)
POSTER_PREVIEW = (800, 1000)
TITLE_MAX = 100
DESCRIPTION_MAX = 500
ETSY_LISTING_URL = "https://www.etsy.com/listing/{listing_id}"
GENERAL_BOARD = "City Map Prints"
FOOTER = "PRINTABLE WALL ART  ·  INSTANT DOWNLOAD"


class PinCopy(BaseModel):
    image: str
    title: str
    description: str
    board: str
    link: str
    alt_text: str


def area_name(place: Place) -> str:
    return place.subtitle or place.city


def pin_canvas(place: Place, headline: str, headline_size: int = 38) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    canvas = Image.new("RGB", PIN_SIZE, PIN_BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    width, height = PIN_SIZE
    draw_tracked_centred(draw, place.title.upper(), load_font(FONT_TITLE, 78), width / 2, 135, 16, INK)
    draw_tracked_centred(draw, area_name(place).upper(), load_font(FONT_BODY, 34), width / 2, 200, 8, MUTED_INK)
    draw_tracked_centred(draw, headline, load_font(FONT_BODY, headline_size), width / 2, height - 120, 4, INK)
    draw_tracked_centred(draw, FOOTER, load_font(FONT_SMALL, 26), width / 2, height - 60, 4, MUTED_INK)
    return canvas, draw


def paste_with_shadow(canvas: Image.Image, image: Image.Image, left: int, top: int) -> None:
    drop_shadow(canvas, (left, top, left + image.width, top + image.height), (10, 12))
    canvas.paste(image, (left, top))


def all_colours_pin(place: Place, members: list[SetMember]) -> Image.Image:
    """Original large on top, Mono and Sage & Terracotta side by side below."""
    canvas, _ = pin_canvas(place, "3 COLOUR VERSIONS INCLUDED")
    posters = [compose_poster(m.raw_map, m.place, m.centre, POSTER_PREVIEW) for m in members]
    main = posters[0].resize((440, 550), Image.Resampling.LANCZOS)
    paste_with_shadow(canvas, main, (PIN_SIZE[0] - main.width) // 2, 260)
    small = [poster.resize((330, 412), Image.Resampling.LANCZOS) for poster in posters[1:]]
    gap = 60
    left = (PIN_SIZE[0] - sum(s.width for s in small) - gap) // 2
    for image in small:
        paste_with_shadow(canvas, image, left, 860)
        left += image.width + gap
    return canvas


def single_colour_pin(place: Place, member: SetMember, label: str) -> Image.Image:
    canvas, _ = pin_canvas(place, f"{label.upper()}  ·  3 COLOURS INCLUDED", headline_size=30)
    poster = compose_poster(member.raw_map, member.place, member.centre, POSTER_PREVIEW)
    frame = framed_poster(poster, frame_height=940)
    paste_with_shadow(canvas, frame, (PIN_SIZE[0] - frame.width) // 2, 265)
    return canvas


def pin_title(place: Place, suffix: str) -> str:
    title = f"{place.city} Map Print, {area_name(place)} Circle Map Wall Art{suffix}"
    return title[:TITLE_MAX]


def pin_description(place: Place, colour_note: str) -> str:
    text = (
        f"Colourful circle street map of {area_name(place)}, {place.city}, {place.country}. {colour_note} "
        f"Printable wall art: instant download in ISO A sizes (A1-A5) and US sizes up to 24x36. "
        f"A thoughtful housewarming, anniversary or travel gift for anyone who loves {place.city}. "
        f"#{place.city.replace(' ', '')}Map #CityMapPrint #MapWallArt #TravelWallArt #GalleryWall"
    )
    return text[:DESCRIPTION_MAX]


def write_pins(place: Place, raw_dir: Path, output_dir: Path, listing_id: int | None) -> list[PinCopy]:
    pins_dir = output_dir / "pins" / place.slug
    pins_dir.mkdir(parents=True, exist_ok=True)
    members = colourway_members(place, raw_dir)
    link = ETSY_LISTING_URL.format(listing_id=listing_id) if listing_id else ""
    board = f"{place.city} Wall Art"
    copies = []
    all_path = pins_dir / f"{place.slug}-pin-all-colours.jpg"
    all_colours_pin(place, members).save(all_path, quality=88)
    copies.append(PinCopy(
        image=str(all_path), title=pin_title(place, " | 3 Colours"), board=board, link=link,
        description=pin_description(place, "You receive all 3 colour versions: Original, Mono and Sage & Terracotta."),
        alt_text=f"Three circle map posters of {area_name(place)}, {place.city} in original, mono and sage and terracotta colours",
    ))
    for name, member in zip(COLOURWAYS, members, strict=True):
        label = COLOURWAY_LABELS[name]
        path = pins_dir / f"{place.slug}-pin-{file_label(name)}.jpg"
        single_colour_pin(place, member, label).save(path, quality=88)
        copies.append(PinCopy(
            image=str(path), title=pin_title(place, f" | {label}"), board=board if name != COLOURWAYS[0] else GENERAL_BOARD,
            link=link, description=pin_description(place, f"Shown in {label}; all 3 colour versions are included."),
            alt_text=f"Framed {label.lower()} circle map poster of {area_name(place)}, {place.city}",
        ))
    return copies


def write_pins_csv(copies: list[PinCopy], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(PinCopy.model_fields))
        writer.writeheader()
        for copy in copies:
            writer.writerow(copy.model_dump())
