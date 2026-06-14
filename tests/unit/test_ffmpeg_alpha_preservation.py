from pathlib import Path
import subprocess

import pytest

from kart_overlay.config import ExternalToolsConfig
from kart_overlay.infrastructure.render.ffmpeg_exporter import FfmpegExporter


def test_supported_transparent_video_formats_preserve_alpha(tmp_path: Path):
    tools = ExternalToolsConfig.from_env()
    if not tools.ffmpeg_available:
        pytest.skip("ffmpeg is not available")

    raw_rgba = bytes(
        [
            255,
            0,
            0,
            255,
            0,
            255,
            0,
            0,
            0,
            0,
            255,
            128,
            0,
            0,
            0,
            0,
        ]
    )
    exporter = FfmpegExporter(binary_path=tools.ffmpeg_path)

    for export_format in ("mov_prores_4444", "mov_qtrle_alpha"):
        output_path = tmp_path / f"{export_format}.mov"
        decoded_path = tmp_path / f"{export_format}.rgba"
        command = exporter.build_command(
            export_format=export_format,
            canvas_size=(2, 2),
            fps=1.0,
            output_path=output_path,
        )
        subprocess.run(command, input=raw_rgba, check=True)
        subprocess.run(
            [
                tools.ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(output_path),
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgba",
                str(decoded_path),
            ],
            check=True,
        )

        decoded = decoded_path.read_bytes()
        alphas = decoded[3::4]
        assert min(alphas) == 0
        assert max(alphas) == 255
