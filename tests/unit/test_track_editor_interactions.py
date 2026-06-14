from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
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


def test_track_editor_replaces_existing_start_finish_with_new_line():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=2, elapsed_sec=2.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=3, elapsed_sec=3.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=4, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=5, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
        ]
    )
    editor = TrackEditor()
    editor.load_telemetry(telemetry)

    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.set_edit_mode("sector")
    editor.commit_line_from_points((10.0, -5.0), (10.0, 5.0))

    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((2.0, -6.0), (2.0, 6.0))

    assert editor.track_definition is not None
    assert editor.track_definition.start_finish.start.x == 2.0
    assert editor.track_definition.start_finish.start.y == -6.0
    assert editor.track_definition.start_finish.end.x == 2.0
    assert editor.track_definition.start_finish.end.y == 6.0
    assert len(editor.track_definition.sectors) == 1
    assert [item.line_key for item in editor.editable_items()].count("start_finish") == 1

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
