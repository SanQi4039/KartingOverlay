import pytest

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.track_analysis import TrackAnalysisBuilder
from kart_overlay.domain.track.models import Point2D, SectorLine, TimingLine, TrackDefinition


def test_track_analysis_builder_computes_lap_and_sector_times():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=2, elapsed_sec=2.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=3, elapsed_sec=3.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=4, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=5, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=6, elapsed_sec=7.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=7, elapsed_sec=8.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
        ]
    )
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

    summary = TrackAnalysisBuilder().build(store=store, track_definition=definition)

    assert summary.last_lap_time_sec == pytest.approx(5.0)
    assert summary.best_lap_time_sec == pytest.approx(5.0)
    assert summary.current_lap_time_at(7.0) == pytest.approx(1.5)
    assert summary.current_lap_number_at(0.1) == 1
    assert summary.current_lap_number_at(1.5) == 1
    assert summary.current_lap_number_at(7.0) == 2
    assert summary.current_sector_time_at(7.0) == pytest.approx(1.5)
    assert summary.last_sector_times["S1"] == pytest.approx(2.0)
    assert summary.best_sector_times["S1"] == pytest.approx(2.0)
