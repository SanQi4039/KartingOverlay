from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import PURPLE, draw_metric_card


class BestLapWidget(OverlayWidget):
    widget_key = "best_lap"
    display_name = widget_display_name("best_lap")
    card_title = "最佳圈"
    default_width = 190
    default_height = 122

    def __init__(
        self,
        *,
        x: int,
        y: int,
        lap_result: LapDetectionResult | None,
        width: int | None = None,
        height: int | None = None,
        background_opacity: int | None = None,
        font_scale: float | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, background_opacity=background_opacity, font_scale=font_scale)
        self._lap_result = lap_result

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        if self._lap_result is None or self._lap_result.best_lap is None:
            value = "--"
            footer = ""
        else:
            value = f"{self._lap_result.best_lap.lap_time_sec:.3f}"
            footer = f"Lap {self._lap_result.best_lap.lap_index}"
        draw_metric_card(
            painter,
            self.bounds_rect(),
            title=self.card_title,
            value=value,
            value_color=PURPLE,
            footer_text=footer,
            **self.card_kwargs(),
        )
