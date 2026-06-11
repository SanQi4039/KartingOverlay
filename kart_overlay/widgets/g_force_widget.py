from math import sqrt

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QFont, QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import ACCENT, PRIMARY_TEXT, draw_g_ball


class GForceWidget(OverlayWidget):
    widget_key = "g_force"
    display_name = widget_display_name("g_force")
    default_width = 140
    default_height = 140

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        rect = self.bounds_rect()
        draw_g_ball(painter, rect, frame.accel_long_g, frame.accel_lat_g)

        if frame.accel_long_g is None and frame.accel_lat_g is None:
            value = "--"
        else:
            magnitude = sqrt((frame.accel_long_g or 0.0) ** 2 + (frame.accel_lat_g or 0.0) ** 2)
            value = f"{magnitude:.2f}G"

        painter.save()
        shadow_font = QFont("Segoe UI", QFont.Weight.Black)
        shadow_font.setPixelSize(self.font_px(13, minimum=10))
        shadow_font.setItalic(True)
        painter.setFont(shadow_font)
        value_height = self.length_px(28.0, minimum=20.0)
        value_rect = QRectF(rect.x(), rect.center().y() - (value_height / 2.0), rect.width(), value_height)
        painter.setPen(QColor(0, 0, 0, 130))
        shadow_offset = self.length_px(1.5, minimum=1.0)
        painter.drawText(value_rect.translated(shadow_offset, shadow_offset), value)

        painter.setPen(PRIMARY_TEXT)
        painter.drawText(value_rect, value)

        label_font = QFont("Segoe UI", QFont.Weight.Bold)
        label_font.setPixelSize(self.font_px(8, minimum=8))
        label_font.setItalic(True)
        painter.setFont(label_font)
        painter.setPen(ACCENT)
        painter.drawText(
            QRectF(rect.x(), rect.y() + self.length_px(4.0, minimum=2.0), rect.width(), self.length_px(16.0, minimum=12.0)),
            "G-FORCE",
        )
        painter.restore()
