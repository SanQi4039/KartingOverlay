from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.domain.telemetry.store import TelemetryStore


class TelemetryInterpolator:
    def __init__(self, store: TelemetryStore) -> None:
        self._store = store

    def frame_at(self, data_elapsed_sec: float) -> TelemetryFrame:
        samples = self._store.samples
        if not samples:
            return TelemetryFrame(data_elapsed_sec=data_elapsed_sec, x_m=None, y_m=None, speed_kmh=None)

        if data_elapsed_sec <= samples[0].elapsed_sec:
            sample = samples[0]
            return TelemetryFrame(
                data_elapsed_sec=data_elapsed_sec,
                x_m=sample.x_m,
                y_m=sample.y_m,
                speed_kmh=sample.speed_kmh,
                lap_time_sec=data_elapsed_sec,
                lat=sample.lat,
                lon=sample.lon,
                elevation_m=sample.elevation_m,
                heading_deg=sample.heading_deg,
                accel_long_g=sample.accel_long_g,
                accel_lat_g=sample.accel_lat_g,
            )

        for previous, current in zip(samples, samples[1:]):
            if previous.elapsed_sec <= data_elapsed_sec <= current.elapsed_sec:
                span = current.elapsed_sec - previous.elapsed_sec
                ratio = 0.0 if span == 0 else (data_elapsed_sec - previous.elapsed_sec) / span
                return TelemetryFrame(
                    data_elapsed_sec=data_elapsed_sec,
                    x_m=_lerp(previous.x_m, current.x_m, ratio),
                    y_m=_lerp(previous.y_m, current.y_m, ratio),
                    speed_kmh=_lerp(previous.speed_kmh, current.speed_kmh, ratio),
                    lap_time_sec=data_elapsed_sec,
                    lat=_lerp(previous.lat, current.lat, ratio),
                    lon=_lerp(previous.lon, current.lon, ratio),
                    elevation_m=_lerp(previous.elevation_m, current.elevation_m, ratio),
                    heading_deg=_lerp(previous.heading_deg, current.heading_deg, ratio),
                    accel_long_g=_lerp(previous.accel_long_g, current.accel_long_g, ratio),
                    accel_lat_g=_lerp(previous.accel_lat_g, current.accel_lat_g, ratio),
                )

        sample = samples[-1]
        return TelemetryFrame(
            data_elapsed_sec=data_elapsed_sec,
            x_m=sample.x_m,
            y_m=sample.y_m,
            speed_kmh=sample.speed_kmh,
            lap_time_sec=data_elapsed_sec,
            lat=sample.lat,
            lon=sample.lon,
            elevation_m=sample.elevation_m,
            heading_deg=sample.heading_deg,
            accel_long_g=sample.accel_long_g,
            accel_lat_g=sample.accel_lat_g,
        )


def _lerp(a: float | None, b: float | None, ratio: float) -> float | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return a + (b - a) * ratio
