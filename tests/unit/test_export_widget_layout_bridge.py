from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_service import ExportExecutionResult, ExportPreparationResult
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.track.models import Point2D, TimingLine, TrackDefinition
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.export_workspace import ExportWorkspace


class FakeExportService:
    def __init__(self) -> None:
        self.last_execute_kwargs = None

    def prepare_export(self, **kwargs):
        return ExportPreparationResult(
            command=["ffmpeg"],
            frame_timestamps=[0.0],
            encoder_label="ProRes 4444 (CPU)",
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
            encoder_label="ProRes 4444 (CPU)",
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
        return VideoMetadata(width=1920, height=1080, fps=60.0, duration_sec=10.0, rotation_deg=0)


class ImmediateExportTaskRunner:
    def __init__(self, export_service) -> None:
        self._export_service = export_service

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
        return


def test_export_workspace_uses_widget_layouts_from_shared_session(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 160, "y": 220, "enabled": True},
            "timer": {"x": 300, "y": 360, "enabled": True},
            "altitude": {"x": 420, "y": 80, "enabled": True},
            "heading": {"x": 420, "y": 150, "enabled": True},
            "g_force": {"x": 520, "y": 240, "enabled": True},
            "mini_track": {"x": 900, "y": 80, "enabled": True},
            "lap_summary": {"x": 720, "y": 360, "enabled": True},
            "best_lap": {"x": 720, "y": 460, "enabled": True},
            "sector_state": {"x": 1020, "y": 320, "enabled": True},
        }
    )
    session.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(0.0, -5.0),
                end=Point2D(0.0, 5.0),
                direction="positive_to_negative",
            )
        )
    )
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=10.0, speed_kmh=50.0),
        ]
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
    workspace.start_export()

    widget_positions = {
        widget.__class__.__name__: (widget.x, widget.y)
        for widget in export_service.last_execute_kwargs["widgets"]
    }
    assert widget_positions["SpeedWidget"] == (160, 220)
    assert widget_positions["TimerWidget"] == (300, 360)
    assert widget_positions["AltitudeWidget"] == (420, 80)
    assert widget_positions["HeadingWidget"] == (420, 150)
    assert widget_positions["GForceWidget"] == (520, 240)
    assert widget_positions["MiniTrackWidget"] == (900, 80)
    assert widget_positions["LapSummaryWidget"] == (720, 360)
    assert widget_positions["BestLapWidget"] == (720, 460)
    assert widget_positions["SectorStateWidget"] == (1020, 320)
    app.quit()


def test_export_workspace_skips_hidden_widgets_from_shared_session(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 160, "y": 220, "enabled": True},
            "mini_track": {"x": 900, "y": 80, "enabled": False},
        }
    )
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=10.0, speed_kmh=50.0),
        ]
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
    workspace.start_export()

    widget_names = [widget.__class__.__name__ for widget in export_service.last_execute_kwargs["widgets"]]
    assert "SpeedWidget" in widget_names
    assert "MiniTrackWidget" not in widget_names
    app.quit()


def test_export_workspace_skips_hidden_g_force_widget_from_shared_session(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 160, "y": 220, "enabled": True},
            "g_force": {"x": 520, "y": 240, "enabled": False},
        }
    )
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=10.0, speed_kmh=50.0),
        ]
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
    workspace.start_export()

    widget_names = [widget.__class__.__name__ for widget in export_service.last_execute_kwargs["widgets"]]
    assert "SpeedWidget" in widget_names
    assert "GForceWidget" not in widget_names
    app.quit()


def test_export_workspace_uses_loaded_widget_dimensions_from_shared_session(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 160, "y": 220, "width": 420, "height": 160, "enabled": True},
            "mini_track": {"x": 900, "y": 80, "width": 280, "height": 180, "enabled": True},
        }
    )
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=10.0, speed_kmh=50.0),
        ]
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
    workspace.start_export()

    widgets = {widget.__class__.__name__: widget for widget in export_service.last_execute_kwargs["widgets"]}
    assert widgets["SpeedWidget"].width == 420
    assert widgets["SpeedWidget"].height == 160
    assert widgets["MiniTrackWidget"].width == 280
    assert widgets["MiniTrackWidget"].height == 180
    app.quit()
