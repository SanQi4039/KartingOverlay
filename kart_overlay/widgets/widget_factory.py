from typing import TYPE_CHECKING

from kart_overlay.domain.timing.track_analysis import TrackAnalysisBuilder
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.altitude_widget import AltitudeWidget
from kart_overlay.widgets.best_lap_gap_widget import BestLapGapWidget
from kart_overlay.widgets.best_lap_widget import BestLapWidget
from kart_overlay.widgets.coordinates_widget import CoordinatesWidget
from kart_overlay.widgets.g_force_widget import GForceBallWidget
from kart_overlay.widgets.g_force_widget import GForceWidget
from kart_overlay.widgets.g_force_widget import LongitudinalGForceWidget
from kart_overlay.widgets.heading_widget import HeadingWidget
from kart_overlay.widgets.height_widget import HeightWidget
from kart_overlay.widgets.hud_theme import DEFAULT_CARD_OPACITY, DEFAULT_FONT_SCALE
from kart_overlay.widgets.lap_distance_widget import LapDistanceWidget
from kart_overlay.widgets.lap_summary_widget import LapSummaryWidget
from kart_overlay.widgets.mini_track_widget import MiniTrackWidget
from kart_overlay.widgets.sector_state_widget import SectorStateWidget
from kart_overlay.widgets.speed_widget import SpeedWidget
from kart_overlay.widgets.timer_widget import TimerWidget

if TYPE_CHECKING:
    from kart_overlay.application.project_session import ProjectSession


def default_widget_layouts() -> dict[str, dict[str, object]]:
    def layout(x: int, y: int, width: int, height: int) -> dict[str, object]:
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "enabled": False,
            "background_opacity": DEFAULT_CARD_OPACITY,
            "font_scale": DEFAULT_FONT_SCALE,
        }

    return {
        "speed": layout(20, 24, SpeedWidget.default_width, SpeedWidget.default_height),
        "timer": layout(222, 24, 190, 122),
        "lap_distance": layout(424, 24, 190, 122),
        "altitude": layout(626, 24, 190, 122),
        "height": layout(828, 24, 190, 122),
        "g_force": layout(1030, 24, 190, 122),
        "g_force_longitudinal": layout(20, 158, 190, 122),
        "lap_summary": layout(222, 158, 190, 122),
        "best_lap": layout(424, 158, 190, 122),
        "best_lap_gap": layout(626, 158, 190, 122),
        "sector_state": layout(828, 158, 190, 122),
        "coordinates": layout(1030, 158, 190, 122),
        "mini_track": layout(20, 292, 392, 122),
        "heading": layout(424, 292, 190, 122),
        "g_force_ball": layout(626, 292, 190, 122),
    }


def minimum_widget_dimensions(widget_key: str, *, font_scale: float = DEFAULT_FONT_SCALE) -> tuple[int, int]:
    widget_classes = {
        "speed": SpeedWidget,
        "timer": TimerWidget,
        "lap_distance": LapDistanceWidget,
        "altitude": AltitudeWidget,
        "height": HeightWidget,
        "g_force": GForceWidget,
        "g_force_longitudinal": LongitudinalGForceWidget,
        "lap_summary": LapSummaryWidget,
        "best_lap": BestLapWidget,
        "best_lap_gap": BestLapGapWidget,
        "sector_state": SectorStateWidget,
        "coordinates": CoordinatesWidget,
        "mini_track": MiniTrackWidget,
        "heading": HeadingWidget,
        "g_force_ball": GForceBallWidget,
    }
    widget_class = widget_classes.get(widget_key)
    if widget_class is None:
        return (80, 40)
    return widget_class.minimum_dimensions(font_scale=font_scale)


def widget_labels() -> list[str]:
    return [display_name for _, display_name in widget_label_pairs()]


def widget_label_pairs() -> list[tuple[str, str]]:
    return [
        (widget_key, widget_display_name(widget_key))
        for widget_key in default_widget_layouts()
    ]


def build_widgets_from_session(session: "ProjectSession") -> list[object]:
    telemetry_points = []
    baseline_elevation_m = None
    analysis_summary = session.track_analysis
    if session.telemetry is not None:
        telemetry_points = [
            (sample.x_m, sample.y_m)
            for sample in session.telemetry.samples
            if sample.x_m is not None and sample.y_m is not None
        ]
        baseline_elevation_m = next(
            (sample.elevation_m for sample in session.telemetry.samples if sample.elevation_m is not None),
            None,
        )
        if analysis_summary is None and session.track_definition is not None:
            analysis_summary = TrackAnalysisBuilder().build(
                store=session.telemetry,
                track_definition=session.track_definition,
            )

    widget_layouts = session.widget_layouts
    widgets: list[object] = []

    def _enabled(key: str) -> bool:
        return bool(widget_layouts.get(key, {}).get("enabled", False))

    def _geometry(layout: dict[str, object]) -> dict[str, int | float | None]:
        width = layout.get("width")
        height = layout.get("height")
        background_opacity = layout.get("background_opacity")
        font_scale = layout.get("font_scale")
        return {
            "width": None if width is None else int(width),
            "height": None if height is None else int(height),
            "background_opacity": None if background_opacity is None else int(background_opacity),
            "font_scale": None if font_scale is None else float(font_scale),
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
    if _enabled("height"):
        layout = widget_layouts["height"]
        widgets.append(
            HeightWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                baseline_elevation_m=baseline_elevation_m,
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
    if _enabled("g_force_longitudinal"):
        layout = widget_layouts["g_force_longitudinal"]
        widgets.append(
            LongitudinalGForceWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                **_geometry(layout),
            )
        )
    if _enabled("g_force_ball"):
        layout = widget_layouts["g_force_ball"]
        widgets.append(
            GForceBallWidget(
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
    if _enabled("best_lap_gap"):
        layout = widget_layouts["best_lap_gap"]
        widgets.append(
            BestLapGapWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                analysis_summary=analysis_summary,
                **_geometry(layout),
            )
        )
    if _enabled("lap_distance"):
        layout = widget_layouts["lap_distance"]
        widgets.append(
            LapDistanceWidget(
                x=int(layout["x"]),
                y=int(layout["y"]),
                analysis_summary=analysis_summary,
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
