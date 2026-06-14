from pathlib import Path
from threading import Event
from uuid import uuid4

from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_events import ExportCancelledError
from kart_overlay.application.export_service import ExportService
from kart_overlay.infrastructure.render.ffmpeg_exporter import FfmpegCapabilities
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.widgets.speed_widget import SpeedWidget


def test_export_service_schedules_endpoint_inclusive_frames_and_builds_stream_command(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    service = ExportService()

    result = service.prepare_export(
        telemetry=store,
        widgets=[SpeedWidget(x=20, y=40)],
        canvas_size=(320, 180),
        fps=2.0,
        duration_sec=1.0,
        output_path=tmp_path / "overlay.mov",
    )

    assert result.frame_count == 2
    assert result.frame_timestamps == [0.0, 1.0]
    assert "-i" in result.command
    assert result.command[result.command.index("-i") + 1] == "-"
    assert result.command[-1].endswith("overlay.mov")
    assert list(tmp_path.rglob("frame_*.png")) == []
    app.quit()


def test_export_service_uses_requested_small_transparent_format(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    service = ExportService()

    result = service.prepare_export(
        telemetry=store,
        widgets=[SpeedWidget(x=20, y=40)],
        canvas_size=(1280, 720),
        fps=50.0,
        duration_sec=1.0,
        output_path=tmp_path / "overlay.mov",
        export_format="mov_qtrle_alpha",
    )

    assert "qtrle" in result.command
    assert result.command[-1].endswith("overlay.mov")
    assert result.encoder_label == "MOV Animation alpha (small transparent)"
    app.quit()


def test_export_service_resolves_full_telemetry_window():
    service = ExportService()

    window = service.resolve_export_window(
        telemetry_duration_sec=20.0,
        sync_offset_sec=0.0,
        range_mode="full_telemetry",
    )

    assert window.start_video_time_sec == 0.0
    assert window.start_data_time_sec == 0.0
    assert window.duration_sec == 20.0


def test_export_service_cleans_partial_mov_and_manifest_when_cancelled():
    app = QApplication.instance() or QApplication([])
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    output_dir = Path("build") / "test-output" / f"cancel-cleanup-{uuid4().hex}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "overlay.mov"
    manifest_path = output_dir / "export_manifest.json"
    log_path = output_dir / "export.log"
    service = ExportService(exporter=_CancellingPartialFileExporter())

    try:
        service.execute_export(
            telemetry=store,
            widgets=[SpeedWidget(x=20, y=40)],
            canvas_size=(320, 180),
            fps=2.0,
            duration_sec=1.0,
            output_path=output_path,
            manifest_path=manifest_path,
            log_path=log_path,
            manifest_payload={"canvas_width": 320},
            cancel_event=Event(),
        )
    except ExportCancelledError:
        pass
    else:
        raise AssertionError("Expected export cancellation")

    assert not output_path.exists()
    assert not manifest_path.exists()
    assert log_path.exists()
    log_text = log_path.read_text(encoding="utf-8")
    assert "cancel cleanup completed" in log_text
    assert str(output_path.name) in log_text
    app.quit()


class _CancellingPartialFileExporter:
    def ensure_available(self) -> None:
        return None

    def probe_capabilities(self) -> FfmpegCapabilities:
        return FfmpegCapabilities()

    def build_command(self, *, output_path: Path, **_kwargs) -> list[str]:
        return ["ffmpeg", str(output_path)]

    def describe_encoder(self, *_args, **_kwargs) -> str:
        return "Fake cancelling encoder"

    def run(self, command: list[str], log_path: Path, *, frame_stream, cancel_event=None) -> None:
        output_path = Path(command[-1])
        output_path.write_bytes(b"partial mov")
        log_path.write_text("ffmpeg cancelled\n", encoding="utf-8")
        raise ExportCancelledError("Export cancelled during MOV encoding.")
