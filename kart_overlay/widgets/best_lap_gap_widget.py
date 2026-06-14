from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import ACCENT, NEGATIVE, POSITIVE, TEXT, draw_metric_card


class BestLapGapWidget(OverlayWidget):
    widget_key = "best_lap_gap"
    display_name = widget_display_name("best_lap_gap")
    default_width = 190
    default_height = 122

    def __init__(
        self,
        *,
        x: int,
        y: int,
        analysis_summary: TrackAnalysisSummary | None,
        width: int | None = None,
        height: int | None = None,
        background_opacity: int | None = None,
        font_scale: float | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, background_opacity=background_opacity, font_scale=font_scale)
        self._analysis_summary = analysis_summary

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        display = None if self._analysis_summary is None else self._analysis_summary.realtime_gap_display_at(
            frame.data_elapsed_sec
        )
        value = "--" if display is None else display.text
        color = TEXT if display is None else _gap_color(display.status)
        draw_metric_card(
            painter,
            self.bounds_rect(),
            title=self.display_name,
            value=value,
            unit="s" if value not in {"--", "BEST"} else "",
            value_color=color,
            progress=0.78 if display is not None else None,
            progress_color=color,
            **self.card_kwargs(),
            footer_text="快于最佳" if display is not None and display.status == "faster" else "慢于最佳" if display is not None and display.status == "slower" else "",
        )


def _gap_color(status: str):
    if status == "faster":
        return POSITIVE
    if status == "slower":
        return NEGATIVE
    if status == "best":
        return ACCENT
    return TEXT
