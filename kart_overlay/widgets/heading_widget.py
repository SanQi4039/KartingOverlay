from math import isfinite

from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import (
    POSITIVE,
    draw_card_background,
    draw_card_title,
    draw_heading_ticks,
    draw_scale_labels,
    draw_value_with_unit,
    heading_text,
    hud_card_layout,
)


class HeadingWidget(OverlayWidget):
    widget_key = "heading"
    display_name = widget_display_name("heading")
    card_title = "方向 / 航向"
    default_width = 190
    default_height = 122

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        heading_deg = frame.heading_deg
        valid_heading = heading_deg is not None and isfinite(heading_deg)
        value = "--" if not valid_heading else f"{heading_deg:.0f}°"
        unit = "" if not valid_heading else heading_text(heading_deg)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.bounds_rect()
        draw_card_background(painter, rect, **self.background_kwargs())
        layout = hud_card_layout(rect, font_scale=self.effective_font_scale)
        draw_card_title(painter, layout, self.card_title)
        draw_value_with_unit(painter, layout, value=value, unit=unit)
        draw_heading_ticks(painter, layout.visual_rect, heading_deg=heading_deg, color=POSITIVE)
        draw_scale_labels(painter, layout.footer_rect, ("W", "N", "E"))
        painter.restore()
