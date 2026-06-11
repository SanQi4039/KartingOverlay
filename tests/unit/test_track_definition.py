from kart_overlay.domain.track.models import DisplayTransform, Point2D, SectorLine, TimingLine, TrackDefinition


def test_track_definition_uses_transform_only_display_state():
    definition = TrackDefinition(
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
                direction="positive_to_negative",
                order=1,
            )
        ],
        background_image_path="assets/track.png",
    )

    assert definition.display_transform == DisplayTransform()
    assert definition.display_transform.scale == 1.0
    assert not hasattr(definition.display_transform, "basemap_provider")
    assert definition.background_image_path == "assets/track.png"
    assert definition.sectors[0].order == 1
