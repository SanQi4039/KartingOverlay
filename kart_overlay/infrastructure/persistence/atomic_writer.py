import json
from pathlib import Path


class AtomicWriter:
    def write_text(self, path: Path, text: str) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(text, encoding="utf-8")
        temp_text = temp_path.read_text(encoding="utf-8")
        json.loads(temp_text)
        temp_path.replace(path)
