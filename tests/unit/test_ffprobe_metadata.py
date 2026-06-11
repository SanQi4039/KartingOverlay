from kart_overlay.infrastructure.video.ffprobe_service import FfprobeService


def test_ffprobe_service_parses_video_metadata_payload():
    service = FfprobeService()
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
        "format": {
            "filename": "sample.mp4",
            "duration": "123.456",
        },
    }

    metadata = service.parse_metadata(payload)

    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.fps == 60000 / 1001
    assert metadata.duration_sec == 123.456
    assert metadata.rotation_deg == 90
