from pathlib import Path

import pytest

from peracolor.models import load_places
from peracolor.pins import DESCRIPTION_MAX, TITLE_MAX, pin_description, pin_title

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("place", load_places(REPO_ROOT / "places.yaml"), ids=lambda p: p.slug)
def test_pin_copy_fits_pinterest_limits(place) -> None:  # noqa: ANN001 - parametrised Place
    """Given any place, when its pin text is built, then title and description fit Pinterest's limits."""
    title = pin_title(place, " | Sage & Terracotta")
    description = pin_description(place, "You receive all 3 colour versions: Original, Mono and Sage & Terracotta.")

    assert len(title) <= TITLE_MAX
    assert len(description) <= DESCRIPTION_MAX
    assert place.city in title
