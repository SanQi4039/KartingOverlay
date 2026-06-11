from pathlib import Path

from kart_overlay.config import ExternalToolsConfig


def test_external_tools_config_prefers_explicit_env_paths(monkeypatch, tmp_path: Path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffprobe_path = tmp_path / "ffprobe.exe"
    ffmpeg_path.write_text("", encoding="utf-8")
    ffprobe_path.write_text("", encoding="utf-8")

    monkeypatch.setenv("KART_OVERLAY_FFMPEG_PATH", str(ffmpeg_path))
    monkeypatch.setenv("KART_OVERLAY_FFPROBE_PATH", str(ffprobe_path))

    config = ExternalToolsConfig.from_env()

    assert config.ffmpeg_path == str(ffmpeg_path)
    assert config.ffprobe_path == str(ffprobe_path)
    assert config.ffmpeg_available is True
    assert config.ffprobe_available is True


def test_external_tools_config_reports_missing_binaries(monkeypatch):
    monkeypatch.delenv("KART_OVERLAY_FFMPEG_PATH", raising=False)
    monkeypatch.delenv("KART_OVERLAY_FFPROBE_PATH", raising=False)
    monkeypatch.setattr("kart_overlay.config.shutil.which", lambda _: None)
    monkeypatch.setattr("kart_overlay.config._default_binary_candidates", lambda _: [])

    config = ExternalToolsConfig.from_env()

    assert config.ffmpeg_path == "ffmpeg"
    assert config.ffprobe_path == "ffprobe"
    assert config.ffmpeg_available is False
    assert config.ffprobe_available is False
