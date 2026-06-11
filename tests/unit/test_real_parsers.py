from pathlib import Path

import pytest

from kart_overlay.infrastructure.parsers.gpx_parser import GpxParser
from kart_overlay.infrastructure.parsers.vbo_parser import VboParser


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_gpx_parser_reads_real_sample_file():
    parser = GpxParser()

    store = parser.parse(FIXTURE_DIR / "test.gpx")

    first = store.samples[0]
    second = store.samples[1]

    assert store.sample_count > 1000
    assert first.lat == pytest.approx(30.263644)
    assert first.lon == pytest.approx(120.3155138)
    assert first.speed_kmh == pytest.approx(46.5084)
    assert first.heading_deg == pytest.approx(33.99)
    assert first.x_m is not None
    assert first.y_m is not None
    assert second.elapsed_sec == pytest.approx(0.44)


def test_vbo_parser_reads_real_sample_file_and_matches_gpx_reference():
    parser = VboParser()

    store = parser.parse(FIXTURE_DIR / "test.vbo")

    first = store.samples[0]
    second = store.samples[1]

    assert store.sample_count > 1000
    assert first.lat == pytest.approx(30.263644)
    assert first.lon == pytest.approx(120.31551383333333)
    assert first.speed_kmh == pytest.approx(46.51)
    assert first.heading_deg == pytest.approx(33.99)
    assert first.x_m is not None
    assert first.y_m is not None
    assert second.elapsed_sec == pytest.approx(0.44)
