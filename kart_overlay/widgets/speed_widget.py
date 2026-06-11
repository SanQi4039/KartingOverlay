from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class SpeedWidget(OverlayWidget):
    widget_key = "speed"
    display_name = widget_display_name("speed")
    default_width = 300
    default_height = 120

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = "--" if frame.speed_kmh is None else f"{frame.speed_kmh:.1f}"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="速度",
            value=value,
            subtitle="KM/H",
        )
