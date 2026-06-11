from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_service import ExportExecutionResult, ExportProgressEvent
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.export_workspace import ExportWorkspace


class FakeExportTaskRunner:
    def __init__(self) -> None:
        self.started = False
        self.cancelled = False
        self.request = None

    def start(self, request, *, on_progress, on_finished, on_failed, on_cancelled) -> None:
        self.started = True
        self.request = request
        on_progress(
            ExportProgressEvent(
                stage="render",
                current=1,
                total=4,
                percent=25,
                message="Rendering frame 1/4",
            )
        )
        request.log_path.write_text("ffmpeg ok", encoding="utf-8")
        on_finished(
            ExportExecutionResult(
                command=["ffmpeg"],
                manifest_path=request.manifest_path,
                log_path=request.log_path,
                frame_count=4,
            )
        )

    def cancel(self) -> None:
        self.cancelled = True


class FakeVideoMetadataService:
    def runtime_status(self) -> dict:
        return {
            "ffmpeg_available": True,
            "ffmpeg_path": "ffmpeg",
            "ffprobe_available": True,
            "ffprobe_path": "ffprobe",
        }

    def inspect(self, path):
        return VideoMetadata(width=1920, height=1080, fps=60.0, duration_sec=10.0, rotation_deg=0)


def test_export_workspace_displays_runner_progress_and_logs(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    runner = FakeExportTaskRunner()
    workspace = ExportWorkspace(
        session=ProjectSession(),
        export_task_runner=runner,
        video_metadata_service=FakeVideoMetadataService(),
    )
    workspace.load_telemetry(telemetry)
    workspace.output_dir_input.setText(str(tmp_path))

    workspace.start_export()

    assert runner.started is True
    assert workspace.progress_bar.value() == 100
    assert "导出完成" in workspace.status_label.text()
    assert workspace.log_output.toPlainText() == "ffmpeg ok"
    app.quit()


def test_export_workspace_can_request_runner_cancellation(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    runner = FakeExportTaskRunner()
    workspace = ExportWorkspace(
        session=ProjectSession(),
        export_task_runner=runner,
        video_metadata_service=FakeVideoMetadataService(),
    )
    workspace.load_telemetry(telemetry)
    workspace.output_dir_input.setText(str(tmp_path))

    workspace._set_export_running(True)
    workspace.cancel_export()

    assert runner.cancelled is True
    app.quit()
