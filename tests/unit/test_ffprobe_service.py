import json
import subprocess

import pytest

from kart_overlay.infrastructure.video.ffprobe_service import FfprobeService


def test_ffprobe_service_builds_safe_command():
    service = FfprobeService(binary_path="ffprobe")

    command = service.build_command("sample.mp4")

    assert command[0] == "ffprobe"
    assert "sample.mp4" in command
    assert isinstance(command, list)


def test_ffprobe_service_uses_oriented_canvas_size():
    service = FfprobeService(binary_path="ffprobe")
    payload = {
        "streams": [
            {
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "60000/1001",
                "duration": "123.456",
                "tags": {"rotate": "90"},
            }
        ],
        "format": {"duration": "123.456"},
    }

    metadata = service.parse_metadata(payload)

    assert metadata.canvas_size == (1080, 1920)


def test_ffprobe_service_probe_decodes_utf8_json_output(monkeypatch):
    service = FfprobeService(binary_path="ffprobe")
    payload = {
        "streams": [
            {
                "codec_type": "video",
                "width": 2688,
                "height": 1512,
                "avg_frame_rate": "30000/1001",
                "r_frame_rate": "30000/1001",
                "duration": "12.345",
                "tags": {"handler_name": "锐速赛道车载"},
            }
        ],
        "format": {"duration": "12.345", "tags": {"encoder": "DJI OsmoAction3"}},
    }

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    metadata = service.probe("sample.mp4")

    assert metadata.width == 2688
    assert metadata.height == 1512
    assert metadata.fps == pytest.approx(30000 / 1001)
    assert metadata.duration_sec == pytest.approx(12.345)


def test_ffprobe_service_probe_rejects_empty_output(monkeypatch):
    service = FfprobeService(binary_path="ffprobe")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="empty JSON output"):
        service.probe("sample.mp4")


def test_ffprobe_service_probe_rejects_invalid_json_output(monkeypatch):
    service = FfprobeService(binary_path="ffprobe")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=b"not-json",
            stderr=b"",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="valid JSON"):
        service.probe("sample.mp4")


def test_ffprobe_service_probe_rejects_output_without_video_stream(monkeypatch):
    service = FfprobeService(binary_path="ffprobe")
    payload = {
        "streams": [
            {"codec_type": "audio", "duration": "12.345"},
        ],
        "format": {"duration": "12.345"},
    }

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="No video stream"):
        service.probe("sample.mp4")


def test_ffprobe_service_reads_rotation_from_display_matrix_side_data():
    service = FfprobeService(binary_path="ffprobe")
    payload = {
        "streams": [
            {
                "codec_type": "video",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "60000/1001",
                "duration": "45.000",
                "side_data_list": [
                    {
                        "side_data_type": "Display Matrix",
                        "rotation": -90,
                    }
                ],
            }
        ],
        "format": {"duration": "45.000"},
    }

    metadata = service.parse_metadata(payload)

    assert metadata.rotation_deg == -90
    assert metadata.canvas_size == (1920, 1080)
