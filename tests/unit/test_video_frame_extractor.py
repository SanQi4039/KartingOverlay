import subprocess

import pytest
from PySide6.QtGui import QImage

from kart_overlay.infrastructure.video.video_frame_extractor import VideoFrameExtractor


def test_video_frame_extractor_builds_first_frame_command():
    extractor = VideoFrameExtractor(binary_path="ffmpeg")

    command = extractor.build_command("sample.mp4")

    assert command == [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        "0",
        "-i",
        "sample.mp4",
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "pipe:1",
    ]


def test_video_frame_extractor_decodes_png_from_stdout(monkeypatch):
    source = QImage(8, 4, QImage.Format.Format_RGB32)
    source.fill(0xFF336699)
    buffer = source.bits().tobytes()
    assert buffer

    png_bytes = _png_bytes(source)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=png_bytes, stderr=b"")

    monkeypatch.setattr("kart_overlay.infrastructure.video.video_frame_extractor.binary_path_available", lambda path: True)
    monkeypatch.setattr(subprocess, "run", fake_run)

    image = VideoFrameExtractor(binary_path="ffmpeg").extract_first_frame("sample.mp4")

    assert image is not None
    assert image.width() == 8
    assert image.height() == 4
    assert image.pixelColor(0, 0).red() == 0x33


def test_video_frame_extractor_returns_none_for_invalid_image(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=b"not-an-image", stderr=b"")

    monkeypatch.setattr("kart_overlay.infrastructure.video.video_frame_extractor.binary_path_available", lambda path: True)
    monkeypatch.setattr(subprocess, "run", fake_run)

    assert VideoFrameExtractor(binary_path="ffmpeg").extract_first_frame("sample.mp4") is None


def test_video_frame_extractor_raises_when_ffmpeg_missing(monkeypatch):
    monkeypatch.setattr("kart_overlay.infrastructure.video.video_frame_extractor.binary_path_available", lambda path: False)

    with pytest.raises(FileNotFoundError, match="ffmpeg"):
        VideoFrameExtractor(binary_path="missing-ffmpeg").extract_first_frame("sample.mp4")


def _png_bytes(image: QImage) -> bytes:
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    try:
        assert image.save(buffer, "PNG")
    finally:
        buffer.close()
    return bytes(data)
