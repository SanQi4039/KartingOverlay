from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.ui.track_editor import TrackEditor


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_track_editor_selects_timing_line_and_exposes_visual_state():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    line_item = editor.editable_items()[0]
    line_item.select_line()

    assert editor.selected_line_key == "start_finish"
    assert line_item.is_selected_visual is True
    assert line_item.handle_count == 2
    assert "起终线" in editor.status_message
    app.quit()


def test_track_editor_clicking_existing_line_selects_it_in_edit_mode():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.resize(800, 600)
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.show()
    app.processEvents()

    line_item = editor.editable_items()[0]
    click_pos = editor.mapFromScene(line_item.line().pointAt(0.5))
    QTest.mouseClick(editor.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, click_pos)

    assert editor.selected_line_key == "start_finish"
    assert line_item.is_selected_visual is True
    app.quit()


def test_track_editor_dragging_endpoint_updates_geometry_and_status():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    line_item = editor.editable_items()[0]
    line_item.select_line()
    editor.drag_selected_endpoint("start", (2.0, -3.0))
    editor.finish_endpoint_drag()

    assert editor.track_definition is not None
    assert editor.track_definition.start_finish.start.x == 2.0
    assert editor.track_definition.start_finish.start.y == -3.0
    assert "重新计算" in editor.status_message
    app.quit()


def test_track_editor_can_delete_selected_sector_and_clear_stale_analysis():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.set_edit_mode("sector")
    editor.commit_line_from_points((10.0, -5.0), (10.0, 5.0))

    sector_item = editor.editable_items()[1]
    sector_item.select_line()
    editor.delete_selected_line()

    assert editor.track_definition is not None
    assert editor.track_definition.sectors == []
    assert editor.analysis_state is not None
    assert editor.analysis_state.summary is not None
    assert "重新计算" in editor.status_message
    app.quit()


def test_track_editor_drawing_mode_uses_cross_cursor():
    app = QApplication.instance() or QApplication([])
    editor = TrackEditor()

    editor.set_edit_mode("start_finish")

    assert editor.viewport().cursor().shape() == Qt.CursorShape.CrossCursor
    app.quit()


def test_track_editor_start_finish_line_uses_checker_style_and_no_text_label():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    line_item = editor.editable_items()[0]

    assert line_item.visual_style == "checker"
    assert line_item.label_item is None
    assert line_item.pen().widthF() <= 2.0
    app.quit()


def test_track_editor_selected_line_changes_pen_visual():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    line_item = editor.editable_items()[0]
    base_width = line_item.pen().widthF()
    line_item.select_line()

    assert line_item.pen().widthF() > base_width
    app.quit()


def test_track_editor_shows_pending_preview_line_after_first_click_for_draw_modes():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    for mode in ("start_finish", "sector"):
        editor = TrackEditor()
        editor.load_telemetry(telemetry)
        if mode == "sector":
            editor.set_edit_mode("start_finish")
            editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
        editor.set_edit_mode(mode)

        editor.handle_scene_click((0.0, -5.0))
        editor.update_pending_preview((5.0, 3.0))

        assert editor.has_pending_preview_line is True
        assert editor.has_track_path is True

    app.quit()
