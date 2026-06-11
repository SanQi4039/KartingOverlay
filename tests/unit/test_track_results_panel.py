from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.application.project_session import ProjectSession
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
