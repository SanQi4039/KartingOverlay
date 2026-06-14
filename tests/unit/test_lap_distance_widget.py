from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.lap_detector import LapDetectionResult, LapRecord
from kart_overlay.domain.timing.line_crossing import LineCrossing
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import LapDistanceProfile, TrackAnalysisSummary
from kart_overlay.widgets.lap_distance_widget import LapDistanceWidget


def test_lap_distance_widget_uses_profile_distance_and_clamps_progress(monkeypatch):
    captured: dict[str, object] = {}

    def fake_draw(_painter, _rect, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("kart_overlay.widgets.lap_distance_widget.draw_lap_progress_card", fake_draw)
    widget = LapDistanceWidget(
        x=0,
        y=0,
        analysis_summary=_summary(
            LapDistanceProfile(
                lap_index=1,
                start_time_sec=0.0,
                end_time_sec=10.0,
                distances_m=(0.0, 80.0, 150.0),
                elapsed_offsets_sec=(0.0, 5.0, 10.0),
            )
        ),
    )

    widget.render(
        None,
        TelemetryFrame(data_elapsed_sec=12.0, x_m=None, y_m=None, speed_kmh=None),
    )

    assert captured["title"] == "圈已行驶距离"
    assert captured["value"] == "150"
    assert captured["unit"] == "m"
    assert captured["progress"] == 1.0
    assert captured["min_label"] == "0"
    assert captured["max_label"] == "150"


def test_lap_distance_widget_keeps_missing_data_empty(monkeypatch):
    captured: dict[str, object] = {}

    def fake_draw(_painter, _rect, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("kart_overlay.widgets.lap_distance_widget.draw_lap_progress_card", fake_draw)
    widget = LapDistanceWidget(x=0, y=0, analysis_summary=None)

    widget.render(
        None,
        TelemetryFrame(data_elapsed_sec=3.0, x_m=None, y_m=None, speed_kmh=None),
    )

    assert captured["value"] == "--"
    assert captured["unit"] == "m"
    assert captured["progress"] is None
    assert captured["max_label"] == ""


def _summary(profile: LapDistanceProfile) -> TrackAnalysisSummary:
    lap = LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0)
    return TrackAnalysisSummary(
        lap_result=LapDetectionResult(
            crossings=[LineCrossing(cross_time_sec=0.0, ratio=0.0)],
            laps=[lap],
            best_lap=lap,
        ),
        sector_result=SectorDetectionResult(sector_crossings={}),
        lap_distance_profiles={1: profile},
    )
