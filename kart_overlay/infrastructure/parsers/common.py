from dataclasses import replace
from datetime import datetime, timezone
from math import atan2, cos, radians, sin

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.track.projection import project_samples_to_local_xy


def parse_iso8601_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def to_timestamp_ms(value: datetime) -> float:
    return value.timestamp() * 1000.0


def parse_vbo_time_of_day(value: str, base_date: datetime | None) -> datetime:
    hours = int(value[0:2])
    minutes = int(value[2:4])
    seconds = float(value[4:])
    second_int = int(seconds)
    microseconds = int(round((seconds - second_int) * 1_000_000))

    if base_date is None:
        base_date = datetime(1970, 1, 1, tzinfo=timezone.utc)

    return base_date.replace(
        hour=hours,
        minute=minutes,
        second=second_int,
        microsecond=microseconds,
    )


def ddmm_to_decimal(value: str) -> float:
    raw = float(value)
    sign = -1.0 if raw < 0 else 1.0
    magnitude = abs(raw)
    degrees = int(magnitude // 100)
    minutes = magnitude - degrees * 100
    decimal = degrees + minutes / 60.0
    return decimal * sign


def normalize_racebobo_coordinate(decimal_value: float, axis: str) -> float:
    if axis == "lat" and 0.0 <= decimal_value < 20.0:
        return decimal_value + 12.0
    if axis == "lon" and decimal_value < 0.0:
        return abs(decimal_value) + 48.0
    return decimal_value


def derive_missing_motion_fields(samples: list[TelemetrySample]) -> list[TelemetrySample]:
    if len(samples) < 2:
        return samples

    updated: list[TelemetrySample] = []
    for index, sample in enumerate(samples):
        speed_kmh = sample.speed_kmh
        heading_deg = sample.heading_deg
        quality = dict(sample.quality)

        if index > 0:
            previous = samples[index - 1]
            delta_t = sample.elapsed_sec - previous.elapsed_sec
            if delta_t > 0 and sample.x_m is not None and sample.y_m is not None and previous.x_m is not None and previous.y_m is not None:
                delta_x = sample.x_m - previous.x_m
                delta_y = sample.y_m - previous.y_m
                distance_m = (delta_x ** 2 + delta_y ** 2) ** 0.5

                if speed_kmh is None:
                    speed_kmh = (distance_m / delta_t) * 3.6
                    quality["speed"] = "estimated"

                if heading_deg is None and distance_m > 0:
                    heading_rad = atan2(delta_x, delta_y)
                    heading_deg = (heading_rad * 180.0 / 3.141592653589793) % 360.0
                    quality["heading"] = "estimated"

        updated.append(
            replace(
                sample,
                speed_kmh=speed_kmh,
                heading_deg=heading_deg,
                quality=quality,
            )
        )

    return updated


def finalize_samples(samples: list[TelemetrySample]) -> list[TelemetrySample]:
    return derive_missing_motion_fields(project_samples_to_local_xy(samples))
