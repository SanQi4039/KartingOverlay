from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class BestLapWidget(OverlayWidget):
    widget_key = "best_lap"
    display_name = widget_display_name("best_lap")
    default_width = 280
    default_height = 110

    def __init__(
        self,
        *,
        x: int,
        y: int,
        lap_result: LapDetectionResult | None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height)
        self._lap_result = lap_result

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        if self._lap_result is None or self._lap_result.best_lap is None:
            value = "--"
            subtitle = "暂无最佳圈"
        else:
            value = f"{self._lap_result.best_lap.lap_time_sec:.3f}"
            subtitle = f"第 {self._lap_result.best_lap.lap_index} 圈最佳"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="最佳圈",
            value=value,
            subtitle=subtitle,
        )
