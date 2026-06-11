from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class TimerWidget(OverlayWidget):
    widget_key = "timer"
    display_name = widget_display_name("timer")
    default_width = 280
    default_height = 120

    def __init__(
        self,
        *,
        x: int,
        y: int,
        analysis_summary: TrackAnalysisSummary | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height)
        self._analysis_summary = analysis_summary

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        lap_time_sec = frame.lap_time_sec
        if self._analysis_summary is not None:
            lap_time_sec = self._analysis_summary.current_lap_time_at(frame.data_elapsed_sec)
        value = "--" if lap_time_sec is None else f"{lap_time_sec:.3f}"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="当前圈",
            value=value,
            subtitle="秒",
        )
