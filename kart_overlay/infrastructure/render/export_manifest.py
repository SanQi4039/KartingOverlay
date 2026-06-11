import json
from pathlib import Path


class ExportManifestWriter:
    def write(self, *, path: Path, payload: dict) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
