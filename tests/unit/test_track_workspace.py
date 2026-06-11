from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QSplitter

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.ui.track_workspace import TrackWorkspace


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def _write_png(path: Path, *, width: int = 640, height: int = 480) -> None:
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0xFF336699)
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    path.write_bytes(bytes(data))


def test_track_workspace_updates_inspector_after_line_creation():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    assert workspace.inspector.lap_crossings_value.text() != "0"
    app.quit()


def test_track_workspace_receives_telemetry_from_shared_session():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    session.set_telemetry(telemetry, source_path=FIXTURE_DIR / "test.gpx")

    assert workspace.editor.scene().items()
    app.quit()


def test_track_workspace_publishes_track_definition_to_shared_session():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    assert session.track_definition is not None
    assert session.track_definition.start_finish.name == "Start/Finish"
    app.quit()


def test_track_workspace_publishes_recalculated_analysis_to_shared_session():
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

    assert session.track_analysis is not None
    assert session.track_analysis.lap_result is not None
    assert "S1" in session.track_analysis.sector_result.sector_crossings
    app.quit()


def test_track_workspace_shows_mode_and_selection_feedback():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()

    workspace.start_finish_button.click()

    assert workspace.editor_status_label.text()
    assert workspace.start_finish_button.isChecked() is True
    app.quit()


def test_track_workspace_reset_start_finish_clears_shared_analysis():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    workspace.reset_start_finish_button.click()

    assert session.track_definition is None
    assert session.track_analysis is None
    app.quit()


def test_track_workspace_can_apply_background_image_to_editor(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)

    workspace.set_background_image_path(image_path)

    assert workspace.editor.has_background_image is True
    assert workspace.editor.background_image_path == str(image_path)
    app.quit()


def test_track_workspace_prioritizes_editor_as_primary_right_pane():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()
    workspace.resize(1600, 900)
    workspace.show()
    app.processEvents()

    splitter = workspace.top_splitter

    assert splitter is not None
    assert splitter.widget(1) is workspace.editor
    assert splitter.sizes()[1] > splitter.sizes()[0]
    app.quit()


def test_track_workspace_uses_nested_splitters_for_results_first_layout():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace(session=ProjectSession())

    splitters = workspace.findChildren(QSplitter)

    assert len(splitters) >= 2
    assert workspace.results_panel is not None
    assert workspace.editor is not None
    assert workspace.operation_bar is not None
    app.quit()


def test_track_workspace_updates_background_status_label(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)

    workspace.set_background_image_path(image_path)

    assert "track-background.png" in workspace.background_status_label.text()
    app.quit()


def test_track_workspace_nudge_buttons_update_display_transform():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    workspace.nudge_right_button.click()
    workspace.nudge_down_button.click()

    assert workspace.editor.display_transform.translate_x > 0
    assert workspace.editor.display_transform.translate_y < 0
    app.quit()


def test_track_workspace_precise_zoom_buttons_update_display_transform_scale():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()

    before_scale = workspace.editor.display_transform.scale
    workspace.precise_zoom_in_button.click()

    assert workspace.editor.display_transform.scale > before_scale

    workspace.precise_zoom_out_button.click()

    assert workspace.editor.display_transform.scale == before_scale
    app.quit()


def test_track_workspace_returns_to_view_mode_after_interactive_line_creation():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    workspace.load_telemetry(telemetry)

    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.update_pending_preview((0.0, 5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    assert workspace.editor.edit_mode == "view"
    assert workspace.view_button.isChecked() is True
    assert workspace.start_finish_button.isChecked() is False
    app.quit()


def test_track_workspace_populates_lap_list_and_point_slider():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    workspace.point_slider.setValue(0)

    assert workspace.point_slider.maximum() == telemetry.sample_count - 1
    assert workspace.results_panel.lap_list_widget.count() == len(workspace.editor.analysis_state.summary.lap_result.laps)
    assert workspace.editor.selected_sample == telemetry.samples[0]
    assert "1 /" in workspace.point_index_label.text()
    assert "第" in workspace.point_lap_label.text()
    app.quit()


def test_track_workspace_rotate_buttons_and_precise_nudges_use_small_steps():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()

    workspace.nudge_right_button.click()
    workspace.nudge_up_button.click()
    workspace.rotate_right_button.click()

    assert workspace.editor.display_transform.translate_x == 1.0
    assert workspace.editor.display_transform.translate_y == 1.0
    assert workspace.editor.display_transform.rotation_deg == 0.5
    app.quit()
