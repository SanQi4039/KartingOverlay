from dataclasses import dataclass
import json
from pathlib import Path
import subprocess

from kart_overlay.config import ExternalToolsConfig, binary_path_available


@dataclass(frozen=True)
class VideoMetadata:
    width: int
    height: int
    fps: float
    duration_sec: float
    rotation_deg: int = 0
    is_variable_frame_rate: bool = False

    @property
    def canvas_size(self) -> tuple[int, int]:
        if abs(self.rotation_deg) % 180 == 90:
            return (self.height, self.width)
        return (self.width, self.height)


class FfprobeService:
    def __init__(self, binary_path: str | None = None) -> None:
        self._binary_path = binary_path or ExternalToolsConfig.from_env().ffprobe_path

    @property
    def binary_path(self) -> str:
        return self._binary_path

    def ensure_available(self) -> None:
        if binary_path_available(self._binary_path):
            return
        raise FileNotFoundError(
            "ffprobe not found. Set KART_OVERLAY_FFPROBE_PATH or add ffprobe to PATH."
        )

    def build_command(self, video_path: str) -> list[str]:
        return [
            self._binary_path,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

    def probe(self, video_path: str | Path) -> VideoMetadata:
        self.ensure_available()
        command = self.build_command(str(video_path))
        completed = subprocess.run(
            command,
            shell=False,
            check=True,
            capture_output=True,
        )
        output_text = self._decode_probe_output(completed.stdout)
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError("ffprobe did not return valid JSON output.") from exc
        return self.parse_metadata(payload)

    def parse_metadata(self, payload: dict) -> VideoMetadata:
        video_stream = self._find_video_stream(payload)
        average_fps = self._parse_fraction(video_stream.get("avg_frame_rate", "0/1"))
        nominal_fps = self._parse_fraction(video_stream.get("r_frame_rate", "0/1"))
        duration = self._parse_float(
            video_stream.get("duration") or payload.get("format", {}).get("duration")
        )
        rotation = self._extract_rotation(video_stream)
        return VideoMetadata(
            width=self._parse_int(video_stream.get("width") or video_stream.get("coded_width")),
            height=self._parse_int(video_stream.get("height") or video_stream.get("coded_height")),
            fps=average_fps or nominal_fps,
            duration_sec=duration,
            rotation_deg=rotation,
            is_variable_frame_rate=bool(
                average_fps and nominal_fps and abs(average_fps - nominal_fps) > 0.01
            ),
        )

    @staticmethod
    def _decode_probe_output(raw_output: str | bytes | bytearray | None) -> str:
        if raw_output is None:
            raise ValueError("ffprobe returned empty JSON output.")
        if isinstance(raw_output, str):
            text = raw_output
        else:
            text = bytes(raw_output).decode("utf-8", errors="replace")
        if not text.strip():
            raise ValueError("ffprobe returned empty JSON output.")
        return text

    @staticmethod
    def _find_video_stream(payload: dict) -> dict:
        for stream in payload.get("streams", []):
            if stream.get("codec_type") == "video":
                return stream
        raise ValueError("No video stream found in ffprobe output.")

    @classmethod
    def _extract_rotation(cls, video_stream: dict) -> int:
        tags = video_stream.get("tags", {})
        rotate_value = tags.get("rotate")
        if rotate_value not in (None, ""):
            return int(round(cls._parse_float(rotate_value)))

        for side_data in video_stream.get("side_data_list") or []:
            rotation = side_data.get("rotation")
            if rotation not in (None, ""):
                return int(round(cls._parse_float(rotation)))

        return 0

    @staticmethod
    def _parse_fraction(value: str) -> float:
        if not value or "/" not in value:
            return 0.0
        numerator, denominator = value.split("/", 1)
        denominator_value = FfprobeService._parse_float(denominator)
        if denominator_value == 0:
            return 0.0
        return FfprobeService._parse_float(numerator) / denominator_value

    @staticmethod
    def _parse_float(value: object) -> float:
        if value in (None, "", "N/A"):
            return 0.0
        return float(value)

    @staticmethod
    def _parse_int(value: object) -> int:
        return int(round(FfprobeService._parse_float(value)))
