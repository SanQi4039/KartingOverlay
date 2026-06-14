from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_lap_progress_card


class LapDistanceWidget(OverlayWidget):
    widget_key = "lap_distance"
    display_name = widget_display_name("lap_distance")
    card_title = "圈已行驶距离"
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
        lap_distance_m = None
        lap_length_m = None
        if self._analysis_summary is not None:
            lap_distance_m = self._analysis_summary.current_lap_distance_at(frame.data_elapsed_sec)
            lap_length_m = self._analysis_summary.current_lap_length_at(frame.data_elapsed_sec)

        if lap_distance_m is None:
            value = "--"
            progress = None
            max_label = ""
        else:
            value = f"{lap_distance_m:.0f}"
            if lap_length_m is None or lap_length_m <= 0.0:
                progress = None
                max_label = ""
            else:
                progress = max(0.0, min(lap_distance_m / lap_length_m, 1.0))
                max_label = f"{lap_length_m:.0f}"

        draw_lap_progress_card(
            painter,
            self.bounds_rect(),
            title=self.card_title,
            value=value,
            unit="m",
            progress=progress,
            min_label="0",
            max_label=max_label,
            **self.card_kwargs(),
        )
