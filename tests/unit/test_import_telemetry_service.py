from pathlib import Path

from kart_overlay.application.import_telemetry_service import TelemetryImportService


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_import_service_supports_real_gpx_and_vbo_files():
    service = TelemetryImportService()

    gpx_store = service.import_file(FIXTURE_DIR / "test.gpx")
    vbo_store = service.import_file(FIXTURE_DIR / "test.vbo")

    assert gpx_store.source_format == "gpx"
    assert vbo_store.source_format == "vbo"
    assert gpx_store.sample_count > 1000
    assert vbo_store.sample_count > 1000
