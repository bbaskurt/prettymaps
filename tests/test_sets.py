from pathlib import Path

import pytest
from pydantic import ValidationError

from peracolor.sets import PER_MAP_FORMATS, SET_SIZE, PosterSet, compose_set, load_sets
from peracolor.sizes import ETSY_MAX_FILES

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPosterSet:
    def test_set_needs_exactly_three_places(self) -> None:
        """Given a set with two places, when it is validated, then it is rejected."""
        with pytest.raises(ValidationError):
            PosterSet(slug="london-set", title="London", places=["london-big-ben", "london-tower-bridge"])

    def test_set_files_fit_etsy_file_limit(self) -> None:
        """Given the set file layout, when files are counted, then it stays within Etsy's five-file limit."""
        assert SET_SIZE * 1 + 2 <= ETSY_MAX_FILES
        assert len(PER_MAP_FORMATS) == 2

    def test_unknown_place_fails_before_any_output(self, tmp_path: Path) -> None:
        """Given a set naming a place that does not exist, when it is composed, then it raises immediately."""
        poster_set = PosterSet(slug="test-set", title="Test", places=["a", "b", "c"])

        with pytest.raises(ValueError, match="unknown places"):
            compose_set(poster_set, {}, tmp_path / "raw", tmp_path / "out")

        assert not (tmp_path / "out").exists()


def test_shipped_sets_file_is_valid() -> None:
    """Given the repository's sets.yaml, when it is loaded, then every set is valid and slugs are sorted."""
    slugs = [poster_set.slug for poster_set in load_sets(REPO_ROOT / "sets.yaml")]

    assert slugs == sorted(slugs)
