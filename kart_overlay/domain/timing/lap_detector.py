from dataclasses import dataclass

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.line_crossing import LineCrossing, LineCrossingDetector
from kart_overlay.domain.track.models import Point2D, TrackDefinition


@dataclass(frozen=True)
class LapRecord:
    lap_index: int
    start_time_sec: float
    end_time_sec: float
    lap_time_sec: float


@dataclass(frozen=True)
class LapDetectionResult:
    crossings: list[LineCrossing]
    laps: list[LapRecord]
    best_lap: LapRecord | None


class LapDetector:
    def __init__(self, crossing_detector: LineCrossingDetector | None = None) -> None:
        self._crossing_detector = crossing_detector or LineCrossingDetector()

    def detect(self, *, store: TelemetryStore, track_definition: TrackDefinition) -> LapDetectionResult:
        crossings: list[LineCrossing] = []
        for previous, current in zip(store.samples, store.samples[1:]):
            if (
                previous.x_m is None
                or previous.y_m is None
                or current.x_m is None
                or current.y_m is None
            ):
                continue
            crossing = self._crossing_detector.detect(
                line=track_definition.start_finish,
                previous_point=Point2D(previous.x_m, previous.y_m),
                current_point=Point2D(current.x_m, current.y_m),
                previous_time_sec=previous.elapsed_sec,
                current_time_sec=current.elapsed_sec,
            )
            if crossing is not None:
                crossings.append(crossing)

        laps: list[LapRecord] = []
        for lap_index, (start, end) in enumerate(zip(crossings, crossings[1:]), start=1):
            laps.append(
                LapRecord(
                    lap_index=lap_index,
                    start_time_sec=start.cross_time_sec,
                    end_time_sec=end.cross_time_sec,
                    lap_time_sec=end.cross_time_sec - start.cross_time_sec,
                )
            )

        best_lap = min(laps, key=lambda lap: lap.lap_time_sec) if laps else None
        return LapDetectionResult(crossings=crossings, laps=laps, best_lap=best_lap)
