from bisect import bisect_left, bisect_right
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
class GapDisplay:
    value_sec: float | None
    text: str
    status: str


@dataclass(frozen=True)
class LapDistanceProfile:
    lap_index: int
    start_time_sec: float
    end_time_sec: float
    distances_m: tuple[float, ...]
    elapsed_offsets_sec: tuple[float, ...]

    @property
    def total_distance_m(self) -> float:
        return self.distances_m[-1] if self.distances_m else 0.0

    def distance_at_time(self, data_time_sec: float) -> float | None:
        if not self.elapsed_offsets_sec or self.total_distance_m <= 0.0:
            return None
        elapsed = data_time_sec - self.start_time_sec
        return _interpolate(self.elapsed_offsets_sec, self.distances_m, elapsed)

    def elapsed_at_distance(self, distance_m: float) -> float | None:
        if not self.distances_m or self.total_distance_m <= 0.0:
            return None
        clamped = max(0.0, min(distance_m, self.total_distance_m))
        return _interpolate(self.distances_m, self.elapsed_offsets_sec, clamped)


@dataclass(frozen=True)
class TrackAnalysisSummary:
    lap_result: LapDetectionResult | None
    sector_result: SectorDetectionResult
    sector_splits: list[SectorSplitRecord] = field(default_factory=list)
    segment_names: list[str] = field(default_factory=list)
    lap_distance_profiles: dict[int, LapDistanceProfile] = field(default_factory=dict)
    _crossing_times: tuple[float, ...] = field(init=False, repr=False, compare=False)
    _lap_records_by_index: dict[int, object] = field(init=False, repr=False, compare=False)
    _sector_splits_by_lap: dict[int, tuple[SectorSplitRecord, ...]] = field(init=False, repr=False, compare=False)
    _sector_end_times_by_lap: dict[int, tuple[float, ...]] = field(init=False, repr=False, compare=False)
    _sector_names_by_lap: dict[int, tuple[str, ...]] = field(init=False, repr=False, compare=False)
    _sector_split_by_lap_and_name: dict[tuple[int, str], SectorSplitRecord] = field(init=False, repr=False, compare=False)
    _best_lap_sector_times: dict[str, float] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        crossings = () if self.lap_result is None else tuple(
            crossing.cross_time_sec for crossing in self.lap_result.crossings
        )
        lap_records = {} if self.lap_result is None else {
            record.lap_index: record for record in self.lap_result.laps
        }
        splits_by_lap: dict[int, list[SectorSplitRecord]] = {}
        split_by_lap_and_name: dict[tuple[int, str], SectorSplitRecord] = {}
        for split in self.sector_splits:
            splits_by_lap.setdefault(split.lap_index, []).append(split)
            split_by_lap_and_name[(split.lap_index, split.segment_name)] = split

        ordered_splits_by_lap: dict[int, tuple[SectorSplitRecord, ...]] = {}
        sector_end_times_by_lap: dict[int, tuple[float, ...]] = {}
        sector_names_by_lap: dict[int, tuple[str, ...]] = {}
        for lap_index, splits in splits_by_lap.items():
            ordered = tuple(sorted(splits, key=lambda split: split.order))
            ordered_splits_by_lap[lap_index] = ordered
            sector_end_times_by_lap[lap_index] = tuple(split.end_time_sec for split in ordered)
            sector_names_by_lap[lap_index] = tuple(split.segment_name for split in ordered)

        best_lap_index = None
        if self.lap_result is not None and self.lap_result.best_lap is not None:
            best_lap_index = self.lap_result.best_lap.lap_index
        best_lap_sector_times = {
            split.segment_name: split.duration_sec
            for split in ordered_splits_by_lap.get(best_lap_index, ())
        }

        object.__setattr__(self, "_crossing_times", crossings)
        object.__setattr__(self, "_lap_records_by_index", lap_records)
        object.__setattr__(self, "_sector_splits_by_lap", ordered_splits_by_lap)
        object.__setattr__(self, "_sector_end_times_by_lap", sector_end_times_by_lap)
        object.__setattr__(self, "_sector_names_by_lap", sector_names_by_lap)
        object.__setattr__(self, "_sector_split_by_lap_and_name", split_by_lap_and_name)
        object.__setattr__(self, "_best_lap_sector_times", best_lap_sector_times)

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

    @property
    def best_lap_sector_times(self) -> dict[str, float]:
        return dict(self._best_lap_sector_times)

    @property
    def best_lap_index(self) -> int | None:
        if self.lap_result is None or self.lap_result.best_lap is None:
            return None
        return self.lap_result.best_lap.lap_index

    def lap_gap_to_best(self, lap_index: int) -> float | None:
        if self.lap_result is None or self.lap_result.best_lap is None:
            return None
        lap = self._lap_records_by_index.get(lap_index)
        if lap is None:
            return None
        return lap.lap_time_sec - self.lap_result.best_lap.lap_time_sec

    def lap_gap_display(self, lap_index: int) -> GapDisplay:
        if lap_index == self.best_lap_index:
            return GapDisplay(value_sec=0.0, text="BEST", status="best")
        return format_gap_display(self.lap_gap_to_best(lap_index))

    def sector_gap_to_best_lap(self, lap_index: int, segment_name: str) -> float | None:
        reference = self.best_lap_sector_times.get(segment_name)
        if reference is None:
            return None
        split = self._sector_split_by_lap_and_name.get((lap_index, segment_name))
        if split is None:
            return None
        return split.duration_sec - reference

    def sector_gap_display(self, lap_index: int, segment_name: str) -> GapDisplay:
        if lap_index == self.best_lap_index:
            return GapDisplay(value_sec=0.0, text="BEST", status="best")
        return format_gap_display(self.sector_gap_to_best_lap(lap_index, segment_name))

    def realtime_gap_to_best_at(self, data_time_sec: float) -> float | None:
        if self.lap_result is None or self.lap_result.best_lap is None:
            return None
        current_lap_index = self.current_lap_number_at(data_time_sec)
        current_profile = self.lap_distance_profiles.get(current_lap_index)
        best_profile = self.lap_distance_profiles.get(self.lap_result.best_lap.lap_index)
        if current_profile is None or best_profile is None:
            return None
        current_distance = current_profile.distance_at_time(data_time_sec)
        if current_distance is None or current_profile.total_distance_m <= 0.0 or best_profile.total_distance_m <= 0.0:
            return None
        progress = max(0.0, min(current_distance / current_profile.total_distance_m, 1.0))
        best_elapsed = best_profile.elapsed_at_distance(best_profile.total_distance_m * progress)
        if best_elapsed is None:
            return None
        current_elapsed = max(0.0, data_time_sec - current_profile.start_time_sec)
        return current_elapsed - best_elapsed

    def realtime_gap_display_at(self, data_time_sec: float) -> GapDisplay:
        if self.current_lap_number_at(data_time_sec) == self.best_lap_index:
            return GapDisplay(value_sec=0.0, text="BEST", status="best")
        return format_gap_display(self.realtime_gap_to_best_at(data_time_sec))

    def current_lap_distance_at(self, data_time_sec: float) -> float | None:
        profile = self.lap_distance_profiles.get(self.current_lap_number_at(data_time_sec))
        if profile is None:
            return None
        return profile.distance_at_time(data_time_sec)

    def current_lap_length_at(self, data_time_sec: float) -> float | None:
        profile = self.lap_distance_profiles.get(self.current_lap_number_at(data_time_sec))
        if profile is None or profile.total_distance_m <= 0.0:
            return None
        return profile.total_distance_m

    def current_lap_time_at(self, data_time_sec: float) -> float | None:
        if self.lap_result is None:
            return None
        start_time_sec = self._current_lap_start_time_at(data_time_sec)
        return max(0.0, data_time_sec - start_time_sec)

    def current_lap_number_at(self, data_time_sec: float) -> int:
        if self.lap_result is None or not self._crossing_times:
            return 1
        return max(1, bisect_right(self._crossing_times, data_time_sec))

    def current_sector_time_at(self, data_time_sec: float) -> float | None:
        if self.lap_result is None:
            return None
        boundary_time_sec = self._current_lap_start_time_at(data_time_sec)
        lap_index = self.current_lap_number_at(data_time_sec)
        end_times = self._sector_end_times_by_lap.get(lap_index, ())
        end_index = bisect_right(end_times, data_time_sec) - 1
        if end_index >= 0:
            boundary_time_sec = max(boundary_time_sec, end_times[end_index])
        return max(0.0, data_time_sec - boundary_time_sec)

    def current_sector_name_at(self, data_time_sec: float) -> str:
        if not self.segment_names:
            return "--"
        lap_index = self.current_lap_number_at(data_time_sec)
        end_times = self._sector_end_times_by_lap.get(lap_index, ())
        names = self._sector_names_by_lap.get(lap_index, ())
        end_index = bisect_right(end_times, data_time_sec)
        if end_index < len(names):
            return names[end_index]
        splits = self._sector_splits_by_lap.get(lap_index, ())
        if not splits:
            return self.segment_names[0]
        next_index = min(splits[-1].order, len(self.segment_names) - 1)
        return self.segment_names[next_index]

    def _current_lap_start_time_at(self, data_time_sec: float) -> float:
        crossing_index = bisect_right(self._crossing_times, data_time_sec) - 1
        if crossing_index < 0:
            return 0.0
        return self._crossing_times[crossing_index]


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
        segment_names = [f"S{index}" for index in range(1, len(ordered_sectors) + 2)]
        for lap_index, (start_crossing, end_crossing) in enumerate(
            zip(lap_result.crossings, lap_result.crossings[1:]),
            start=1,
        ):
            boundary_time_sec = start_crossing.cross_time_sec
            segment_order = 1
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
                        segment_name=f"S{segment_order}",
                        start_time_sec=boundary_time_sec,
                        end_time_sec=crossing.cross_time_sec,
                        duration_sec=crossing.cross_time_sec - boundary_time_sec,
                        order=segment_order,
                    )
                )
                boundary_time_sec = crossing.cross_time_sec
                segment_order += 1
            if boundary_time_sec < end_crossing.cross_time_sec:
                sector_splits.append(
                    SectorSplitRecord(
                        lap_index=lap_index,
                        segment_name=f"S{segment_order}",
                        start_time_sec=boundary_time_sec,
                        end_time_sec=end_crossing.cross_time_sec,
                        duration_sec=end_crossing.cross_time_sec - boundary_time_sec,
                        order=segment_order,
                    )
                )

        return TrackAnalysisSummary(
            lap_result=lap_result,
            sector_result=sector_result,
            sector_splits=sector_splits,
            segment_names=segment_names,
            lap_distance_profiles=_build_lap_distance_profiles(store, lap_result),
        )


