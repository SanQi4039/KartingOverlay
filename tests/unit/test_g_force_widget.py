from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.widgets.g_force_widget import GForceBallWidget, GForceWidget, LongitudinalGForceWidget


def test_g_force_widgets_use_racechrono_axis_card_size():
    assert GForceWidget.default_width == 190
    assert GForceWidget.default_height == 122
    assert LongitudinalGForceWidget.default_width == 190
    assert LongitudinalGForceWidget.default_height == 122
    assert GForceBallWidget.default_width == 190
    assert GForceBallWidget.default_height == 122


def test_g_force_widgets_render_lateral_and_longitudinal_bars():
    app = QApplication.instance() or QApplication([])
    image = QImage(460, 180, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    try:
        GForceWidget(x=20, y=20).render(
            painter,
            TelemetryFrame(
                data_elapsed_sec=1.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=None,
                accel_long_g=0.35,
                accel_lat_g=-0.45,
            ),
        )
        LongitudinalGForceWidget(x=230, y=20).render(
            painter,
            TelemetryFrame(
                data_elapsed_sec=1.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=None,
                accel_long_g=0.35,
                accel_lat_g=-0.45,
            ),
        )
        GForceBallWidget(x=20, y=20).render(
            painter,
            TelemetryFrame(
                data_elapsed_sec=1.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=None,
                accel_long_g=0.35,
                accel_lat_g=-0.45,
            ),
        )
    finally:
        painter.end()

    assert _alpha_scan(image) > 0
    app.quit()


def _alpha_scan(image: QImage) -> int:
    visible = 0
    for y in range(0, image.height(), 6):
        for x in range(0, image.width(), 6):
            if image.pixelColor(x, y).alpha() > 0:
                visible += 1
    return visible
