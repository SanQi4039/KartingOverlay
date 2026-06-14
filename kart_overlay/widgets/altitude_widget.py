from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_metric_card, draw_metric_card_dynamic, draw_metric_card_static


class AltitudeWidget(OverlayWidget):
    widget_key = "altitude"
    display_name = widget_display_name("altitude")
    default_width = 190
    default_height = 122
    supports_static_render = True

    def render_static(self, painter: QPainter) -> None:
        draw_metric_card_static(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            **self.card_kwargs(),
        )

    def render_dynamic(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = "--" if frame.elevation_m is None else f"{frame.elevation_m:.0f}"
        draw_metric_card_dynamic(
            painter,
            self.bounds_rect(),
            value=value,
            unit="m",
            **self.text_kwargs(),
            footer_text="螖 --",
        )

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = "--" if frame.elevation_m is None else f"{frame.elevation_m:.0f}"
        footer = "Δ --"
        draw_metric_card(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            value=value,
            unit="m",
            footer_text=footer,
            **self.card_kwargs(),
        )
