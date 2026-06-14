import pytest

from kart_overlay.domain.telemetry.interpolator import TelemetryInterpolator
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore


def test_telemetry_interpolator_estimates_g_force_from_motion_when_missing():
    store = TelemetryStore(
        samples=[
            TelemetrySample(
                sample_index=0,
                elapsed_sec=0.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=0.0,
                heading_deg=0.0,
            ),
            TelemetrySample(
                sample_index=1,
                elapsed_sec=1.0,
                x_m=10.0,
                y_m=0.0,
                speed_kmh=36.0,
                heading_deg=0.0,
            ),
        ]
    )

    frame = TelemetryInterpolator(store).frame_at(1.0)

    assert frame.accel_long_g is not None
    assert frame.accel_long_g > 0.0
    assert frame.accel_source == "estimated"


def test_telemetry_interpolator_prefers_real_g_force_when_available():
    store = TelemetryStore(
        samples=[
            TelemetrySample(
                sample_index=0,
                elapsed_sec=0.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=36.0,
                heading_deg=0.0,
                accel_long_g=0.25,
                accel_lat_g=0.5,
            ),
            TelemetrySample(
                sample_index=1,
                elapsed_sec=1.0,
                x_m=10.0,
                y_m=0.0,
                speed_kmh=72.0,
                heading_deg=0.0,
                accel_long_g=0.35,
                accel_lat_g=0.6,
            ),
        ]
    )

    frame = TelemetryInterpolator(store).frame_at(0.5)

    assert frame.accel_long_g == pytest.approx(0.3)
    assert frame.accel_lat_g == pytest.approx(0.55)
    assert frame.accel_source == "measured"
