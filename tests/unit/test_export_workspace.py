from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_service import ExportExecutionResult
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.export_workspace import ExportWorkspace


class FakeExportService:
    def __init__(self) -> None:
        self.last_execute_kwargs = None

    def execute_export(self, **kwargs):
        self.last_execute_kwargs = kwargs
        output_path = kwargs["output_path"]
        output_path.write_text("fake mov", encoding="utf-8")
        manifest_path = kwargs["manifest_path"]
        manifest_path.write_text("{}", encoding="utf-8")
        log_path = kwargs["log_path"]
        log_path.write_text("ok", encoding="utf-8")
        return ExportExecutionResult(
            command=["ffmpeg"],
            manifest_path=manifest_path,
            log_path=log_path,
            frame_count=0,
        )


class FakeVideoMetadataService:
    def runtime_status(self) -> dict:
        return {
            "ffmpeg_available": True,
            "ffmpeg_path": "C:/tools/ffmpeg.exe",
            "ffprobe_available": True,
            "ffprobe_path": "C:/tools/ffprobe.exe",
        }

    def inspect(self, path: str | Path) -> VideoMetadata:
        return VideoMetadata(
            width=1920,
            height=1080,
            fps=60000 / 1001,
            duration_sec=123.456,
            rotation_deg=90,
        )


class ImmediateExportTaskRunner:
    def __init__(self, export_service) -> None:
        self._export_service = export_service
        self.cancelled = False

    def start(self, request, *, on_progress, on_finished, on_failed, on_cancelled) -> None:
        try:
            result = self._export_service.execute_export(
                telemetry=request.telemetry,
                widgets=request.widgets,
                canvas_size=request.canvas_size,
                fps=request.fps,
                duration_sec=request.duration_sec,
                start_data_time_sec=request.start_data_time_sec,
                output_path=request.output_path,
                manifest_path=request.manifest_path,
                log_path=request.log_path,
                manifest_payload=request.manifest_payload,
            )
        except Exception as exc:
            on_failed(str(exc), request.log_path)
            return
        on_finished(result)

    def cancel(self) -> None:
        self.cancelled = True


def test_export_workspace_runs_export_and_updates_status(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    export_service = FakeExportService()
    workspace = ExportWorkspace(
        export_service=export_service,
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(export_service),
    )
    workspace.load_telemetry(telemetry)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))
    workspace.output_filename_input.setText("session_run")
    workspace.start_export()

    assert "session_run.mov" in workspace.status_label.text()
    assert workspace.fps_input.text().startswith("59.940")
    assert workspace.canvas_width_input.text() == "1080"
    assert workspace.canvas_height_input.text() == "1920"
    assert "FFmpeg" in workspace.tools_label.text()
    assert export_service.last_execute_kwargs["canvas_size"] == (1080, 1920)
    assert export_service.last_execute_kwargs["fps"] == pytest.approx(60000 / 1001)
    assert export_service.last_execute_kwargs["start_data_time_sec"] == pytest.approx(0.0)
    assert export_service.last_execute_kwargs["duration_sec"] == pytest.approx(1.0)
    assert export_service.last_execute_kwargs["manifest_payload"]["video_file"] == "sample.mp4"
    assert export_service.last_execute_kwargs["manifest_payload"]["overlay_start_video_time_sec"] == pytest.approx(0.0)
    assert export_service.last_execute_kwargs["manifest_payload"]["export_range_mode"] == "full_telemetry"
    assert export_service.last_execute_kwargs["output_path"] == tmp_path / "session_run.mov"
    assert not hasattr(workspace, "sync_offset_input")
    assert not hasattr(workspace, "range_mode_combo")
    assert workspace.output_filename_input.text() == "session_run"
    assert (tmp_path / "session_run.mov").exists()
    app.quit()


def test_export_workspace_always_exports_full_telemetry_without_sync_controls(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=10.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    export_service = FakeExportService()
    session = ProjectSession()
    workspace = ExportWorkspace(
        export_service=export_service,
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(export_service),
        session=session,
    )
    workspace.load_telemetry(telemetry)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))
    workspace.output_filename_input.setText("full_range_export.mov")

    workspace.start_export()

    assert "full_range_export.mov" in workspace.status_label.text()
    assert export_service.last_execute_kwargs["start_data_time_sec"] == pytest.approx(0.0)
    assert export_service.last_execute_kwargs["duration_sec"] == pytest.approx(10.0)
    assert export_service.last_execute_kwargs["manifest_payload"]["overlay_start_video_time_sec"] == pytest.approx(0.0)
    assert export_service.last_execute_kwargs["manifest_payload"]["export_range_mode"] == "full_telemetry"
    assert session.export_settings["range_mode"] == "full_telemetry"
    assert session.export_settings["output_filename"] == "full_range_export.mov"
    assert export_service.last_execute_kwargs["output_path"] == tmp_path / "full_range_export.mov"
    app.quit()


def test_export_workspace_pushes_output_filename_without_suffix_and_normalizes_on_export(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    export_service = FakeExportService()
    session = ProjectSession()
    workspace = ExportWorkspace(
        export_service=export_service,
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(export_service),
        session=session,
    )
    workspace.load_telemetry(telemetry)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))
    workspace.output_filename_input.setText("custom_name")
    workspace._push_export_settings()

    assert session.export_settings["output_filename"] == "custom_name"

    workspace.start_export()

    assert export_service.last_execute_kwargs["output_path"] == tmp_path / "custom_name.mov"
    assert "custom_name.mov" in workspace.status_label.text()
    app.quit()


def test_export_workspace_minimum_size_hint_stays_resizable_with_long_status_text():
    app = QApplication.instance() or QApplication([])

    class LongPathVideoMetadataService(FakeVideoMetadataService):
        def runtime_status(self) -> dict:
            long_path = (
                "C:/Users/Z/Desktop/KartOverlay-windows-x64/KartOverlay/"
                "tools/ffmpeg/bin/ffmpeg.exe"
            )
            return {
                "ffmpeg_available": True,
                "ffmpeg_path": long_path,
                "ffprobe_available": True,
                "ffprobe_path": long_path.replace("ffmpeg.exe", "ffprobe.exe"),
            }

    workspace = ExportWorkspace(
        export_service=FakeExportService(),
        video_metadata_service=LongPathVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(FakeExportService()),
    )

    assert workspace.minimumSizeHint().width() < 1200

    app.quit()