def gap_status(value_sec: float | None, *, epsilon_sec: float = 0.001) -> str:
    if value_sec is None:
        return "unknown"
    if value_sec < -epsilon_sec:
        return "faster"
    if value_sec > epsilon_sec:
        return "slower"
    return "equal"


def format_gap_display(value_sec: float | None) -> GapDisplay:
    status = gap_status(value_sec)
    if value_sec is None:
        return GapDisplay(value_sec=None, text="--", status=status)
    return GapDisplay(value_sec=value_sec, text=f"{value_sec:+.3f}", status=status)


def _build_lap_distance_profiles(store: TelemetryStore, lap_result: LapDetectionResult | None) -> dict[int, LapDistanceProfile]:
    if lap_result is None or not lap_result.laps:
        return {}
    samples = [
        sample
        for sample in store.samples
        if sample.x_m is not None and sample.y_m is not None
    ]
    if len(samples) < 2:
        return {}

    profiles: dict[int, LapDistanceProfile] = {}
    for lap in lap_result.laps:
        points: list[tuple[float, float, float]] = []
        start_xy = _xy_at_time(samples, lap.start_time_sec)
        end_xy = _xy_at_time(samples, lap.end_time_sec)
        if start_xy is None or end_xy is None:
            continue
        points.append((lap.start_time_sec, start_xy[0], start_xy[1]))
        points.extend(
            (sample.elapsed_sec, sample.x_m, sample.y_m)
            for sample in samples
            if lap.start_time_sec < sample.elapsed_sec < lap.end_time_sec
        )
        points.append((lap.end_time_sec, end_xy[0], end_xy[1]))
        if len(points) < 2:
            continue

        distances = [0.0]
        elapsed_offsets = [0.0]
        total = 0.0
        for previous, current in zip(points, points[1:]):
            total += ((current[1] - previous[1]) ** 2 + (current[2] - previous[2]) ** 2) ** 0.5
            distances.append(total)
            elapsed_offsets.append(current[0] - lap.start_time_sec)
        profiles[lap.lap_index] = LapDistanceProfile(
            lap_index=lap.lap_index,
            start_time_sec=lap.start_time_sec,
            end_time_sec=lap.end_time_sec,
            distances_m=tuple(distances),
            elapsed_offsets_sec=tuple(elapsed_offsets),
        )
    return profiles


