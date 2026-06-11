from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.domain.track.models import Point2D, SectorLine, TimingLine, TrackDefinition
from kart_overlay.ui.track_editor import TrackEditor


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_track_editor_loads_real_telemetry_path():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()

    editor.load_telemetry(telemetry)

    assert editor.scene().items()
    app.quit()


def test_track_editor_renders_track_definition_lines():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()

    editor.load_telemetry(telemetry)
    editor.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(-5.0, -5.0),
                end=Point2D(-5.0, 5.0),
            ),
            sectors=[
                SectorLine(
                    name="S1",
                    start=Point2D(5.0, -5.0),
                    end=Point2D(5.0, 5.0),
                    order=1,
                )
            ],
        )
    )

    assert len(editor.scene().items()) >= 3
    app.quit()
