from bisect import bisect_left
from math import isfinite, radians

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.telemetry.store import TelemetryStore


class TelemetryInterpolator:
    def __init__(self, store: TelemetryStore) -> None:
        self._store = store
        self._elapsed_times = tuple(sample.elapsed_sec for sample in store.samples)
        self._last_sample_index = 0

    def frame_at(self, data_elapsed_sec: float) -> TelemetryFrame:
        samples = self._store.samples
        if not samples:
            return TelemetryFrame(data_elapsed_sec=data_elapsed_sec, x_m=None, y_m=None, speed_kmh=None)

        if data_elapsed_sec <= samples[0].elapsed_sec:
            sample = samples[0]
            accel_long_g, accel_lat_g, accel_source = _frame_acceleration(
                sample=sample,
                previous_sample=None,
            )
            return TelemetryFrame(
                data_elapsed_sec=data_elapsed_sec,
                x_m=sample.x_m,
                y_m=sample.y_m,
                speed_kmh=sample.speed_kmh,
                lap_time_sec=data_elapsed_sec,
                lat=sample.lat,
                lon=sample.lon,
                elevation_m=sample.elevation_m,
                heading_deg=_normalize_heading(sample.heading_deg),
                accel_long_g=accel_long_g,
                accel_lat_g=accel_lat_g,
                accel_source=accel_source,
            )

        if data_elapsed_sec <= samples[-1].elapsed_sec and len(samples) > 1:
            sample_index = self._sample_index_before(data_elapsed_sec)
            previous = samples[sample_index]
            current = samples[sample_index + 1]
            span = current.elapsed_sec - previous.elapsed_sec
            ratio = 0.0 if span == 0 else (data_elapsed_sec - previous.elapsed_sec) / span
            accel_long_g, accel_lat_g, accel_source = _interpolated_acceleration(
                previous=previous,
                current=current,
                ratio=ratio,
            )
            return TelemetryFrame(
                data_elapsed_sec=data_elapsed_sec,
                x_m=_lerp(previous.x_m, current.x_m, ratio),
                y_m=_lerp(previous.y_m, current.y_m, ratio),
                speed_kmh=_lerp(previous.speed_kmh, current.speed_kmh, ratio),
                lap_time_sec=data_elapsed_sec,
                lat=_lerp(previous.lat, current.lat, ratio),
                lon=_lerp(previous.lon, current.lon, ratio),
                elevation_m=_lerp(previous.elevation_m, current.elevation_m, ratio),
                heading_deg=_normalize_heading(_lerp(previous.heading_deg, current.heading_deg, ratio)),
                accel_long_g=accel_long_g,
                accel_lat_g=accel_lat_g,
                accel_source=accel_source,
            )

        sample = samples[-1]
        previous_sample = None if len(samples) < 2 else samples[-2]
        accel_long_g, accel_lat_g, accel_source = _frame_acceleration(
            sample=sample,
            previous_sample=previous_sample,
        )
        return TelemetryFrame(
            data_elapsed_sec=data_elapsed_sec,
            x_m=sample.x_m,
            y_m=sample.y_m,
            speed_kmh=sample.speed_kmh,
            lap_time_sec=data_elapsed_sec,
            lat=sample.lat,
            lon=sample.lon,
            elevation_m=sample.elevation_m,
            heading_deg=_normalize_heading(sample.heading_deg),
            accel_long_g=accel_long_g,
            accel_lat_g=accel_lat_g,
            accel_source=accel_source,
        )

    def _sample_index_before(self, data_elapsed_sec: float) -> int:
        samples = self._store.samples
        last_pair_index = max(0, len(samples) - 2)
        if not samples or last_pair_index == 0:
            self._last_sample_index = 0
            return 0

        cursor = min(self._last_sample_index, last_pair_index)
        cursor_start = samples[cursor].elapsed_sec
        if data_elapsed_sec >= cursor_start:
            while (
                cursor < last_pair_index
                and samples[cursor + 1].elapsed_sec < data_elapsed_sec
            ):
                cursor += 1
            self._last_sample_index = cursor
            return cursor

        position = bisect_left(self._elapsed_times, data_elapsed_sec)
        cursor = min(max(0, position - 1), last_pair_index)
        self._last_sample_index = cursor
        return cursor


def _lerp(a: float | None, b: float | None, ratio: float) -> float | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return a + (b - a) * ratio


def _normalize_heading(value: float | None) -> float | None:
    if value is None or not isfinite(value):
        return None
    return value % 360.0


def _interpolated_acceleration(*, previous, current, ratio: float) -> tuple[float | None, float | None, str | None]:
    measured_long = _lerp(previous.accel_long_g, current.accel_long_g, ratio)
    measured_lat = _lerp(previous.accel_lat_g, current.accel_lat_g, ratio)
    if measured_long is not None or measured_lat is not None:
        return measured_long, measured_lat, "measured"

    estimated_long, estimated_lat = _estimate_acceleration(previous=previous, current=current)
    if estimated_long is None and estimated_lat is None:
        return None, None, None
    return estimated_long, estimated_lat, "estimated"


def _frame_acceleration(*, sample, previous_sample) -> tuple[float | None, float | None, str | None]:
    if sample.accel_long_g is not None or sample.accel_lat_g is not None:
        return sample.accel_long_g, sample.accel_lat_g, "measured"
    if previous_sample is None:
        return None, None, None

    estimated_long, estimated_lat = _estimate_acceleration(previous=previous_sample, current=sample)
    if estimated_long is None and estimated_lat is None:
        return None, None, None
    return estimated_long, estimated_lat, "estimated"


def _estimate_acceleration(*, previous, current) -> tuple[float | None, float | None]:
    delta_t = current.elapsed_sec - previous.elapsed_sec
    if delta_t <= 0:
        return None, None

    previous_speed_ms = None if previous.speed_kmh is None else previous.speed_kmh / 3.6
    current_speed_ms = None if current.speed_kmh is None else current.speed_kmh / 3.6

    long_g = None
    if previous_speed_ms is not None and current_speed_ms is not None:
        long_g = (current_speed_ms - previous_speed_ms) / delta_t / 9.80665

    lat_g = None
    previous_heading = _normalize_heading(previous.heading_deg)
    current_heading = _normalize_heading(current.heading_deg)
    if (
        previous_speed_ms is not None
        and current_speed_ms is not None
        and previous_heading is not None
        and current_heading is not None
    ):
        avg_speed_ms = (previous_speed_ms + current_speed_ms) / 2.0
        delta_heading_deg = _shortest_heading_delta(previous_heading, current_heading)
        yaw_rate = radians(delta_heading_deg) / delta_t
        lat_g = (avg_speed_ms * yaw_rate) / 9.80665

    return long_g, lat_g


def _shortest_heading_delta(previous_heading: float, current_heading: float) -> float:
    return (current_heading - previous_heading + 180.0) % 360.0 - 180.0
