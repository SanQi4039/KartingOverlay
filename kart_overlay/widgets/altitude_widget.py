from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class AltitudeWidget(OverlayWidget):
    widget_key = "altitude"
    display_name = widget_display_name("altitude")
    default_width = 260
    default_height = 110

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = "--" if frame.elevation_m is None else f"{frame.elevation_m:.1f} m"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="海拔",
            value=value,
            subtitle="GPS 高程",
        )
