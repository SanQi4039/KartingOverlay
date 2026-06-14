from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.application.project_session import ProjectSession, _default_output_dir
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.export_workspace import ExportWorkspace


FIXTURE_DIR = Path(__file__).resolve().parents[2]


class FakeVideoMetadataService:
    def runtime_status(self) -> dict:
        return {
            "ffmpeg_available": True,
            "ffmpeg_path": "ffmpeg",
            "ffprobe_available": True,
            "ffprobe_path": "ffprobe",
        }

    def inspect(self, path: str | Path) -> VideoMetadata:
        return VideoMetadata(
            width=1920,
            height=1080,
            fps=60.0,
            duration_sec=120.0,
            rotation_deg=90,
        )


def test_project_session_pushes_shared_state_into_export_workspace():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    session = ProjectSession()
    export_workspace = ExportWorkspace(
        session=session,
        video_metadata_service=FakeVideoMetadataService(),
    )

    session.set_telemetry(telemetry, source_path=FIXTURE_DIR / "test.gpx")
    session.set_video_path("sample.mp4")
    session.set_video_metadata(FakeVideoMetadataService().inspect("sample.mp4"))

    assert export_workspace.video_path_input.text() == "sample.mp4"
    assert export_workspace.fps_input.text().startswith("60.000")
    assert export_workspace.resolution_combo.currentData() == "original"
    assert not hasattr(export_workspace, "canvas_width_input")
    assert not hasattr(export_workspace, "canvas_height_input")
    assert export_workspace._telemetry is telemetry
    app.quit()


def test_project_session_defaults_export_output_dir_to_desktop():
    session = ProjectSession()

    assert session.export_settings["output_dir"] == _default_output_dir()
    assert session.export_settings["output_dir"]
