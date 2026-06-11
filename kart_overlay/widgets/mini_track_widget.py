from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import ACCENT, BORDER, TEXT, draw_hud_card, track_normalize


class MiniTrackWidget(OverlayWidget):
    widget_key = "mini_track"
    display_name = widget_display_name("mini_track")
    default_width = 320
    default_height = 220

    def __init__(
        self,
        *,
        x: int,
        y: int,
        track_points: list[tuple[float, float]] | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height)
        self._track_points = track_points or []

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="赛道图",
            value="LIVE",
            subtitle="当前位置",
        )

        if not self._track_points:
            return

        horizontal_padding = self.length_px(16.0, minimum=8.0)
        top_padding = self.length_px(52.0, minimum=28.0)
        bottom_padding = self.length_px(16.0, minimum=10.0)
        inner_rect = QRectF(
            self.x + horizontal_padding,
            self.y + top_padding,
            self.width - (horizontal_padding * 2.0),
            self.height - top_padding - bottom_padding,
        )
        normalized = track_normalize(self._track_points, inner_rect)
        if len(normalized) < 2:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.moveTo(*normalized[0])
        for point in normalized[1:]:
            path.lineTo(*point)
        painter.setPen(QPen(BORDER, self.length_px(2.0, minimum=1.0)))
        painter.drawPath(path)

        if frame.x_m is not None and frame.y_m is not None:
            current = track_normalize([(frame.x_m, frame.y_m)], inner_rect)
            if current:
                current_x, current_y = current[0]
                radius = self.length_px(5.0, minimum=3.0)
                painter.setPen(QPen(TEXT, self.length_px(1.0, minimum=1.0)))
                painter.setBrush(ACCENT)
                painter.drawEllipse(QRectF(current_x - radius, current_y - radius, radius * 2.0, radius * 2.0))
        painter.restore()
