from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.infrastructure.render.frame_renderer import FrameRenderer
from kart_overlay.widgets.altitude_widget import AltitudeWidget
from kart_overlay.widgets.g_force_widget import GForceWidget
from kart_overlay.widgets.heading_widget import HeadingWidget
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
