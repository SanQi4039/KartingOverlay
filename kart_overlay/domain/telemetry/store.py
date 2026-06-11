from dataclasses import dataclass, field

from kart_overlay.domain.telemetry.models import TelemetrySample


@dataclass(frozen=True)
class TelemetryStore:
    samples: list[TelemetrySample]
    source_format: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    quality_report: dict[str, object] = field(default_factory=dict)

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def duration_sec(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].elapsed_sec - self.samples[0].elapsed_sec

    def sample_nearest_to_elapsed_sec(self, elapsed_sec: float) -> TelemetrySample | None:
        if not self.samples:
            return None
        return min(
            self.samples,
            key=lambda sample: abs(sample.elapsed_sec - elapsed_sec),
        )
