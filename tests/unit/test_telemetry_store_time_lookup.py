import pytest

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore


def test_telemetry_store_finds_nearest_sample_for_elapsed_time():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0),
            TelemetrySample(sample_index=2, elapsed_sec=2.5),
        ]
    )

    sample = store.sample_nearest_to_elapsed_sec(1.7)

    assert sample is not None
    assert sample.sample_index == 1
    assert sample.elapsed_sec == pytest.approx(1.0)
