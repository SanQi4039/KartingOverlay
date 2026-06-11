from pathlib import Path
import xml.etree.ElementTree as ET

from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.parsers.common import (
    finalize_samples,
    parse_iso8601_utc,
    to_timestamp_ms,
)


class GpxParser:
    format_name = "gpx"

    def parse(self, path: str | Path) -> TelemetryStore:
        file_path = Path(path)
        namespaces = {
            "gpx": "http://www.topografix.com/GPX/1/1",
            "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
        }
        root = ET.parse(file_path).getroot()

        samples: list[TelemetrySample] = []
        first_timestamp_ms: float | None = None

        for index, point in enumerate(root.findall(".//gpx:trkpt", namespaces)):
            lat = float(point.attrib["lat"])
            lon = float(point.attrib["lon"])
            elevation_text = point.findtext("gpx:ele", default=None, namespaces=namespaces)
            time_text = point.findtext("gpx:time", default=None, namespaces=namespaces)
            speed_text = point.findtext(".//gpxtpx:speed", default=None, namespaces=namespaces)
            course_text = point.findtext(".//gpxtpx:course", default=None, namespaces=namespaces)

            if time_text is None:
                raise ValueError("GPX point is missing required time field for timing analysis")

            timestamp_ms = to_timestamp_ms(parse_iso8601_utc(time_text))
            if first_timestamp_ms is None:
                first_timestamp_ms = timestamp_ms

            quality: dict[str, str] = {}
            speed_kmh = None
            if speed_text is not None:
                speed_kmh = float(speed_text) * 3.6
                quality["speed"] = "original"

            heading_deg = None
            if course_text is not None:
                heading_deg = float(course_text)
                quality["heading"] = "original"

            samples.append(
                TelemetrySample(
                    sample_index=index,
                    elapsed_sec=(timestamp_ms - first_timestamp_ms) / 1000.0,
                    timestamp_ms=timestamp_ms,
                    lat=lat,
                    lon=lon,
                    elevation_m=float(elevation_text) if elevation_text is not None else None,
                    speed_kmh=speed_kmh,
                    heading_deg=heading_deg,
                    quality=quality,
                )
            )

        samples = finalize_samples(samples)
        return TelemetryStore(
            samples=samples,
            source_format=self.format_name,
            metadata={"source_file": str(file_path)},
        )
