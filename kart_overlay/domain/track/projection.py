from dataclasses import replace
from math import cos, radians

from kart_overlay.domain.telemetry.models import TelemetrySample


EARTH_RADIUS_M = 6_371_000.0


def project_samples_to_local_xy(samples: list[TelemetrySample]) -> list[TelemetrySample]:
    geo_samples = [sample for sample in samples if sample.lat is not None and sample.lon is not None]
    if not geo_samples:
        return samples

    origin_lat = sum(sample.lat for sample in geo_samples if sample.lat is not None) / len(geo_samples)
    origin_lon = sum(sample.lon for sample in geo_samples if sample.lon is not None) / len(geo_samples)
    origin_lat_rad = radians(origin_lat)

    projected: list[TelemetrySample] = []
    for sample in samples:
        if sample.lat is None or sample.lon is None:
            projected.append(sample)
            continue

        x_m = radians(sample.lon - origin_lon) * EARTH_RADIUS_M * cos(origin_lat_rad)
        y_m = radians(sample.lat - origin_lat) * EARTH_RADIUS_M
        projected.append(replace(sample, x_m=x_m, y_m=y_m))

    return projected
