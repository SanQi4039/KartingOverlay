from pathlib import Path

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.parsers.common import (
    ddmm_to_decimal,
    finalize_samples,
    normalize_racebobo_coordinate,
    parse_iso8601_utc,
    parse_vbo_time_of_day,
    to_timestamp_ms,
)


class VboParser:
    format_name = "vbo"

    def parse(self, path: str | Path) -> TelemetryStore:
        file_path = Path(path)
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()

        column_names: list[str] | None = None
        data_started = False
        base_date = None
        samples: list[TelemetrySample] = []
        first_timestamp_ms: float | None = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("UTC:"):
                base_date = parse_iso8601_utc(stripped.split("UTC:", 1)[1].strip())
                continue

            if stripped == "[column names]":
                column_names = None
                continue

            if column_names is None and "[column names]" not in stripped and not data_started and not stripped.startswith("[") and stripped != "rpm":
                if "sats time lat long velocity heading" in stripped:
                    column_names = stripped.split()
                    continue

            if stripped == "[data]":
                data_started = True
                continue

            if not data_started or column_names is None or stripped.startswith("["):
                continue

            parts = stripped.split()
            if len(parts) != len(column_names):
                continue

            row = dict(zip(column_names, parts))
            timestamp = parse_vbo_time_of_day(row["time"], base_date)
            timestamp_ms = to_timestamp_ms(timestamp)
            if first_timestamp_ms is None:
                first_timestamp_ms = timestamp_ms

            lat = normalize_racebobo_coordinate(ddmm_to_decimal(row["lat"]), "lat")
            lon = normalize_racebobo_coordinate(ddmm_to_decimal(row["long"]), "lon")

            samples.append(
                TelemetrySample(
                    sample_index=len(samples),
                    elapsed_sec=(timestamp_ms - first_timestamp_ms) / 1000.0,
                    timestamp_ms=timestamp_ms,
                    lat=lat,
                    lon=lon,
                    elevation_m=float(row["height"]),
                    speed_kmh=float(row["velocity"]),
                    heading_deg=float(row["heading"]),
                    quality={"speed": "original", "heading": "original"},
                )
            )

        samples = finalize_samples(samples)
        return TelemetryStore(
            samples=samples,
            source_format=self.format_name,
            metadata={"source_file": str(file_path), "columns": column_names or []},
        )
