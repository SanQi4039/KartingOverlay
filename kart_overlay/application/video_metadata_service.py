from pathlib import Path

from kart_overlay.config import ExternalToolsConfig
from kart_overlay.infrastructure.video.ffprobe_service import FfprobeService, VideoMetadata


class VideoMetadataService:
    def __init__(self, ffprobe_service: FfprobeService | None = None) -> None:
        self._ffprobe_service = ffprobe_service or FfprobeService()

    def inspect(self, path: str | Path) -> VideoMetadata:
        return self._ffprobe_service.probe(path)

    def runtime_status(self) -> dict:
        tools = ExternalToolsConfig.from_env()
        return {
            "ffmpeg_available": tools.ffmpeg_available,
            "ffmpeg_path": tools.ffmpeg_path,
            "ffprobe_available": tools.ffprobe_available,
            "ffprobe_path": tools.ffprobe_path,
        }
