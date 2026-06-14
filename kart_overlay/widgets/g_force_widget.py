from math import isfinite

from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import (
    ACCENT,
    NEGATIVE,
    POSITIVE,
    draw_card_background,
    draw_card_title,
    draw_center_g_bar,
    draw_footer_text,
    draw_g_ball,
    draw_scale_labels,
    draw_value_with_unit,
    hud_card_layout,
)


class GForceWidget(OverlayWidget):
    widget_key = "g_force"
    display_name = widget_display_name("g_force")
    label_text = "G 值 (横向)"
    default_width = 190
    default_height = 122

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = frame.accel_lat_g
        _draw_g_axis_card(
            painter,
            self.bounds_rect(),
            title=self.label_text,
            value=value,
            positive_color=NEGATIVE,
            negative_color=ACCENT,
            background_opacity=self.background_opacity,
            font_scale=self.effective_font_scale,
        )


class LongitudinalGForceWidget(OverlayWidget):
    widget_key = "g_force_longitudinal"
    display_name = widget_display_name("g_force_longitudinal")
    label_text = "G 值 (纵向)"
    default_width = 190
    default_height = 122

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        value = frame.accel_long_g
        _draw_g_axis_card(
            painter,
            self.bounds_rect(),
            title=self.label_text,
            value=value,
            positive_color=NEGATIVE,
            negative_color=ACCENT,
            background_opacity=self.background_opacity,
            font_scale=self.effective_font_scale,
        )


class GForceBallWidget(OverlayWidget):
    widget_key = "g_force_ball"
    display_name = widget_display_name("g_force_ball")
    label_text = "G 力球"
    default_width = 190
    default_height = 122

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        lat_g = frame.accel_lat_g
        long_g = frame.accel_long_g
        value = _g_magnitude(lat_g=lat_g, long_g=long_g)
        display_value = "--" if value is None else f"{value:.2f}"

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_card_background(painter, self.bounds_rect(), **self.background_kwargs())
        layout = hud_card_layout(self.bounds_rect(), font_scale=self.effective_font_scale)
        draw_card_title(painter, layout, self.label_text)
        draw_value_with_unit(painter, layout, value=display_value, unit="G")
        draw_g_ball(
            painter,
            layout.visual_rect,
            None if long_g is None or not isfinite(long_g) else long_g,
            None if lat_g is None or not isfinite(lat_g) else lat_g,
        )
        draw_footer_text(painter, layout.footer_rect, "横向 / 纵向", color=POSITIVE if value is not None else ACCENT)
        painter.restore()


def _draw_g_axis_card(
    painter: QPainter,
    rect,
    *,
    title: str,
    value: float | None,
    positive_color,
    negative_color,
    background_opacity: int | None = None,
    font_scale: float = 1.0,
) -> None:
    display_value = "--" if value is None or not isfinite(value) else f"{value:+.2f}"
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_card_background(painter, rect, background_opacity=background_opacity)
    layout = hud_card_layout(rect, font_scale=font_scale)
    draw_card_title(painter, layout, title)
    draw_value_with_unit(painter, layout, value=display_value, unit="G")
    draw_center_g_bar(
        painter,
        layout.visual_rect,
        value=None if value is None or not isfinite(value) else value,
        color_positive=positive_color,
        color_negative=negative_color,
    )
    draw_scale_labels(painter, layout.footer_rect, ("-2.0", "0", "2.0"))
    painter.restore()


def _g_magnitude(*, lat_g: float | None, long_g: float | None) -> float | None:
    if lat_g is None or long_g is None:
        return None
    if not isfinite(lat_g) or not isfinite(long_g):
        return None
    return (lat_g * lat_g + long_g * long_g) ** 0.5
