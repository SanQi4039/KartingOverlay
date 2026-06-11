from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.domain.track.models import Point2D, TimingLine, TrackDefinition
from kart_overlay.ui.track_editor import TrackEditor


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


def test_track_editor_moves_start_finish_endpoint():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    editor.move_line_endpoint("start_finish", "start", (2.0, -3.0))

    assert editor.track_definition is not None
    assert editor.track_definition.start_finish.start.x == 2.0
    assert editor.track_definition.start_finish.start.y == -3.0
    app.quit()


def test_track_editor_loads_background_image_from_track_definition(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(0.0, -5.0),
                end=Point2D(0.0, 5.0),
            ),
            background_image_path=str(image_path),
        )
    )

    assert editor.has_background_image is True
    assert editor.background_image_path == str(image_path)
    assert "track-background.png" in editor.background_status_message
    app.quit()


def test_track_editor_clear_background_preserves_timing_lines(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.set_background_image_path(str(image_path))

    editor.clear_background_image()

    assert editor.track_definition is not None
    assert editor.track_definition.start_finish.name == "Start/Finish"
    assert editor.track_definition.background_image_path == ""
    assert editor.has_background_image is False
    app.quit()


def test_track_editor_fits_scene_into_view_when_resized(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)
    editor = TrackEditor()
    editor.resize(960, 640)
    editor.show()
    app.processEvents()

    editor.load_telemetry(telemetry)
    editor.set_background_image_path(str(image_path))
    app.processEvents()

    visible_bounds = editor.mapFromScene(editor.sceneRect()).boundingRect()

    assert visible_bounds.width() <= editor.viewport().width() + 4
    assert visible_bounds.height() <= editor.viewport().height() + 4
    app.quit()


def test_track_editor_display_transform_moves_overlay_layer_without_shifting_background(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.set_background_image_path(str(image_path))

    before_rect = editor._background_item.sceneBoundingRect()
    before_line = editor.editable_items()[0].line()

    editor.nudge_display_transform(delta_x=12.0, delta_y=-8.0)

    after_rect = editor._background_item.sceneBoundingRect()
    after_line = editor.editable_items()[0].line()

    assert before_rect == after_rect
    assert after_line != before_line
    app.quit()
