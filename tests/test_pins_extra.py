from peracolor.pins import HEADLINE_TRACKING
from peracolor.pins_extra import HEADLINE_MAX_WIDTH, SET_HEADLINE_MAX_SIZE, fitting_headline_size
from peracolor.style import FONT_BODY
from peracolor.typography import load_font, tracked_width


class TestFittingHeadlineSize:
    def test_short_headline_keeps_maximum_size(self) -> None:
        """Given a headline that already fits, when its size is chosen, then the maximum size is kept."""
        assert fitting_headline_size("BIG BEN  ·  SOHO", SET_HEADLINE_MAX_SIZE) == SET_HEADLINE_MAX_SIZE

    def test_long_headline_shrinks_to_fit_pin_width(self) -> None:
        """Given a headline too wide for the pin, when its size is chosen, then it is reduced until it fits."""
        headline = "SAGRADA FAMÍLIA  ·  PARK GÜELL  ·  PLAÇA DE CATALUNYA"

        size = fitting_headline_size(headline, SET_HEADLINE_MAX_SIZE)

        assert size < SET_HEADLINE_MAX_SIZE
        assert tracked_width(headline, load_font(FONT_BODY, size), HEADLINE_TRACKING) <= HEADLINE_MAX_WIDTH
