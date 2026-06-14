from pathlib import Path
from threading import Event

import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_service import ExportCancelledError, ExportService
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.render.ffmpeg_exporter import FfmpegCapabilities, FfmpegExporter
from kart_overlay.infrastructure.render.frame_renderer import FrameRenderer
from kart_overlay.widgets.speed_widget import SpeedWidget


class FakeFfmpegExporter(FfmpegExporter):
    def __init__(self) -> None:
        super().__init__(binary_path="ffmpeg")
        self.ran_command = None
        self.frames: list[bytes] = []
        self.build_kwargs = None

    def ensure_available(self) -> None:
        return

    def probe_capabilities(self) -> FfmpegCapabilities:
        return FfmpegCapabilities(prores_vulkan_available=False)

    def build_mov_prores_command(self, *, canvas_size, fps, output_path, capabilities=None):
        self.build_kwargs = {
            "canvas_size": canvas_size,
            "fps": fps,
            "output_path": output_path,
            "capabilities": capabilities,
        }
        return super().build_mov_prores_command(
            canvas_size=canvas_size,
            fps=fps,
            output_path=output_path,
            capabilities=capabilities,
        )

    def run(self, command: list[str], log_path: Path, *, frame_stream, cancel_event=None) -> None:
        self.ran_command = command
        self.frames = []
        for frame_bytes in frame_stream:
            self.frames.append(frame_bytes)
        log_path.write_text("ffmpeg ok", encoding="utf-8")


def test_export_service_executes_export_and_streams_frames_to_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    exporter = FakeFfmpegExporter()
    service = ExportService(exporter=exporter)

    def fake_render(self, frame):
        image = QImage(320, 180, QImage.Format.Format_RGBA8888)
        image.fill(0)
        return image

    monkeypatch.setattr(FrameRenderer, "render", fake_render)

    result = service.execute_export(
        telemetry=telemetry,
        widgets=[SpeedWidget(x=20, y=40)],
        canvas_size=(320, 180),
        fps=2.0,
        duration_sec=1.0,
        output_path=tmp_path / "overlay.mov",
        manifest_path=tmp_path / "export_manifest.json",
        log_path=tmp_path / "export.log",
        manifest_payload={
            "project_name": "demo",
            "video_file": "input.mp4",
            "data_file": "input.gpx",
            "overlay_start_video_time_sec": 0.0,
            "data_duration_sec": 1.0,
            "canvas_width": 320,
            "canvas_height": 180,
            "fps": 2.0,
            "export_format": "mov_prores_4444",
            "alpha": True,
        },
    )

    assert exporter.ran_command is not None
    assert exporter.build_kwargs == {
        "canvas_size": (320, 180),
        "fps": 2.0,
        "output_path": tmp_path / "overlay.mov",
        "capabilities": FfmpegCapabilities(prores_vulkan_available=False),
    }
    assert len(exporter.frames) == 2
    assert len(exporter.frames[0]) == 320 * 180 * 4
    assert result.manifest_path.exists()
    assert result.log_path.exists()
    log_text = result.log_path.read_text(encoding="utf-8")
    assert "render_ms" in log_text
    assert "to_bytes_ms" in log_text
    assert "total_frame_ms" in log_text
    assert result.frame_count == 2
    assert result.encoder_label == "ProRes 4444 (CPU)"
    assert list(tmp_path.rglob("frame_*.png")) == []
    app.quit()


def test_export_service_emits_progress_events(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    exporter = FakeFfmpegExporter()
    service = ExportService(exporter=exporter)
    progress_events = []

    service.execute_export(
        telemetry=telemetry,
        widgets=[SpeedWidget(x=20, y=40)],
        canvas_size=(320, 180),
        fps=2.0,
        duration_sec=1.0,
        output_path=tmp_path / "overlay.mov",
        manifest_path=tmp_path / "export_manifest.json",
        log_path=tmp_path / "export.log",
        manifest_payload={"project_name": "demo"},
        progress_callback=progress_events.append,
    )

    assert progress_events
    assert progress_events[0].stage == "render"
    assert progress_events[-2].stage == "encode"
    assert progress_events[-1].percent == 100
    app.quit()


def test_export_service_supports_cancellation(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
        ]
    )
    exporter = FakeFfmpegExporter()
    service = ExportService(exporter=exporter)
    cancel_event = Event()

    def _on_progress(progress_event):
        cancel_event.set()

    with pytest.raises(ExportCancelledError):
        service.execute_export(
            telemetry=telemetry,
            widgets=[SpeedWidget(x=20, y=40)],
            canvas_size=(320, 180),
            fps=2.0,
            duration_sec=1.0,
            output_path=tmp_path / "overlay.mov",
            manifest_path=tmp_path / "export_manifest.json",
            log_path=tmp_path / "export.log",
            manifest_payload={"project_name": "demo"},
            progress_callback=_on_progress,
            cancel_event=cancel_event,
        )

    assert exporter.ran_command is not None
    assert len(exporter.frames) == 1
    app.quit()
