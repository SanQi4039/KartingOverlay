from typing import TYPE_CHECKING

from kart_overlay.domain.timing.track_analysis import TrackAnalysisBuilder
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.altitude_widget import AltitudeWidget
from kart_overlay.widgets.best_lap_widget import BestLapWidget
from kart_overlay.widgets.coordinates_widget import CoordinatesWidget
from kart_overlay.widgets.g_force_widget import GForceWidget
from kart_overlay.widgets.heading_widget import HeadingWidget
from kart_overlay.widgets.lap_summary_widget import LapSummaryWidget
from kart_overlay.widgets.mini_track_widget import MiniTrackWidget
from kart_overlay.widgets.sector_state_widget import SectorStateWidget
from kart_overlay.widgets.speed_widget import SpeedWidget
from kart_overlay.widgets.timer_widget import TimerWidget

if TYPE_CHECKING:
    from kart_overlay.application.project_session import ProjectSession


def default_widget_layouts() -> dict[str, dict[str, object]]:
    return {
        "speed": {"x": 56, "y": 48, "enabled": True},
        "timer": {"x": 56, "y": 184, "enabled": True},
        "altitude": {"x": 56, "y": 320, "enabled": True},
        "heading": {"x": 376, "y": 48, "enabled": True},
        "g_force": {"x": 376, "y": 184, "enabled": True},
        "lap_summary": {"x": 696, "y": 48, "enabled": True},
        "best_lap": {"x": 696, "y": 184, "enabled": True},
        "sector_state": {"x": 696, "y": 320, "enabled": True},
        "coordinates": {"x": 56, "y": 456, "enabled": False},
        "mini_track": {"x": 920, "y": 56, "enabled": True},
    }


def widget_labels() -> list[str]:
    return [display_name for _, display_name in widget_label_pairs()]


def widget_label_pairs() -> list[tuple[str, str]]:
    return [
        (widget_key, widget_display_name(widget_key))
        for widget_key in default_widget_layouts()
    ]


def build_widgets_from_session(session: "ProjectSession") -> list[object]:
    telemetry_points = []
    analysis_summary = session.track_analysis
    if session.telemetry is not None:
        telemetry_points = [
            (sample.x_m, sample.y_m)
            for sample in session.telemetry.samples
            if sample.x_m is not None and sample.y_m is not None
        ]
        if analysis_summary is None and session.track_definition is not None:
            analysis_summary = TrackAnalysisBuilder().build(
                store=session.telemetry,
                track_definition=session.track_definition,
            )

    widget_layouts = session.widget_layouts
    widgets: list[object] = []

    def _enabled(key: str) -> bool:
        return bool(widget_layouts.get(key, {}).get("enabled", True))

    def _geometry(layout: dict[str, object]) -> dict[str, int | None]:
        width = layout.get("width")
        height = layout.get("height")
        return {
            "width": None if width is None else int(width),
            "height": None if height is None else int(height),
        }

    if _enabled("speed"):
        layout = widget_layouts["speed"]
        widgets.append(
            SpeedWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                **_geometry(layout),
            )
        )
    if _enabled("timer"):
        layout = widget_layouts["timer"]
        widgets.append(
            TimerWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                analysis_summary=analysis_summary,
                **_geometry(layout),
            )
        )
    if _enabled("altitude"):
        layout = widget_layouts["altitude"]
        widgets.append(
            AltitudeWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                **_geometry(layout),
            )
        )
    if _enabled("heading"):
        layout = widget_layouts["heading"]
        widgets.append(
            HeadingWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                **_geometry(layout),
            )
        )
    if _enabled("g_force"):
        layout = widget_layouts["g_force"]
        widgets.append(
            GForceWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                **_geometry(layout),
            )
        )
    if _enabled("lap_summary"):
        layout = widget_layouts["lap_summary"]
        widgets.append(
            LapSummaryWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                lap_result=None if analysis_summary is None else analysis_summary.lap_result,
                **_geometry(layout),
            )
        )
    if _enabled("best_lap"):
        layout = widget_layouts["best_lap"]
        widgets.append(
            BestLapWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                lap_result=None if analysis_summary is None else analysis_summary.lap_result,
                **_geometry(layout),
            )
        )
    if _enabled("sector_state"):
        layout = widget_layouts["sector_state"]
        widgets.append(
            SectorStateWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                analysis_summary=analysis_summary,
                **_geometry(layout),
            )
        )
    if _enabled("coordinates"):
        layout = widget_layouts["coordinates"]
        widgets.append(
            CoordinatesWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                **_geometry(layout),
            )
        )
    if _enabled("mini_track"):
        layout = widget_layouts["mini_track"]
        widgets.append(
            MiniTrackWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                track_points=telemetry_points,
                **_geometry(layout),
            )
        )

    return widgets
