from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.infrastructure.render.frame_renderer import FrameRenderer
from kart_overlay.widgets.altitude_widget import AltitudeWidget
from kart_overlay.widgets.g_force_widget import GForceWidget
from kart_overlay.widgets.heading_widget import HeadingWidget
from kart_overlay.widgets.height_widget import HeightWidget
from kart_overlay.widgets.lap_summary_widget import LapSummaryWidget
from kart_overlay.widgets.mini_track_widget import MiniTrackWidget
from kart_overlay.widgets.speed_widget import SpeedWidget
from kart_overlay.widgets.timer_widget import TimerWidget


def test_frame_renderer_produces_transparent_frame_with_widget_pixels():
    app = QApplication.instance() or QApplication([])
    renderer = FrameRenderer(
        canvas_size=(640, 360),
        widgets=[
            SpeedWidget(x=20, y=40),
            TimerWidget(x=20, y=100),
        ],
    )

    image = renderer.render(
        TelemetryFrame(
            data_elapsed_sec=12.345,
            x_m=0.0,
            y_m=0.0,
            speed_kmh=48.7,
        )
    )

    assert image.width() == 640
    assert image.height() == 360
    assert image.pixelColor(0, 0).alpha() == 0

    visible_pixel_found = False
    for y in range(0, image.height(), 8):
        for x in range(0, image.width(), 8):
            if image.pixelColor(x, y).alpha() > 0:
                visible_pixel_found = True
                break
        if visible_pixel_found:
            break

    assert visible_pixel_found
    app.quit()


def test_frame_renderer_supports_expanded_dashboard_widgets():
    app = QApplication.instance() or QApplication([])
    renderer = FrameRenderer(
        canvas_size=(960, 540),
        widgets=[
            SpeedWidget(x=20, y=40),
            TimerWidget(x=20, y=120),
            AltitudeWidget(x=20, y=200),
            HeadingWidget(x=20, y=280),
            GForceWidget(x=20, y=360),
            MiniTrackWidget(x=640, y=40),
        ],
    )

    image = renderer.render(
        TelemetryFrame(
            data_elapsed_sec=12.345,
            x_m=10.0,
            y_m=5.0,
            speed_kmh=48.7,
            lap_time_sec=12.345,
            elevation_m=120.5,
            heading_deg=42.0,
            accel_long_g=0.3,
            accel_lat_g=-0.4,
        )
    )

    visible_pixel_found = False
    for y in range(0, image.height(), 12):
        for x in range(0, image.width(), 12):
            if image.pixelColor(x, y).alpha() > 0:
                visible_pixel_found = True
                break
        if visible_pixel_found:
            break

    assert visible_pixel_found
    app.quit()


def test_frame_renderer_background_stays_transparent():
    app = QApplication.instance() or QApplication([])
    renderer = FrameRenderer(canvas_size=(100, 60), widgets=[])

    image = renderer.render(TelemetryFrame(data_elapsed_sec=0.0, x_m=None, y_m=None, speed_kmh=None))

    assert image.pixelColor(10, 10) == QColor(0, 0, 0, 0)
    app.quit()


def test_frame_renderer_caches_static_widget_layer_between_frames():
    app = QApplication.instance() or QApplication([])
    widget = _StaticLayerProbeWidget()
    renderer = FrameRenderer(canvas_size=(80, 50), widgets=[widget])

    first = renderer.render(TelemetryFrame(data_elapsed_sec=1.0, x_m=None, y_m=None, speed_kmh=None))
    second = renderer.render(TelemetryFrame(data_elapsed_sec=2.0, x_m=None, y_m=None, speed_kmh=None))

    assert widget.static_render_count == 1
    assert widget.dynamic_render_count == 2
    assert first.pixelColor(10, 10).alpha() > 0
    assert second.pixelColor(20, 20).alpha() > 0
    app.quit()


