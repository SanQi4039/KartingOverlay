from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.export_service import ExportService
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
