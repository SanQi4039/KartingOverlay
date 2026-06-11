from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.ui.track_editor import TrackEditor


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_track_editor_can_create_start_finish_line_and_refresh_analysis():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)

    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    assert editor.track_definition is not None
    assert editor.track_definition.start_finish.name == "Start/Finish"
    assert editor.analysis_state is not None
    assert editor.analysis_state.lap_result is not None

    app.quit()


def test_track_editor_can_add_sector_line():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)

    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.set_edit_mode("sector")
    editor.commit_line_from_points((10.0, -5.0), (10.0, 5.0))

    assert editor.track_definition is not None
    assert len(editor.track_definition.sectors) == 1
    assert editor.track_definition.sectors[0].name == "S1"
    assert editor.analysis_state is not None
    assert "S1" in editor.analysis_state.sector_result.sector_crossings

    app.quit()
