from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class SectorStateWidget(OverlayWidget):
    widget_key = "sector_state"
    display_name = widget_display_name("sector_state")
    default_width = 300
    default_height = 110

    def __init__(
        self,
        *,
        x: int,
        y: int,
        analysis_summary: TrackAnalysisSummary | None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height)
        self._analysis_summary = analysis_summary

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        last_sector = self._last_sector_name(frame.data_elapsed_sec)
        sector_time_sec = None if self._analysis_summary is None else self._analysis_summary.current_sector_time_at(frame.data_elapsed_sec)
        value = "--" if sector_time_sec is None else f"{sector_time_sec:.3f}"
        subtitle = last_sector
        if self._analysis_summary is not None:
            best_times = self._analysis_summary.best_sector_times
            if last_sector in best_times:
                subtitle = f"{last_sector} 最佳 {best_times[last_sector]:.3f} 秒"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="分段",
            value=value,
            subtitle=subtitle,
        )

    def _last_sector_name(self, data_time_sec: float) -> str:
        if self._analysis_summary is None:
            return "--"
        return self._analysis_summary.current_sector_name_at(data_time_sec)
