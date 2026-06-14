from pathlib import Path
from uuid import uuid4

import pytest

from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_service import ExportExecutionResult, ExportPreparationResult
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.export_workspace import ExportWorkspace


class FakeExportService:
    def __init__(self) -> None:
        self.last_prepare_kwargs = None
        self.last_execute_kwargs = None

    def prepare_export(self, **kwargs):
        self.last_prepare_kwargs = kwargs
        return ExportPreparationResult(
            command=["ffmpeg"],
            frame_timestamps=[0.0],
            encoder_label="Fake encoder",
        )

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
            encoder_label="Fake encoder",
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
                export_format=request.export_format,
            )
        except Exception as exc:
            on_failed(str(exc), request.log_path)
            return
        on_finished(result)

    def cancel(self) -> None:
        self.cancelled = True


class MutatingExportTaskRunner(ImmediateExportTaskRunner):
    def __init__(self, export_service, *, session: ProjectSession) -> None:
        super().__init__(export_service)
        self._session = session

    def start(self, request, *, on_progress, on_finished, on_failed, on_cancelled) -> None:
        self._session.set_widget_layouts(
            {
                "speed": {"x": 900, "y": 800, "width": 50, "height": 50, "enabled": True},
            }
        )
        super().start(
            request,
            on_progress=on_progress,
            on_finished=on_finished,
            on_failed=on_failed,
            on_cancelled=on_cancelled,
        )


def _enable_speed_for_export(workspace: ExportWorkspace) -> None:
    workspace._session.set_widget_layouts({"speed": {"enabled": True}})


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
    _enable_speed_for_export(workspace)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))
    workspace.output_filename_input.setText("session_run")
    workspace.start_export()

    assert "session_run.mov" in workspace.status_label.text()
    assert workspace.fps_input.text().startswith("59.940")
    assert workspace.fps_input.count() >= 6
    assert "24" in [workspace.fps_input.itemData(index) for index in range(workspace.fps_input.count())]
    assert not hasattr(workspace, "canvas_width_input")
    assert not hasattr(workspace, "canvas_height_input")
    assert "FFmpeg" in workspace.tools_label.text()
    assert "Fake encoder" in workspace.preflight_label.text()
    assert "Fake encoder" in workspace.status_label.text()
    assert export_service.last_execute_kwargs["canvas_size"] == (1080, 1920)
    assert export_service.last_execute_kwargs["fps"] == pytest.approx(60000 / 1001)
    assert export_service.last_execute_kwargs["start_data_time_sec"] == pytest.approx(0.0)
    assert export_service.last_execute_kwargs["duration_sec"] == pytest.approx(1.0)
    assert export_service.last_execute_kwargs["manifest_payload"]["video_file"] == "sample.mp4"
    assert export_service.last_execute_kwargs["manifest_payload"]["overlay_start_video_time_sec"] == pytest.approx(0.0)
    assert export_service.last_execute_kwargs["manifest_payload"]["export_range_mode"] == "full_telemetry"
    assert export_service.last_execute_kwargs["manifest_payload"]["overlay_resolution_mode"] == "original"
    assert export_service.last_execute_kwargs["output_path"] == tmp_path / "session_run.mov"
    assert not hasattr(workspace, "sync_offset_input")
    assert not hasattr(workspace, "range_mode_combo")
    assert workspace.output_filename_input.text() == "session_run"
    assert (tmp_path / "session_run.mov").exists()
    app.quit()


def test_export_workspace_selects_small_transparent_format_and_records_size_estimate(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1500.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    export_service = FakeExportService()
    workspace = ExportWorkspace(
        export_service=export_service,
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(export_service),
    )
    workspace.load_telemetry(telemetry)
    _enable_speed_for_export(workspace)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))
    workspace.output_filename_input.setText("small_overlay.mov")
    workspace.resolution_combo.setCurrentIndex(workspace.resolution_combo.findData("720p"))
    workspace.format_combo.setCurrentIndex(workspace.format_combo.findData("mov_qtrle_alpha"))

    workspace.start_export()

    manifest = export_service.last_execute_kwargs["manifest_payload"]
    assert export_service.last_prepare_kwargs["export_format"] == "mov_qtrle_alpha"
    assert export_service.last_execute_kwargs["export_format"] == "mov_qtrle_alpha"
    assert export_service.last_execute_kwargs["output_path"] == tmp_path / "small_overlay.mov"
    assert manifest["export_format"] == "mov_qtrle_alpha"
    assert manifest["alpha"] is True
    assert manifest["estimated_output_size_bytes"] > 0
    assert manifest["estimated_output_bitrate_mbps"] > 0
    assert "小体量" in workspace.format_combo.currentText()
    assert "约" in workspace.format_info_label.text()
    app.quit()


def test_export_workspace_uses_selected_common_fps_option(tmp_path: Path):
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
    _enable_speed_for_export(workspace)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))

    workspace.fps_input.setCurrentIndex(workspace.fps_input.findData("50"))
    workspace.start_export()

    assert export_service.last_execute_kwargs["fps"] == pytest.approx(50.0)
    assert session.export_settings["fps"] == "50"
    app.quit()


