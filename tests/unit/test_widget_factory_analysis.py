from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.track.models import Point2D, SectorLine, TimingLine, TrackDefinition
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.widget_factory import build_widgets_from_session


def test_widget_factory_builds_analysis_widgets_when_track_definition_exists():
    session = ProjectSession()
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
    assert "SectorStateWidget" in widget_names
    assert widget_display_name("lap_summary") in display_names
    assert widget_display_name("best_lap") in display_names
    assert widget_display_name("sector_state") in display_names


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
