from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import MUTED, TEXT, draw_card_background, draw_card_title, hud_card_layout


class CoordinatesWidget(OverlayWidget):
    widget_key = "coordinates"
    display_name = widget_display_name("coordinates")
    default_width = 190
    default_height = 122

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        lat_text = "--" if frame.lat is None else f"{frame.lat:.6f} N"
        lon_text = "--" if frame.lon is None else f"{frame.lon:.6f} E"
        rect = self.bounds_rect()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_card_background(painter, rect, **self.background_kwargs())
        layout = hud_card_layout(rect, font_scale=self.effective_font_scale)
        draw_card_title(painter, layout, self.display_name)

        font = QFont("Roboto Mono", QFont.Weight.Medium)
        font.setPixelSize(max(14, int(round(18 * layout.ratio))))
        painter.setFont(font)
        painter.setPen(TEXT)
        line_h = layout.value_rect.height() / 2
        painter.drawText(
            QRectF(layout.value_rect.x(), layout.value_rect.y(), layout.value_rect.width(), line_h),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            lat_text,
        )
        painter.drawText(
            QRectF(layout.value_rect.x(), layout.value_rect.y() + line_h, layout.value_rect.width(), line_h),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            lon_text,
        )
        painter.setPen(MUTED)
        painter.drawText(layout.footer_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "GPS")
        painter.restore()
