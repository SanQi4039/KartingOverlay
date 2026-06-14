import pytest

from kart_overlay.domain.telemetry.interpolator import TelemetryInterpolator
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore


def test_telemetry_interpolator_linearly_interpolates_frame():
    store = TelemetryStore(
        samples=[
            TelemetrySample(
                sample_index=0,
                elapsed_sec=0.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=40.0,
                elevation_m=100.0,
                heading_deg=10.0,
                accel_long_g=0.1,
                accel_lat_g=0.2,
            ),
            TelemetrySample(
                sample_index=1,
                elapsed_sec=2.0,
                x_m=20.0,
                y_m=10.0,
                speed_kmh=60.0,
                elevation_m=110.0,
                heading_deg=30.0,
                accel_long_g=0.5,
                accel_lat_g=0.8,
            ),
        ]
    )

    frame = TelemetryInterpolator(store).frame_at(1.0)

    assert frame.data_elapsed_sec == pytest.approx(1.0)
    assert frame.x_m == pytest.approx(10.0)
    assert frame.y_m == pytest.approx(5.0)
    assert frame.speed_kmh == pytest.approx(50.0)
    assert frame.elevation_m == pytest.approx(105.0)
    assert frame.heading_deg == pytest.approx(20.0)
    assert frame.accel_long_g == pytest.approx(0.3)
    assert frame.accel_lat_g == pytest.approx(0.5)


def test_telemetry_interpolator_advances_cursor_for_full_sequence_export():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=index, elapsed_sec=float(index), speed_kmh=float(index * 10))
            for index in range(8)
        ]
    )
    interpolator = TelemetryInterpolator(store)

    speeds = [interpolator.frame_at(elapsed).speed_kmh for elapsed in (0.25, 1.25, 2.25, 3.25)]

    assert speeds == pytest.approx([2.5, 12.5, 22.5, 32.5])
    assert interpolator._last_sample_index >= 3


def test_telemetry_interpolator_keeps_random_access_correct_after_cursor_advance():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=index, elapsed_sec=float(index), speed_kmh=float(index * 10))
            for index in range(10)
        ]
    )
    interpolator = TelemetryInterpolator(store)

    assert interpolator.frame_at(8.5).speed_kmh == pytest.approx(85.0)
    assert interpolator.frame_at(1.5).speed_kmh == pytest.approx(15.0)
    assert interpolator.frame_at(9.0).speed_kmh == pytest.approx(90.0)
