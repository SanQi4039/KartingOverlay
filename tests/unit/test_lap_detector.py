import pytest

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.lap_detector import LapDetector
from kart_overlay.domain.track.models import Point2D, TimingLine, TrackDefinition


def test_lap_detector_detects_crossings_and_builds_laps():
    samples = [
        TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=2, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=3, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=4, elapsed_sec=10.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=5, elapsed_sec=11.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
    ]
    store = TelemetryStore(samples=samples)
    definition = TrackDefinition(
        start_finish=TimingLine(
            name="Start/Finish",
            start=Point2D(0.0, -5.0),
            end=Point2D(0.0, 5.0),
            direction="positive_to_negative",
        )
    )

    result = LapDetector().detect(store=store, track_definition=definition)

    assert len(result.crossings) == 3
    assert len(result.laps) == 2
    assert result.laps[0].lap_time_sec == pytest.approx(5.0)
    assert result.best_lap.lap_index == 1
