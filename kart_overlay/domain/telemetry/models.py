from dataclasses import dataclass, field


@dataclass(frozen=True)
class TelemetrySample:
    sample_index: int
    elapsed_sec: float
    timestamp_ms: float | None = None
    lat: float | None = None
    lon: float | None = None
    elevation_m: float | None = None
    x_m: float | None = None
    y_m: float | None = None
    speed_kmh: float | None = None
    heading_deg: float | None = None
    accel_long_g: float | None = None
    accel_lat_g: float | None = None
    lap_id: int | None = None
    sector_id: int | None = None
    quality: dict[str, str] = field(default_factory=dict)
