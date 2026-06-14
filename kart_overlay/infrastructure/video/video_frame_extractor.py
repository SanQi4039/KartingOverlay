from pathlib import Path
import subprocess

from PySide6.QtGui import QImage

from kart_overlay.config import ExternalToolsConfig, binary_path_available
from kart_overlay.infrastructure.video.ffprobe_service import _hidden_subprocess_kwargs


class VideoFrameExtractor:
    def __init__(self, binary_path: str | None = None) -> None:
        self._binary_path = binary_path or ExternalToolsConfig.from_env().ffmpeg_path

    def ensure_available(self) -> None:
        if binary_path_available(self._binary_path):
            return
        raise FileNotFoundError(
            "ffmpeg not found. Set KART_OVERLAY_FFMPEG_PATH or add ffmpeg to PATH."
        )

    def build_command(self, video_path: str | Path) -> list[str]:
        return [
            self._binary_path,
            "-v",
            "error",
            "-ss",
            "0",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "pipe:1",
        ]

    def extract_first_frame(self, video_path: str | Path) -> QImage | None:
        self.ensure_available()
        completed = subprocess.run(
            self.build_command(video_path),
            shell=False,
            check=True,
            capture_output=True,
            **_hidden_subprocess_kwargs(),
        )
        image = QImage()
        if not image.loadFromData(completed.stdout, "PNG"):
            return None
        return image