def test_export_workspace_resolves_overlay_resolution_modes(tmp_path: Path):
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
    _enable_speed_for_export(workspace)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))

    workspace.resolution_combo.setCurrentIndex(workspace.resolution_combo.findData("720p"))
    workspace.start_export()

    assert export_service.last_execute_kwargs["canvas_size"] == (720, 1280)
    assert export_service.last_execute_kwargs["manifest_payload"]["overlay_resolution_mode"] == "720p"

    workspace.resolution_combo.setCurrentIndex(workspace.resolution_combo.findData("1080p"))
    workspace.start_export()

    assert export_service.last_execute_kwargs["canvas_size"] == (1080, 1920)
    assert export_service.last_execute_kwargs["manifest_payload"]["overlay_resolution_mode"] == "1080p"
    app.quit()


def test_export_workspace_scales_export_widget_copies_without_mutating_session(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 153, "y": 306, "width": 303, "height": 159, "enabled": True},
            "timer": {"enabled": False},
            "altitude": {"enabled": False},
            "heading": {"enabled": False},
            "g_force": {"enabled": False},
            "lap_summary": {"enabled": False},
            "best_lap": {"enabled": False},
            "best_lap_gap": {"enabled": False},
            "sector_state": {"enabled": False},
            "coordinates": {"enabled": False},
            "mini_track": {"enabled": False},
        }
    )
    export_service = FakeExportService()
    workspace = ExportWorkspace(
        session=session,
        export_service=export_service,
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(export_service),
    )
    workspace.load_telemetry(telemetry)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))
    workspace.resolution_combo.setCurrentIndex(workspace.resolution_combo.findData("720p"))

    workspace.start_export()

    exported_speed = export_service.last_execute_kwargs["widgets"][0]
    manifest = export_service.last_execute_kwargs["manifest_payload"]

    assert export_service.last_execute_kwargs["canvas_size"] == (720, 1280)
    assert (exported_speed.x, exported_speed.y, exported_speed.width, exported_speed.height) == (102, 204, 202, 106)
    assert getattr(exported_speed, "visual_scale", 1.0) == pytest.approx(720 / 1080)
    assert getattr(exported_speed, "effective_font_scale", exported_speed.font_scale) == pytest.approx(720 / 1080)
    assert session.widget_layouts["speed"]["x"] == 153
    assert session.widget_layouts["speed"]["y"] == 306
    assert session.widget_layouts["speed"]["width"] == 303
    assert session.widget_layouts["speed"]["height"] == 159
    assert manifest["widget_original_canvas_width"] == 1080
    assert manifest["widget_original_canvas_height"] == 1920
    assert manifest["widget_target_canvas_width"] == 720
    assert manifest["widget_target_canvas_height"] == 1280
    assert manifest["widget_scale_x"] == pytest.approx(720 / 1080)
    assert manifest["widget_scale_y"] == pytest.approx(1280 / 1920)
    assert manifest["widget_visual_scale"] == pytest.approx(720 / 1080)
    app.quit()


def test_export_workspace_freezes_widget_snapshot_before_background_export(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    export_service = FakeExportService()
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 153, "y": 306, "width": 303, "height": 159, "enabled": True},
            "timer": {"enabled": False},
            "altitude": {"enabled": False},
            "heading": {"enabled": False},
            "g_force": {"enabled": False},
            "g_force_longitudinal": {"enabled": False},
            "g_force_ball": {"enabled": False},
            "lap_summary": {"enabled": False},
            "best_lap": {"enabled": False},
            "best_lap_gap": {"enabled": False},
            "lap_distance": {"enabled": False},
            "sector_state": {"enabled": False},
            "coordinates": {"enabled": False},
            "mini_track": {"enabled": False},
        }
    )
    runner = MutatingExportTaskRunner(export_service, session=session)
    workspace = ExportWorkspace(
        session=session,
        export_service=export_service,
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=runner,
    )
    workspace.load_telemetry(telemetry)
    workspace.video_path_input.setText("sample.mp4")
    workspace.read_video_metadata()
    workspace.output_dir_input.setText(str(tmp_path))

    workspace.start_export()

    exported_speed = export_service.last_execute_kwargs["widgets"][0]
    assert (exported_speed.x, exported_speed.y, exported_speed.width, exported_speed.height) == (
        153,
        306,
        303,
        159,
    )
    assert session.widget_layouts["speed"]["x"] == 900
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
    _enable_speed_for_export(workspace)
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
    _enable_speed_for_export(workspace)
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


def test_export_workspace_cancel_callback_clears_active_output_state():
    app = QApplication.instance() or QApplication([])
    output_dir = Path("build") / "test-output" / f"workspace-cancel-{uuid4().hex}"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "export.log"
    log_path.write_text("ffmpeg cancelled\ncancel cleanup completed: overlay.mov\n", encoding="utf-8")
    workspace = ExportWorkspace(
        export_service=FakeExportService(),
        video_metadata_service=FakeVideoMetadataService(),
        export_task_runner=ImmediateExportTaskRunner(FakeExportService()),
    )
    workspace._active_output_path = output_dir / "overlay.mov"
    workspace._active_encoder_label = "Fake encoder"

    workspace._handle_export_cancelled("Export cancelled during MOV encoding.", log_path)

    assert workspace._active_output_path is None
    assert workspace._active_encoder_label == ""
    assert workspace.progress_bar.value() == 0
    assert "cancelled" in workspace.status_label.text().lower()
    assert "cleanup" in workspace.log_output.toPlainText()
    app.quit()