def test_frame_renderer_caches_speed_metric_card_chrome_between_frames(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = {"static": 0, "dynamic": 0}

    def fake_static(_painter, _rect, **_kwargs):
        calls["static"] += 1

    def fake_dynamic(_painter, _rect, **_kwargs):
        calls["dynamic"] += 1

    monkeypatch.setattr("kart_overlay.widgets.speed_widget.draw_metric_card_static", fake_static)
    monkeypatch.setattr("kart_overlay.widgets.speed_widget.draw_metric_card_dynamic", fake_dynamic)
    renderer = FrameRenderer(canvas_size=(120, 80), widgets=[SpeedWidget(x=0, y=0)])

    renderer.render(TelemetryFrame(data_elapsed_sec=1.0, x_m=None, y_m=None, speed_kmh=42.0))
    renderer.render(TelemetryFrame(data_elapsed_sec=2.0, x_m=None, y_m=None, speed_kmh=43.0))

    assert calls == {"static": 1, "dynamic": 2}
    app.quit()


def test_frame_renderer_caches_timer_metric_card_chrome_between_frames(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = {"static": 0, "dynamic": 0}

    def fake_static(_painter, _rect, **_kwargs):
        calls["static"] += 1

    def fake_dynamic(_painter, _rect, **_kwargs):
        calls["dynamic"] += 1

    monkeypatch.setattr("kart_overlay.widgets.timer_widget.draw_metric_card_static", fake_static)
    monkeypatch.setattr("kart_overlay.widgets.timer_widget.draw_metric_card_dynamic", fake_dynamic)
    renderer = FrameRenderer(canvas_size=(120, 80), widgets=[TimerWidget(x=0, y=0)])

    renderer.render(TelemetryFrame(data_elapsed_sec=1.0, x_m=None, y_m=None, speed_kmh=None, lap_time_sec=1.0))
    renderer.render(TelemetryFrame(data_elapsed_sec=2.0, x_m=None, y_m=None, speed_kmh=None, lap_time_sec=2.0))

    assert calls == {"static": 1, "dynamic": 2}
    app.quit()


def test_frame_renderer_caches_other_standard_metric_card_chrome_between_frames(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = {"static": 0, "dynamic": 0}

    def fake_static(_painter, _rect, **_kwargs):
        calls["static"] += 1

    def fake_dynamic(_painter, _rect, **_kwargs):
        calls["dynamic"] += 1

    for module_name in ("altitude_widget", "height_widget", "lap_summary_widget"):
        monkeypatch.setattr(f"kart_overlay.widgets.{module_name}.draw_metric_card_static", fake_static)
        monkeypatch.setattr(f"kart_overlay.widgets.{module_name}.draw_metric_card_dynamic", fake_dynamic)
    renderer = FrameRenderer(
        canvas_size=(240, 160),
        widgets=[
            AltitudeWidget(x=0, y=0),
            HeightWidget(x=0, y=50, baseline_elevation_m=100.0),
            LapSummaryWidget(x=0, y=100, lap_result=None),
        ],
    )

    renderer.render(TelemetryFrame(data_elapsed_sec=1.0, x_m=None, y_m=None, speed_kmh=None, elevation_m=101.0))
    renderer.render(TelemetryFrame(data_elapsed_sec=2.0, x_m=None, y_m=None, speed_kmh=None, elevation_m=102.0))

    assert calls == {"static": 3, "dynamic": 6}
    app.quit()


class _StaticLayerProbeWidget:
    supports_static_render = True

    def __init__(self) -> None:
        self.static_render_count = 0
        self.dynamic_render_count = 0

    def render_static(self, painter) -> None:
        self.static_render_count += 1
        painter.fillRect(0, 0, 40, 40, QColor(255, 255, 255, 80))

    def render_dynamic(self, painter, frame: TelemetryFrame) -> None:
        self.dynamic_render_count += 1
        painter.fillRect(20, 20, 10, 10, QColor(255, 0, 0, 255))
