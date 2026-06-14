from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import ACCENT, draw_metric_card, draw_metric_card_dynamic, draw_metric_card_static, draw_mini_line_chart, hud_card_layout


class HeightWidget(OverlayWidget):
    widget_key = "height"
    display_name = widget_display_name("height")
    default_width = 190
    default_height = 122
    supports_static_render = True

    def __init__(
        self,
        *,
        x: int,
        y: int,
        baseline_elevation_m: float | None = None,
        width: int | None = None,
        height: int | None = None,
        background_opacity: int | None = None,
        font_scale: float | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, background_opacity=background_opacity, font_scale=font_scale)
        self._baseline_elevation_m = baseline_elevation_m

    def render_static(self, painter: QPainter) -> None:
        draw_metric_card_static(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            unit="m",
            tick_labels=("-50", "+50"),
            **self.card_kwargs(),
        )
        layout = hud_card_layout(self.bounds_rect(), font_scale=self.effective_font_scale)
        draw_mini_line_chart(painter, layout.visual_rect, color=ACCENT)

    def render_dynamic(self, painter: QPainter, frame: TelemetryFrame) -> None:
        delta = None
        if frame.elevation_m is not None and self._baseline_elevation_m is not None:
            delta = frame.elevation_m - self._baseline_elevation_m
        value = "--" if delta is None else f"{delta:+.1f}"
        draw_metric_card_dynamic(
            painter,
            self.bounds_rect(),
            value=value,
            unit="m",
            tick_labels=("-50", "+50"),
            **self.text_kwargs(),
        )

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        delta = None
        if frame.elevation_m is not None and self._baseline_elevation_m is not None:
            delta = frame.elevation_m - self._baseline_elevation_m
        value = "--" if delta is None else f"{delta:+.1f}"
        draw_metric_card(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            value=value,
            unit="m",
            tick_labels=("-50", "+50"),
            **self.card_kwargs(),
        )
        layout = hud_card_layout(self.bounds_rect(), font_scale=self.effective_font_scale)
        draw_mini_line_chart(painter, layout.visual_rect, color=ACCENT)
