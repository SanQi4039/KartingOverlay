from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetryFrame:
    data_elapsed_sec: float
    x_m: float | None
    y_m: float | None
    speed_kmh: float | None
    lap_time_sec: float | None = None
    lat: float | None = None
    lon: float | None = None
    elevation_m: float | None = None
    heading_deg: float | None = None
    accel_long_g: float | None = None
    accel_lat_g: float | None = None
    accel_source: str | None = None
