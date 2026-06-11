import pytest

from kart_overlay.domain.timing.line_crossing import LineCrossingDetector
from kart_overlay.domain.track.models import Point2D, TimingLine


def test_line_crossing_detector_interpolates_crossing_time():
    detector = LineCrossingDetector()
    line = TimingLine(
        name="Start/Finish",
        start=Point2D(0.0, -5.0),
        end=Point2D(0.0, 5.0),
        direction="positive_to_negative",
    )

    crossing = detector.detect(
        line=line,
        previous_point=Point2D(3.0, 0.0),
        current_point=Point2D(-1.0, 0.0),
        previous_time_sec=10.0,
        current_time_sec=12.0,
    )

    assert crossing is not None
    assert crossing.cross_time_sec == pytest.approx(11.5)
    assert crossing.ratio == pytest.approx(0.75)


def test_line_crossing_detector_rejects_wrong_direction():
    detector = LineCrossingDetector()
    line = TimingLine(
        name="Start/Finish",
        start=Point2D(0.0, -5.0),
        end=Point2D(0.0, 5.0),
        direction="positive_to_negative",
    )

    crossing = detector.detect(
        line=line,
        previous_point=Point2D(-1.0, 0.0),
        current_point=Point2D(3.0, 0.0),
        previous_time_sec=10.0,
        current_time_sec=12.0,
    )

    assert crossing is None
