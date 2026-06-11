from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card, draw_heading_gauge, heading_text


class HeadingWidget(OverlayWidget):
    widget_key = "heading"
    display_name = widget_display_name("heading")
    default_width = 280
    default_height = 110

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = "--" if frame.heading_deg is None else f"{frame.heading_deg:.0f}°"
        subtitle = f"方向 {heading_text(frame.heading_deg)}"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="航向",
            value=value,
            subtitle=subtitle,
        )
        draw_heading_gauge(painter, self.bounds_rect(), frame.heading_deg)
