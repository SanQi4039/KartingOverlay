from pathlib import Path
import json

from kart_overlay.infrastructure.render.export_manifest import ExportManifestWriter


def test_export_manifest_writer_writes_expected_fields(tmp_path: Path):
    manifest_path = tmp_path / "export_manifest.json"

    ExportManifestWriter().write(
        path=manifest_path,
        payload={
            "project_name": "demo",
            "video_file": "input.mp4",
            "data_file": "input.gpx",
            "overlay_start_video_time_sec": 3.2,
            "data_duration_sec": 12.5,
            "canvas_width": 1920,
            "canvas_height": 1080,
            "fps": 60,
            "export_format": "mov_prores_4444",
            "alpha": True,
        },
    )

    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert loaded["project_name"] == "demo"
    assert loaded["export_format"] == "mov_prores_4444"
    assert loaded["alpha"] is True
