from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.track_analysis import TrackAnalysisBuilder
from kart_overlay.domain.track.models import Point2D, SectorLine, TimingLine, TrackDefinition
from kart_overlay.ui.track_workspace import TrackWorkspace


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_track_results_panel_promotes_lap_and_sector_values():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))
    workspace.sector_button.click()
    workspace.editor.handle_scene_click((10.0, -5.0))
    workspace.editor.handle_scene_click((10.0, 5.0))

    assert workspace.results_panel.current_lap_value.text() != "--"
    assert workspace.results_panel.best_lap_value.text() != "--"
    assert "S1" in workspace.results_panel.sector_times_value.text()
    assert workspace.results_panel.lap_list_widget.count() == len(workspace.editor.analysis_state.summary.lap_result.laps)
    app.quit()


def test_track_results_panel_lists_per_lap_sector_splits_in_row_text():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace(session=ProjectSession())
    telemetry = TelemetryStore(
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
    summary = TrackAnalysisBuilder().build(store=telemetry, track_definition=definition)

    workspace.results_panel.update_analysis(
        telemetry=telemetry,
        lap_result=summary.lap_result,
        sector_result=summary.sector_result,
        analysis_summary=summary,
    )

    first_row_text = workspace.results_panel.lap_list_widget.item(0).text()

    assert "S1 2.000 s" in first_row_text
    assert "S2 2.000 s" in first_row_text
    assert "S3 2.000 s" in first_row_text
    assert "+0.000" not in first_row_text
    app.quit()


def test_track_results_panel_shows_best_and_gap_text_in_lap_rows():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace(session=ProjectSession())
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=2, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=3, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=4, elapsed_sec=9.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=5, elapsed_sec=10.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
        ]
    )
    definition = TrackDefinition(
        start_finish=TimingLine(
            name="Start/Finish",
            start=Point2D(0.0, -5.0),
            end=Point2D(0.0, 5.0),
            direction="positive_to_negative",
        )
    )
    summary = TrackAnalysisBuilder().build(store=telemetry, track_definition=definition)

    workspace.results_panel.update_analysis(
        telemetry=telemetry,
        lap_result=summary.lap_result,
        sector_result=summary.sector_result,
        analysis_summary=summary,
    )

    first_row = workspace.results_panel.lap_list_widget.item(0).text()
    second_row = workspace.results_panel.lap_list_widget.item(1).text()

    assert "+1.000" in first_row
    assert "BEST" in second_row
    assert "+0.000" not in second_row
    app.quit()
