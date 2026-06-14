from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.widgets.heading_widget import HeadingWidget


def test_heading_widget_handles_non_finite_heading_values():
    app = QApplication.instance() or QApplication([])
    widget = HeadingWidget(x=20, y=20)

    for value in (float("nan"), float("inf"), float("-inf")):
        image = QImage(360, 180, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter(image)
        try:
            widget.render(
                painter,
                TelemetryFrame(
                    data_elapsed_sec=1.0,
                    x_m=0.0,
                    y_m=0.0,
                    speed_kmh=40.0,
                    heading_deg=value,
                ),
            )
        finally:
            painter.end()

        assert image.pixelColor(0, 0).alpha() == 0
    app.quit()
