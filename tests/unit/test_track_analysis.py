import pytest

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.lap_detector import LapDetectionResult, LapRecord
from kart_overlay.domain.timing.line_crossing import LineCrossing
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import TrackAnalysisBuilder, format_gap_display, gap_status
from kart_overlay.domain.timing.track_analysis import LapDistanceProfile, SectorSplitRecord, TrackAnalysisSummary
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


def test_track_analysis_builder_computes_three_segments_from_two_sector_lines():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=2, elapsed_sec=2.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=3, elapsed_sec=3.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=4, elapsed_sec=4.0, x_m=18.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=5, elapsed_sec=5.0, x_m=22.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=6, elapsed_sec=6.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=7, elapsed_sec=7.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=8, elapsed_sec=8.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=9, elapsed_sec=9.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=10, elapsed_sec=10.0, x_m=18.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=11, elapsed_sec=11.0, x_m=22.0, y_m=0.0, speed_kmh=40.0),
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
            ),
            SectorLine(
                name="S2",
                start=Point2D(20.0, -5.0),
                end=Point2D(20.0, 5.0),
                direction="negative_to_positive",
                order=2,
            ),
        ],
    )

    summary = TrackAnalysisBuilder().build(store=store, track_definition=definition)

    first_lap_splits = [split for split in summary.sector_splits if split.lap_index == 1]

    assert [split.segment_name for split in first_lap_splits] == ["S1", "S2", "S3"]
    assert [split.duration_sec for split in first_lap_splits] == pytest.approx([2.0, 2.0, 2.0])
    assert summary.current_sector_name_at(1.5) == "S1"
    assert summary.current_sector_name_at(3.5) == "S2"
    assert summary.current_sector_name_at(5.5) == "S3"
    assert summary.last_sector_times["S3"] == pytest.approx(2.0)


def test_track_analysis_formats_lap_and_best_lap_sector_gaps():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=2, elapsed_sec=1.25, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=3, elapsed_sec=1.75, x_m=12.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=4, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=5, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=6, elapsed_sec=7.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=7, elapsed_sec=8.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=8, elapsed_sec=9.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=9, elapsed_sec=10.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
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

    assert summary.best_lap_index == 2
    assert summary.lap_gap_to_best(1) == pytest.approx(1.0)
    assert summary.lap_gap_display(2).text == "BEST"
    assert summary.sector_gap_to_best_lap(1, "S1") == pytest.approx(-1.0)
    assert summary.sector_gap_display(1, "S1").status == "faster"
    assert summary.best_sector_times["S1"] == pytest.approx(1.0)
    assert summary.best_lap_sector_times["S1"] == pytest.approx(2.0)


def test_gap_display_never_turns_unknown_into_zero_and_uses_delta_semantics():
    assert format_gap_display(None).text == "--"
    assert gap_status(None) == "unknown"
    assert format_gap_display(0.675).text == "+0.675"
    assert gap_status(0.675) == "slower"
    assert format_gap_display(-0.28).text == "-0.280"
    assert gap_status(-0.28) == "faster"


def test_track_analysis_reports_current_lap_distance_and_length():
    lap = LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0)
    summary = TrackAnalysisSummary(
        lap_result=LapDetectionResult(
            crossings=[LineCrossing(cross_time_sec=0.0, ratio=0.0)],
            laps=[lap],
            best_lap=lap,
        ),
        sector_result=SectorDetectionResult(sector_crossings={}),
        lap_distance_profiles={
            1: LapDistanceProfile(
                lap_index=1,
                start_time_sec=0.0,
                end_time_sec=10.0,
                distances_m=(0.0, 50.0, 120.0),
                elapsed_offsets_sec=(0.0, 5.0, 10.0),
            )
        },
    )

    assert summary.current_lap_distance_at(5.0) == pytest.approx(50.0)
    assert summary.current_lap_length_at(5.0) == pytest.approx(120.0)
    assert summary.current_lap_distance_at(11.0) == pytest.approx(120.0)


def test_track_analysis_precomputes_lookup_indexes_for_export_timeline_queries():
    lap_1 = LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=6.0, lap_time_sec=6.0)
    lap_2 = LapRecord(lap_index=2, start_time_sec=6.0, end_time_sec=12.0, lap_time_sec=6.0)
    summary = TrackAnalysisSummary(
        lap_result=LapDetectionResult(
            crossings=[
                LineCrossing(cross_time_sec=0.0, ratio=0.0),
                LineCrossing(cross_time_sec=6.0, ratio=0.0),
                LineCrossing(cross_time_sec=12.0, ratio=0.0),
            ],
            laps=[lap_1, lap_2],
            best_lap=lap_1,
        ),
        sector_result=SectorDetectionResult(sector_crossings={}),
        sector_splits=[
            SectorSplitRecord(
                lap_index=1,
                segment_name="S1",
                start_time_sec=0.0,
                end_time_sec=2.0,
                duration_sec=2.0,
                order=1,
            ),
            SectorSplitRecord(
                lap_index=1,
                segment_name="S2",
                start_time_sec=2.0,
                end_time_sec=4.0,
                duration_sec=2.0,
                order=2,
            ),
            SectorSplitRecord(
                lap_index=1,
                segment_name="S3",
                start_time_sec=4.0,
                end_time_sec=6.0,
                duration_sec=2.0,
                order=3,
            ),
        ],
        segment_names=["S1", "S2", "S3"],
    )

    assert summary._crossing_times == (0.0, 6.0, 12.0)
    assert summary._sector_end_times_by_lap[1] == (2.0, 4.0, 6.0)
    assert summary.current_lap_number_at(7.0) == 2
    assert summary.current_lap_time_at(7.0) == pytest.approx(1.0)
    assert summary.current_sector_time_at(4.5) == pytest.approx(0.5)
    assert summary.current_sector_name_at(2.0) == "S2"
