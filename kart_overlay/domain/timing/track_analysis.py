from dataclasses import dataclass, field

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.lap_detector import LapDetectionResult, LapDetector
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult, SectorDetector
from kart_overlay.domain.track.models import TrackDefinition


@dataclass(frozen=True)
class SectorSplitRecord:
    lap_index: int
    segment_name: str
    start_time_sec: float
    end_time_sec: float
    duration_sec: float
    order: int


@dataclass(frozen=True)
class TrackAnalysisSummary:
    lap_result: LapDetectionResult | None
    sector_result: SectorDetectionResult
    sector_splits: list[SectorSplitRecord] = field(default_factory=list)

    @property
    def last_lap_time_sec(self) -> float | None:
        if self.lap_result is None or not self.lap_result.laps:
            return None
        return self.lap_result.laps[-1].lap_time_sec

    @property
    def best_lap_time_sec(self) -> float | None:
        if self.lap_result is None or self.lap_result.best_lap is None:
            return None
        return self.lap_result.best_lap.lap_time_sec

    @property
    def last_sector_times(self) -> dict[str, float]:
        latest: dict[str, float] = {}
        for split in self.sector_splits:
            latest[split.segment_name] = split.duration_sec
        return latest

    @property
    def best_sector_times(self) -> dict[str, float]:
        best: dict[str, float] = {}
        for split in self.sector_splits:
            previous = best.get(split.segment_name)
            if previous is None or split.duration_sec < previous:
                best[split.segment_name] = split.duration_sec
        return best

    def current_lap_time_at(self, data_time_sec: float) -> float | None:
        if self.lap_result is None:
            return None
        start_time_sec = 0.0
        for crossing in self.lap_result.crossings:
            if crossing.cross_time_sec <= data_time_sec:
                start_time_sec = crossing.cross_time_sec
            else:
                break
        return max(0.0, data_time_sec - start_time_sec)

    def current_lap_number_at(self, data_time_sec: float) -> int:
        if self.lap_result is None or not self.lap_result.crossings:
            return 1
        lap_number = 1
        for crossing in self.lap_result.crossings:
            if crossing.cross_time_sec <= data_time_sec:
                lap_number += 1
            else:
                break
        return max(1, lap_number - 1)

    def current_sector_time_at(self, data_time_sec: float) -> float | None:
        if self.lap_result is None:
            return None
        boundary_time_sec = 0.0
        for crossing in self.lap_result.crossings:
            if crossing.cross_time_sec <= data_time_sec:
                boundary_time_sec = crossing.cross_time_sec
            else:
                break
        for split in self.sector_splits:
            if split.start_time_sec <= data_time_sec:
                boundary_time_sec = max(boundary_time_sec, split.start_time_sec)
            if split.end_time_sec <= data_time_sec:
                boundary_time_sec = max(boundary_time_sec, split.end_time_sec)
        return max(0.0, data_time_sec - boundary_time_sec)

    def current_sector_name_at(self, data_time_sec: float) -> str:
        last_name = "--"
        last_time = float("-inf")
        for split in self.sector_splits:
            if split.end_time_sec <= data_time_sec and split.end_time_sec > last_time:
                last_name = split.segment_name
                last_time = split.end_time_sec
        return last_name


class TrackAnalysisBuilder:
    def __init__(
        self,
        lap_detector: LapDetector | None = None,
        sector_detector: SectorDetector | None = None,
    ) -> None:
        self._lap_detector = lap_detector or LapDetector()
        self._sector_detector = sector_detector or SectorDetector()

    def build(self, *, store: TelemetryStore, track_definition: TrackDefinition) -> TrackAnalysisSummary:
        lap_result = self._lap_detector.detect(store=store, track_definition=track_definition)
        sector_result = self._sector_detector.detect(store=store, track_definition=track_definition)
        sector_splits: list[SectorSplitRecord] = []

        ordered_sectors = sorted(track_definition.sectors, key=lambda sector: sector.order)
        for lap_index, (start_crossing, end_crossing) in enumerate(
            zip(lap_result.crossings, lap_result.crossings[1:]),
            start=1,
        ):
            boundary_time_sec = start_crossing.cross_time_sec
            for sector in ordered_sectors:
                candidates = [
                    crossing
                    for crossing in sector_result.sector_crossings.get(sector.name, [])
                    if boundary_time_sec < crossing.cross_time_sec < end_crossing.cross_time_sec
                ]
                if not candidates:
                    continue
                crossing = candidates[0]
                sector_splits.append(
                    SectorSplitRecord(
                        lap_index=lap_index,
                        segment_name=sector.name,
                        start_time_sec=boundary_time_sec,
                        end_time_sec=crossing.cross_time_sec,
                        duration_sec=crossing.cross_time_sec - boundary_time_sec,
                        order=sector.order,
                    )
                )
                boundary_time_sec = crossing.cross_time_sec

        return TrackAnalysisSummary(
            lap_result=lap_result,
            sector_result=sector_result,
            sector_splits=sector_splits,
        )
