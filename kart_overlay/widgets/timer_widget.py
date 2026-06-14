from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import ACCENT, draw_metric_card_dynamic, draw_metric_card_static


class TimerWidget(OverlayWidget):
    widget_key = "timer"
    display_name = widget_display_name("timer")
    default_width = 190
    default_height = 122
    supports_static_render = True

    def __init__(
        self,
        *,
        x: int,
        y: int,
        analysis_summary: TrackAnalysisSummary | None = None,
        width: int | None = None,
        height: int | None = None,
        background_opacity: int | None = None,
        font_scale: float | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, background_opacity=background_opacity, font_scale=font_scale)
        self._analysis_summary = analysis_summary

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        self.render_static(painter)
        self.render_dynamic(painter, frame)

    def render_static(self, painter: QPainter) -> None:
        draw_metric_card_static(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            **self.card_kwargs(),
        )

    def render_dynamic(self, painter: QPainter, frame: TelemetryFrame) -> None:
        lap_time_sec = frame.lap_time_sec
        if self._analysis_summary is not None:
            lap_time_sec = self._analysis_summary.current_lap_time_at(frame.data_elapsed_sec)
        value = "--" if lap_time_sec is None else f"{lap_time_sec:.3f}"
        progress = None if lap_time_sec is None else (lap_time_sec % 90.0) / 90.0
        draw_metric_card_dynamic(
            painter,
            self.bounds_rect(),
            value=value,
            progress=progress,
            progress_color=ACCENT,
            **self.text_kwargs(),
        )
