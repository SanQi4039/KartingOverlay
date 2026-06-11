from pathlib import Path

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.parsers.gpx_parser import GpxParser
from kart_overlay.infrastructure.parsers.vbo_parser import VboParser


class TelemetryImportService:
    def __init__(self) -> None:
        self._parsers = {
            ".gpx": GpxParser(),
            ".vbo": VboParser(),
        }

    def import_file(self, path: str | Path) -> TelemetryStore:
        file_path = Path(path)
        parser = self._parsers.get(file_path.suffix.lower())
        if parser is None:
            raise ValueError(f"Unsupported telemetry file format: {file_path.suffix}")
        return parser.parse(file_path)
