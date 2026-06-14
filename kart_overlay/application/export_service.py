from dataclasses import dataclass
from pathlib import Path
from threading import Event
from statistics import mean

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
    encoder_label: str

    @property
    def frame_count(self) -> int:
        return len(self.frame_timestamps)


@dataclass(frozen=True)
class ExportExecutionResult:
    command: list[str]
    manifest_path: Path
    log_path: Path
    frame_count: int = 0
    encoder_label: str = ""


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
        export_format: str = "mov_prores_4444",
        progress_callback=None,
        cancel_event: Event | None = None,
    ) -> ExportPreparationResult:
        capabilities = self._exporter.probe_capabilities()
        frame_timestamps = _build_frame_timestamps(
            start_data_time_sec=start_data_time_sec,
            duration_sec=duration_sec,
            fps=fps,
        )
        command = self._exporter.build_command(
            export_format=export_format,
            canvas_size=canvas_size,
            fps=fps,
            output_path=output_path,
            capabilities=capabilities,
        )
        return ExportPreparationResult(
            command=command,
            frame_timestamps=frame_timestamps,
            encoder_label=self._exporter.describe_encoder(capabilities, export_format=export_format),
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
        export_format: str = "mov_prores_4444",
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
            export_format=export_format,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
        )
        performance_records: list[dict[str, float]] = []
        try:
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
                    performance_records=performance_records,
                ),
                cancel_event=cancel_event,
            )
        except ExportCancelledError:
            _cleanup_cancelled_export_files(
                output_path=output_path,
                manifest_path=manifest_path,
                log_path=log_path,
            )
            raise
        _append_render_performance_log(log_path, performance_records)
        if progress_callback is not None:
            progress_callback(
                ExportProgressEvent(
                    stage="encode",
                    current=1,
                    total=1,
                    percent=95,
                    message=f"Encoding {prepared.encoder_label}",
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
            encoder_label=prepared.encoder_label,
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
        performance_records: list[dict[str, float]] | None = None,
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
            rendered = renderer.render_rgba_bytes_with_metrics(frame)
            if performance_records is not None:
                performance_records.append(
                    {
                        "frame_index": float(index),
                        "render_ms": rendered.render_ms,
                        "to_bytes_ms": rendered.to_bytes_ms,
                        "total_frame_ms": rendered.total_frame_ms,
                    }
                )
            yield rendered.data


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


def _append_render_performance_log(log_path: Path, records: list[dict[str, float]]) -> None:
    if not records:
        return
    lines = ["", "[perf] frame_render_summary"]
    for field in ("render_ms", "to_bytes_ms", "total_frame_ms"):
        values = [record[field] for record in records]
        lines.append(
            f"[perf] {field} avg={mean(values):.3f} p95={_p95(values):.3f} max={max(values):.3f}"
        )
    lines.append(f"[perf] frame_count={len(records)}")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def _cleanup_cancelled_export_files(
    *,
    output_path: Path,
    manifest_path: Path,
    log_path: Path,
) -> None:
    deleted: list[str] = []
    errors: list[str] = []
    for path in (output_path, manifest_path):
        try:
            if path.exists() and path.is_file():
                path.unlink()
                deleted.append(path.name)
        except OSError as exc:
            errors.append(f"{path.name}: {exc}")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["", "[cancel_cleanup] cancel cleanup completed"]
    if deleted:
        lines.append(f"[cancel_cleanup] deleted={', '.join(deleted)}")
    else:
        lines.append("[cancel_cleanup] deleted=<none>")
    if errors:
        lines.append(f"[cancel_cleanup] errors={'; '.join(errors)}")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * 0.95)))
    return ordered[index]
