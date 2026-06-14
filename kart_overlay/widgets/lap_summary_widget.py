from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import ACCENT, draw_metric_card, draw_metric_card_dynamic, draw_metric_card_static


class LapSummaryWidget(OverlayWidget):
    widget_key = "lap_summary"
    display_name = widget_display_name("lap_summary")
    card_title = "圈次"
    default_width = 190
    default_height = 122
    supports_static_render = True

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

    def render_static(self, painter: QPainter) -> None:
        draw_metric_card_static(
            painter,
            self.bounds_rect(),
            title=self.card_title,
            **self.card_kwargs(),
        )

    def render_dynamic(self, painter: QPainter, frame: TelemetryFrame) -> None:
        current_lap = self._current_lap_number(frame.data_elapsed_sec)
        total_laps = 0 if self._lap_result is None else len(self._lap_result.laps)
        unit = f"/{total_laps}" if total_laps else ""
        progress = None if total_laps <= 0 else current_lap / max(total_laps, 1)
        draw_metric_card_dynamic(
            painter,
            self.bounds_rect(),
            value=f"{current_lap}",
            unit=unit,
            progress=progress,
            progress_color=ACCENT,
            footer_text="Lap",
            **self.text_kwargs(),
        )

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        current_lap = self._current_lap_number(frame.data_elapsed_sec)
        total_laps = 0 if self._lap_result is None else len(self._lap_result.laps)
        unit = f"/{total_laps}" if total_laps else ""
        progress = None if total_laps <= 0 else current_lap / max(total_laps, 1)
        draw_metric_card(
            painter,
            self.bounds_rect(),
            title=self.card_title,
            value=f"{current_lap}",
            unit=unit,
            progress=progress,
            progress_color=ACCENT,
            footer_text="Lap",
            **self.card_kwargs(),
        )

    def _current_lap_number(self, data_time_sec: float) -> int:
        if self._lap_result is None or not self._lap_result.crossings:
            return 1
        lap_number = 1
        for crossing in self._lap_result.crossings:
            if crossing.cross_time_sec <= data_time_sec:
                lap_number += 1
        return max(1, lap_number - 1)
