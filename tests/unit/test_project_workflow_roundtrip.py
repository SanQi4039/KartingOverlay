from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.track.models import Point2D, TimingLine, TrackDefinition
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.project_panel import ProjectPanel


class FakeTelemetryImportService:
    def import_file(self, path: str | Path) -> TelemetryStore:
        return TelemetryStore(
            samples=[
                TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0),
                TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=10.0),
            ]
        )


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
            duration_sec=95.0,
            rotation_deg=90,
        )


def test_project_panel_can_save_and_load_complete_workflow_state(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    project_path = tmp_path / "demo.kartoverlay"
    telemetry_path = tmp_path / "sample.gpx"
    telemetry_path.write_text("stub", encoding="utf-8")
    video_path = tmp_path / "sample.mp4"
    video_path.write_text("stub", encoding="utf-8")

    source_session = ProjectSession()
    source_panel = ProjectPanel(
        session=source_session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    source_session.set_telemetry(FakeTelemetryImportService().import_file(telemetry_path), source_path=telemetry_path)
    source_session.set_video_path(video_path)
    source_session.set_video_metadata(FakeVideoMetadataService().inspect(video_path))
    source_session.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(0.0, -5.0),
                end=Point2D(0.0, 5.0),
            ),
            background_image_path=str(tmp_path / "track-background.png"),
        )
    )
    source_session.set_widget_layouts(
        {
            "speed": {"x": 111, "y": 222, "enabled": True},
            "timer": {"x": 333, "y": 444, "enabled": True},
        }
    )
    source_session.set_export_settings(
        {
            "output_dir": str(tmp_path / "exports"),
            "output_filename": "roundtrip_export",
            "fps": "59.940060",
            "canvas_width": "1080",
            "canvas_height": "1920",
            "range_mode": "full_telemetry",
            "format": "mov_prores_4444",
        }
    )

    source_panel.save_project_to_path(project_path)

    loaded_session = ProjectSession()
    loaded_panel = ProjectPanel(
        session=loaded_session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    loaded_panel.load_project_from_path(project_path)
    saved_payload = project_path.read_text(encoding="utf-8")

    assert loaded_session.telemetry is not None
    assert loaded_session.video_path == str(video_path)
    assert loaded_session.video_metadata is not None
    assert '"sync"' not in saved_payload
    assert not hasattr(source_session, "sync_model")
    assert not hasattr(loaded_session, "sync_model")
    assert loaded_session.track_definition is not None
    assert loaded_session.track_definition.start_finish.name == "Start/Finish"
    assert loaded_session.track_definition.background_image_path.endswith("track-background.png")
    assert loaded_session.widget_layouts["speed"]["x"] == 111
    assert loaded_session.widget_layouts["timer"]["y"] == 444
    assert loaded_session.export_settings["output_dir"].endswith("exports")
    assert loaded_session.export_settings["output_filename"] == "roundtrip_export"
    assert loaded_session.export_settings["range_mode"] == "full_telemetry"
    assert loaded_session.export_settings["format"] == "mov_prores_4444"
    app.quit()
