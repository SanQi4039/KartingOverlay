from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class LapSummaryWidget(OverlayWidget):
    widget_key = "lap_summary"
    display_name = widget_display_name("lap_summary")
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
        current_lap = self._current_lap_number(frame.data_elapsed_sec)
        total_laps = 0 if self._lap_result is None else len(self._lap_result.laps)
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="圈数",
            value=f"{current_lap:02d}",
            subtitle=f"已完成 {total_laps} 圈",
        )

    def _current_lap_number(self, data_time_sec: float) -> int:
        if self._lap_result is None or not self._lap_result.crossings:
            return 1
        lap_number = 1
        for crossing in self._lap_result.crossings:
            if crossing.cross_time_sec <= data_time_sec:
                lap_number += 1
        return max(1, lap_number - 1)
