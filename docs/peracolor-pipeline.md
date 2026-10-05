# PeraColor poster pipeline

Turns entries in `places.yaml` into everything an Etsy digital listing needs:
print-ready posters, listing photos and listing copy.

## Setup

```bash
uv sync
```

Python 3.11 with `osmnx==1.2.2` and `shapely<2` (the versions this prettymaps fork was
written against) are pinned in `pyproject.toml`.

## Usage

```bash
uv run python -m peracolor all --only lisbon-bairro-alto        # render + posters + listing copy
uv run python -m peracolor render --palette mono --only bath     # one colourway (original | mono | sage-terracotta | pastel | blush)
uv run python -m peracolor colourways --only bath                # 3-colour package (needs original, mono and sage-terracotta renders)
uv run python -m peracolor sets                                  # three-map set listings from sets.yaml
uv run python -m peracolor palettes --only bath                  # side-by-side palette comparison sheet
uv run python -m peracolor pins                                  # Pinterest pins + pins.csv for every place in etsy_listings.yaml
```

| Command      | Network        | What it does |
|--------------|----------------|--------------|
| `render`     | first use only | Downloads the place's Geofabrik region once, extracts the area with osmium and caches a transparent circle PNG in `cache/raw/` |
| `compose`    | no             | Single-colour posters, Etsy files and listing photos |
| `colourways` | no             | One listing package with Original, Mono and Sage & Terracotta (5 zips, 5 photos) in `output/colourways/<slug>/` |
| `listing`    | no             | Writes `listing.json` (title, 13 tags, description) |
| `sets`       | no             | Three-map set packages in `output/sets/<set>/` |
| `palettes`   | no             | Renders one place in every palette for comparison |
| `pins`       | no             | 1000x1500 Pinterest pins and `output/pins/pins.csv` |
| `all`        | first use only | `render` + `compose` + `listing`, skipping cached renders |

Rendering is offline (see `peracolor/osm_offline.py`): each Geofabrik region (`osm_region` in
`places.yaml`) is downloaded once to `cache/pbf/`, so a place renders in 1-3 minutes without
touching the public Overpass API, which rate-limits and blocks heavy users. Requires
`osmium-tool` (`brew install osmium-tool`).

Keep circles off the Prime Meridian: a circle crossing 0° longitude renders as a flat strip.
Renders that are not roughly square now fail with `MalformedRenderError`.

## Etsy API

Listings are managed through the Etsy Open API v3 (`peracolor/etsy_api.py`).

1. Create an app at https://www.etsy.com/developers/your-apps with callback URL
   `http://localhost:3003/callback`.
2. Put `ETSY_API_KEYSTRING` and `ETSY_SHARED_SECRET` in `.env` (git-ignored).
3. Run `uv run python -m peracolor.etsy_auth` once and approve access in the browser; the
   token is stored in `.etsy-token.json` (git-ignored) and refreshed automatically.

`etsy_listings.yaml` maps each place to its Etsy listing id. `create_listing.py` creates
listings as free drafts and only `publish` makes them active (Etsy charges the listing fee
then). `replace_listing.py` and `colourway_listing.py` swap files, photos and copy on
existing listings without ever exceeding Etsy's five-file limit or leaving a listing empty.
Uploads must state a content type, and `rank` must not be sent for digital files.

## Output

```
output/<slug>/
  files/            upload these as the listing's digital files (max 5, each < 20 MB)
    <slug>-iso-a.jpg              A1, A2, A3, A4, A5
    <slug>-ratio-2x3.jpg          4x6" … 24x36"
    <slug>-ratio-3x4.jpg          6x8" … 18x24"
    <slug>-ratio-4x5.jpg          8x10", 16x20"
    <slug>-sizes-11x14-5x7.zip    11x14" and 5x7"
  images/           listing photos, in upload order
    01-mockup.jpg   framed poster on a sideboard
    02-poster.jpg   flat poster
    03-sizes.jpg    "sizes included" guide
  listing.json      title, tags, description
```

All master files are 300 DPI at the largest size of their ratio.

## Adding places

Add an entry to `places.yaml` (keep it sorted by slug):

```yaml
- slug: york
  title: York
  city: York
  country: United Kingdom
  query: York, United Kingdom
  centre: {lat: 53.9600, lon: -1.0810}
  radius: 1100
  tag_hints: [england map]
```

Always set `centre` to an inland point. OpenStreetMap maps the sea as coastline lines rather
than polygons, so open sea inside the circle renders as plain land colour with a hard
straight edge. Rivers, lakes and canals are polygons and render correctly.

## Custom orders

For a "Custom Circle Map" order, add the buyer's location as a new place (use their
address for `query`, look up `centre`, set `title`/`subtitle` to the text they asked for),
then run `uv run python -m peracolor all --only <slug>` and send the files in
`output/<slug>/files/`.

## Licensing

Map data © OpenStreetMap contributors (ODbL). Neither posters nor listing descriptions carry
the credit; it is given once in the shop description. Keep it there.

Montserrat is used under the SIL Open Font License (`assets/Montserrat-OFL.txt`).

## Tests

```bash
uv run pytest -v tests/
```
