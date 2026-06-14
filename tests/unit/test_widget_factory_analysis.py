from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.track.models import Point2D, SectorLine, TimingLine, TrackDefinition
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.widget_factory import build_widgets_from_session, default_widget_layouts


def test_default_widget_layouts_start_hidden_until_user_enables_components():
    layouts = default_widget_layouts()

    assert layouts
    assert all(layout["enabled"] is False for layout in layouts.values())


def test_widget_factory_builds_analysis_widgets_when_track_definition_exists():
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "lap_summary": {"enabled": True},
            "best_lap": {"enabled": True},
            "best_lap_gap": {"enabled": True},
            "sector_state": {"enabled": True},
            "lap_distance": {"enabled": True},
        }
    )
    session.set_telemetry(
        TelemetryStore(
            samples=[
                TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=2, elapsed_sec=2.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=3, elapsed_sec=3.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=4, elapsed_sec=5.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=5, elapsed_sec=6.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=6, elapsed_sec=7.0, x_m=8.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=7, elapsed_sec=8.0, x_m=12.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=8, elapsed_sec=10.0, x_m=2.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=9, elapsed_sec=11.0, x_m=-2.0, y_m=0.0, speed_kmh=40.0),
            ]
        )
    )
    session.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(0.0, -5.0),
                end=Point2D(0.0, 5.0),
                direction="positive_to_negative",
            ),
            sectors=[
                SectorLine(
                    name="S1",
                    start=Point2D(10.0, -5.0),
                    end=Point2D(10.0, 5.0),
                    direction="negative_to_positive",
                    order=1,
                )
            ],
        )
    )

    widgets = build_widgets_from_session(session)
    widget_names = {widget.__class__.__name__ for widget in widgets}
    display_names = {widget.display_name for widget in widgets}

    assert "LapSummaryWidget" in widget_names
    assert "BestLapWidget" in widget_names
    assert "BestLapGapWidget" in widget_names
    assert "SectorStateWidget" in widget_names
    assert "LapDistanceWidget" in widget_names
    assert widget_display_name("lap_summary") in display_names
    assert widget_display_name("best_lap") in display_names
    assert widget_display_name("best_lap_gap") in display_names
    assert widget_display_name("sector_state") in display_names
    assert widget_display_name("lap_distance") in display_names


def test_widget_factory_applies_custom_widget_dimensions_from_session_layouts():
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 40, "y": 50, "width": 420, "height": 160, "enabled": True},
        }
    )

    widgets = build_widgets_from_session(session)
    speed_widget = next(widget for widget in widgets if widget.widget_key == "speed")

    assert speed_widget.width == 420
    assert speed_widget.height == 160


def test_widget_factory_passes_background_opacity_from_session_layouts():
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {
                "x": 40,
                "y": 50,
                "width": 190,
                "height": 86,
                "enabled": True,
                "background_opacity": 42,
            },
        }
    )

    widgets = build_widgets_from_session(session)
    speed_widget = next(widget for widget in widgets if widget.widget_key == "speed")

    assert speed_widget.background_opacity == 42


def test_widget_factory_passes_font_scale_from_session_layouts():
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {
                "x": 40,
                "y": 50,
                "width": 190,
                "height": 86,
                "enabled": True,
                "font_scale": 1.3,
            },
        }
    )

    widgets = build_widgets_from_session(session)
    speed_widget = next(widget for widget in widgets if widget.widget_key == "speed")

    assert speed_widget.font_scale == 1.3


def test_widget_factory_can_hide_best_lap_gap_widget():
    session = ProjectSession()
    session.set_widget_layouts({"best_lap_gap": {"enabled": False}})

    widgets = build_widgets_from_session(session)

    assert "best_lap_gap" not in {widget.widget_key for widget in widgets}
