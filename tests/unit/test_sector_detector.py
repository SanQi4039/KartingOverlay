import pytest

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.sector_detector import SectorDetector
from kart_overlay.domain.track.models import Point2D, SectorLine, TimingLine, TrackDefinition


def test_sector_detector_detects_sector_crossings_between_laps():
    samples = [
        TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=2, elapsed_sec=2.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=3, elapsed_sec=3.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=4, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=5, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=6, elapsed_sec=7.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
        TelemetrySample(sample_index=7, elapsed_sec=8.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
    ]
    store = TelemetryStore(samples=samples)
    definition = TrackDefinition(
        start_finish=TimingLine(
            name="Start/Finish",
            start=Point2D(0.0, -5.0),
            end=Point2D(0.0, 5.0),
            direction="positive_to_negative",
        ),
        sectors=[
            SectorLine(
                name="S1",
                start=Point2D(10.0, -5.0),
                end=Point2D(10.0, 5.0),
                direction="negative_to_positive",
                order=1,
            )
        ],
    )

    result = SectorDetector().detect(store=store, track_definition=definition)

    assert len(result.sector_crossings["S1"]) == 2
    assert result.sector_crossings["S1"][0].cross_time_sec == pytest.approx(2.5)
