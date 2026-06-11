from dataclasses import dataclass
from pathlib import Path
from threading import Event

from kart_overlay.application.export_events import ExportCancelledError, ExportProgressEvent
from kart_overlay.domain.telemetry.interpolator import TelemetryInterpolator
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.render.ffmpeg_exporter import FfmpegExporter
from kart_overlay.infrastructure.render.export_manifest import ExportManifestWriter
from kart_overlay.infrastructure.render.frame_renderer import FrameRenderer


@dataclass(frozen=True)
class ExportPreparationResult:
    command: list[str]
    frame_timestamps: list[float]

    @property
    def frame_count(self) -> int:
        return len(self.frame_timestamps)


@dataclass(frozen=True)
class ExportExecutionResult:
    command: list[str]
    manifest_path: Path
    log_path: Path
    frame_count: int = 0


@dataclass(frozen=True)
class ExportWindow:
    start_data_time_sec: float
    start_video_time_sec: float
    duration_sec: float


class ExportService:
    def __init__(
        self,
        exporter: FfmpegExporter | None = None,
        manifest_writer: ExportManifestWriter | None = None,
    ) -> None:
        self._exporter = exporter or FfmpegExporter()
        self._manifest_writer = manifest_writer or ExportManifestWriter()

    def prepare_export(
        self,
        *,
        telemetry: TelemetryStore,
        widgets: list[object],
        canvas_size: tuple[int, int],
        fps: float,
        duration_sec: float,
        start_data_time_sec: float = 0.0,
        output_path: Path,
        progress_callback=None,
        cancel_event: Event | None = None,
    ) -> ExportPreparationResult:
        frame_timestamps = _build_frame_timestamps(
            start_data_time_sec=start_data_time_sec,
            duration_sec=duration_sec,
            fps=fps,
        )
        command = self._exporter.build_mov_prores_command(
            canvas_size=canvas_size,
            fps=fps,
            output_path=output_path,
        )
        return ExportPreparationResult(
            command=command,
            frame_timestamps=frame_timestamps,
        )

    def resolve_export_window(
        self,
        *,
        telemetry_duration_sec: float,
        sync_offset_sec: float,
        range_mode: str,
        video_duration_sec: float | None = None,
    ) -> ExportWindow:
        if range_mode != "full_telemetry":
            raise ValueError(f"Unsupported export range mode: {range_mode}")
        return ExportWindow(
            start_data_time_sec=0.0,
            start_video_time_sec=0.0,
            duration_sec=telemetry_duration_sec,
        )

    def execute_export(
        self,
        *,
        telemetry: TelemetryStore,
        widgets: list[object],
        canvas_size: tuple[int, int],
        fps: float,
        duration_sec: float,
        start_data_time_sec: float = 0.0,
        output_path: Path,
        manifest_path: Path,
        log_path: Path,
        manifest_payload: dict,
        progress_callback=None,
        cancel_event: Event | None = None,
    ) -> ExportExecutionResult:
        self._exporter.ensure_available()
        prepared = self.prepare_export(
            telemetry=telemetry,
            widgets=widgets,
            canvas_size=canvas_size,
            fps=fps,
            duration_sec=duration_sec,
            start_data_time_sec=start_data_time_sec,
            output_path=output_path,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
        )
        if cancel_event is not None and cancel_event.is_set():
            raise ExportCancelledError("Export cancelled before encoding.")
        self._manifest_writer.write(path=manifest_path, payload=manifest_payload)
        self._exporter.run(
            prepared.command,
            log_path,
            frame_stream=self._build_frame_stream(
                telemetry=telemetry,
                widgets=widgets,
                canvas_size=canvas_size,
                frame_timestamps=prepared.frame_timestamps,
                progress_callback=progress_callback,
                cancel_event=cancel_event,
            ),
            cancel_event=cancel_event,
        )
        if progress_callback is not None:
            progress_callback(
                ExportProgressEvent(
                    stage="encode",
                    current=1,
                    total=1,
                    percent=95,
                    message="Encoding MOV alpha layer",
                )
            )
            progress_callback(
                ExportProgressEvent(
                    stage="complete",
                    current=1,
                    total=1,
                    percent=100,
                    message="Export completed",
                )
            )
        return ExportExecutionResult(
            command=prepared.command,
            manifest_path=manifest_path,
            log_path=log_path,
            frame_count=prepared.frame_count,
        )

    def _build_frame_stream(
        self,
        *,
        telemetry: TelemetryStore,
        widgets: list[object],
        canvas_size: tuple[int, int],
        frame_timestamps: list[float],
        progress_callback=None,
        cancel_event: Event | None = None,
    ):
        interpolator = TelemetryInterpolator(telemetry)
        renderer = FrameRenderer(canvas_size=canvas_size, widgets=widgets)
        total = len(frame_timestamps)
        for index, data_time in enumerate(frame_timestamps, start=1):
            if cancel_event is not None and cancel_event.is_set():
                raise ExportCancelledError("Export cancelled during frame rendering.")
            frame = interpolator.frame_at(data_time)
            if progress_callback is not None:
                progress_callback(
                    ExportProgressEvent(
                        stage="render",
                        current=index,
                        total=total,
                        percent=min(90, int(round((index / max(total, 1)) * 90))),
                        message=f"Rendering frame {index}/{total}",
                    )
                )
            yield renderer.render_rgba_bytes(frame)


def _build_frame_timestamps(
    *,
    start_data_time_sec: float,
    duration_sec: float,
    fps: float,
) -> list[float]:
    if fps <= 0:
        raise ValueError("FPS must be greater than 0.")
    if duration_sec < 0:
        raise ValueError("Duration must be non-negative.")

    frame_count = max(1, int(round(duration_sec * fps)))
    if frame_count == 1:
        return [start_data_time_sec]

    step = duration_sec / (frame_count - 1)
    return [start_data_time_sec + (step * index) for index in range(frame_count)]