def _xy_at_time(samples, data_time_sec: float) -> tuple[float, float] | None:
    if data_time_sec <= samples[0].elapsed_sec:
        return samples[0].x_m, samples[0].y_m
    for previous, current in zip(samples, samples[1:]):
        if previous.elapsed_sec <= data_time_sec <= current.elapsed_sec:
            span = current.elapsed_sec - previous.elapsed_sec
            ratio = 0.0 if span == 0 else (data_time_sec - previous.elapsed_sec) / span
            return (
                previous.x_m + (current.x_m - previous.x_m) * ratio,
                previous.y_m + (current.y_m - previous.y_m) * ratio,
            )
    return samples[-1].x_m, samples[-1].y_m


def _interpolate(x_values: tuple[float, ...], y_values: tuple[float, ...], target: float) -> float | None:
    if not x_values or not y_values or len(x_values) != len(y_values):
        return None
    if target <= x_values[0]:
        return y_values[0]
    if target >= x_values[-1]:
        return y_values[-1]
    index = bisect_left(x_values, target)
    left_x = x_values[index - 1]
    right_x = x_values[index]
    left_y = y_values[index - 1]
    right_y = y_values[index]
    span = right_x - left_x
    ratio = 0.0 if span == 0 else (target - left_x) / span
    return left_y + (right_y - left_y) * ratio
