from pathlib import Path

from kart_overlay.infrastructure.render.ffmpeg_exporter import FfmpegExporter


def test_ffmpeg_exporter_builds_rawvideo_prores_4444_command():
    exporter = FfmpegExporter(binary_path="ffmpeg")

    command = exporter.build_mov_prores_command(
        canvas_size=(1920, 1080),
        fps=60.0,
        output_path=Path("overlay.mov"),
    )

    assert command[0] == "ffmpeg"
    assert "-f" in command
    assert "rawvideo" in command
    assert "-pix_fmt" in command
    assert "rgba" in command
    assert "-s" in command
    assert "1920x1080" in command
    assert "-r" in command
    assert "60.0" in command
    assert "-i" in command
    assert "-" in command
    assert "prores_ks" in command
    assert "yuva444p10le" in command
    assert "overlay.mov" in command
