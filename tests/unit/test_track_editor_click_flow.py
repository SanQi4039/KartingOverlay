from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.ui.track_editor import TrackEditor


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_track_editor_click_flow_creates_start_finish_after_two_points():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")

    editor.handle_scene_click((0.0, -5.0))
    assert editor.track_definition is None

    editor.handle_scene_click((0.0, 5.0))
    assert editor.track_definition is not None
    assert editor.track_definition.start_finish.start.x == 0.0
    assert editor.track_definition.start_finish.end.y == 5.0

    app.quit()
