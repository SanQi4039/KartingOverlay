from dataclasses import dataclass

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.line_crossing import LineCrossing, LineCrossingDetector
from kart_overlay.domain.track.models import Point2D, TrackDefinition


@dataclass(frozen=True)
class SectorDetectionResult:
    sector_crossings: dict[str, list[LineCrossing]]


class SectorDetector:
    def __init__(self, crossing_detector: LineCrossingDetector | None = None) -> None:
        self._crossing_detector = crossing_detector or LineCrossingDetector()

    def detect(self, *, store: TelemetryStore, track_definition: TrackDefinition) -> SectorDetectionResult:
        sector_crossings: dict[str, list[LineCrossing]] = {
            sector.name: [] for sector in track_definition.sectors
        }

        for previous, current in zip(store.samples, store.samples[1:]):
            if (
                previous.x_m is None
                or previous.y_m is None
                or current.x_m is None
                or current.y_m is None
            ):
                continue
            previous_point = Point2D(previous.x_m, previous.y_m)
            current_point = Point2D(current.x_m, current.y_m)

            for sector in track_definition.sectors:
                crossing = self._crossing_detector.detect(
                    line=sector,
                    previous_point=previous_point,
                    current_point=current_point,
                    previous_time_sec=previous.elapsed_sec,
                    current_time_sec=current.elapsed_sec,
                )
                if crossing is not None:
                    sector_crossings[sector.name].append(crossing)

        return SectorDetectionResult(sector_crossings=sector_crossings)
