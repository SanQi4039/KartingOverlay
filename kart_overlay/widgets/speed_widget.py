from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import POSITIVE, draw_metric_card, draw_metric_card_dynamic, draw_metric_card_static


class SpeedWidget(OverlayWidget):
    widget_key = "speed"
    display_name = widget_display_name("speed")
    default_width = 136
    default_height = 72
    supports_static_render = True

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        self.render_static(painter)
        self.render_dynamic(painter, frame)

    def render_static(self, painter: QPainter) -> None:
        draw_metric_card_static(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            unit="km/h",
            tick_labels=("0", "90", "180"),
            **self.card_kwargs(),
        )

    def render_dynamic(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = "--" if frame.speed_kmh is None else f"{frame.speed_kmh:.0f}"
        progress = None if frame.speed_kmh is None else frame.speed_kmh / 180.0
        draw_metric_card_dynamic(
            painter,
            self.bounds_rect(),
            value=value,
            unit="km/h",
            progress=progress,
            progress_color=POSITIVE,
            tick_labels=("0", "90", "180"),
            **self.text_kwargs(),
        )
