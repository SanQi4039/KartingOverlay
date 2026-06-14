from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from kart_overlay.infrastructure.render import ffmpeg_exporter as ffmpeg_exporter_module
from kart_overlay.infrastructure.render.ffmpeg_exporter import FfmpegCapabilities, FfmpegExporter


def test_ffmpeg_exporter_builds_rawvideo_prores_4444_command():
    exporter = FfmpegExporter(binary_path="ffmpeg")

    command = exporter.build_mov_prores_command(
        canvas_size=(1920, 1080),
        fps=60.0,
        output_path=Path("overlay.mov"),
        capabilities=FfmpegCapabilities(prores_vulkan_available=False),
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


def test_ffmpeg_exporter_uses_cpu_prores_even_when_vulkan_encoder_is_present():
    exporter = FfmpegExporter(binary_path="ffmpeg")

    command = exporter.build_mov_prores_command(
        canvas_size=(1920, 1080),
        fps=60.0,
        output_path=Path("overlay.mov"),
        capabilities=FfmpegCapabilities(prores_vulkan_available=True),
    )

    assert "prores_ks" in command
    assert "prores_ks_vulkan" not in command
    assert "-init_hw_device" not in command
    assert "-filter_hw_device" not in command
    assert "yuva444p10le" in command


def test_ffmpeg_exporter_builds_small_transparent_qtrle_command():
    exporter = FfmpegExporter(binary_path="ffmpeg")

    command = exporter.build_command(
        export_format="mov_qtrle_alpha",
        canvas_size=(1280, 720),
        fps=50.0,
        output_path=Path("overlay.mov"),
        capabilities=FfmpegCapabilities(),
    )

    assert "qtrle" in command
    assert "argb" in command
    assert command[-1] == "overlay.mov"


def test_ffmpeg_exporter_rejects_vp9_webm_alpha_because_alpha_is_not_reliable():
    exporter = FfmpegExporter(binary_path="ffmpeg")

    with pytest.raises(ValueError):
        exporter.build_command(
            export_format="webm_vp9_alpha",
            canvas_size=(1280, 720),
            fps=50.0,
            output_path=Path("overlay.webm"),
            capabilities=FfmpegCapabilities(),
        )


def test_ffmpeg_exporter_hides_windows_console_and_avoids_stderr_pipe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    exporter = FfmpegExporter(binary_path="ffmpeg")
    popen_kwargs: dict[str, object] = {}

    class _FakeStdin:
        def __init__(self) -> None:
            self.closed = False

        def write(self, data: bytes) -> None:
            return None

        def close(self) -> None:
            self.closed = True

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = _FakeStdin()
            self.stdout = None
            self.stderr = None
            self.returncode = 0

        def poll(self) -> int:
            return 0

        def wait(self, timeout=None) -> int:
            return 0

    def fake_popen(command, **kwargs):
        popen_kwargs.update(kwargs)
        return _FakeProcess()

    monkeypatch.setattr(ffmpeg_exporter_module, "binary_path_available", lambda path: True)
    monkeypatch.setattr(ffmpeg_exporter_module, "os", SimpleNamespace(name="nt"), raising=False)
    monkeypatch.setattr(ffmpeg_exporter_module.subprocess, "Popen", fake_popen)

    log_path = tmp_path / "export.log"
    exporter.run(
        ["ffmpeg", "-version"],
        log_path,
        frame_stream=[b"rgba-frame"],
    )

    assert popen_kwargs["stdout"] == subprocess.DEVNULL
    assert popen_kwargs["stderr"] is not subprocess.PIPE
    assert popen_kwargs["creationflags"] != 0
    assert popen_kwargs["startupinfo"] is not None
    assert "pipe_write_ms" in log_path.read_text(encoding="utf-8")
