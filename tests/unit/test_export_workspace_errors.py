from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.export_workspace import ExportWorkspace


class MissingFfmpegExportService:
    def execute_export(self, **kwargs):
        raise FileNotFoundError("ffmpeg not found")


class MissingToolsVideoMetadataService:
    def runtime_status(self) -> dict:
        return {
            "ffmpeg_available": False,
            "ffmpeg_path": "ffmpeg",
            "ffprobe_available": True,
            "ffprobe_path": "ffprobe",
        }

    def inspect(self, path):
        return VideoMetadata(width=1920, height=1080, fps=60.0, duration_sec=10.0, rotation_deg=0)


class HealthyToolsVideoMetadataService:
    def runtime_status(self) -> dict:
        return {
            "ffmpeg_available": True,
            "ffmpeg_path": "ffmpeg",
            "ffprobe_available": True,
            "ffprobe_path": "ffprobe",
        }

    def inspect(self, path):
        return VideoMetadata(width=1920, height=1080, fps=60.0, duration_sec=10.0, rotation_deg=0)


def test_export_workspace_reports_missing_ffmpeg(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    workspace = ExportWorkspace(
        export_service=MissingFfmpegExportService(),
        video_metadata_service=MissingToolsVideoMetadataService(),
    )
    workspace.load_telemetry(telemetry)
    workspace.output_dir_input.setText(str(tmp_path))

    workspace.start_export()

    assert "ffmpeg" in workspace.status_label.text().lower()
    app.quit()


def test_export_workspace_no_longer_exposes_synced_range_controls(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    workspace = ExportWorkspace(
        export_service=MissingFfmpegExportService(),
        video_metadata_service=HealthyToolsVideoMetadataService(),
    )
    workspace.load_telemetry(telemetry)
    workspace.output_dir_input.setText(str(tmp_path))

    assert not hasattr(workspace, "sync_offset_input")
    assert not hasattr(workspace, "range_mode_combo")
    app.quit()
