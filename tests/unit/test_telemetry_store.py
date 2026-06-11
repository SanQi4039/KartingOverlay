from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore


def test_telemetry_store_exposes_duration_and_sample_count():
    samples = [
        TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0),
        TelemetrySample(sample_index=1, elapsed_sec=1.5, x_m=10.0, y_m=5.0),
    ]

    store = TelemetryStore(samples=samples)

    assert store.sample_count == 2
    assert store.duration_sec == 1.5
