import json
from pathlib import Path

from kart_overlay.domain.project import ProjectDocument
from kart_overlay.infrastructure.persistence.atomic_writer import AtomicWriter


class ProjectRepository:
    def __init__(self, writer: AtomicWriter | None = None) -> None:
        self._writer = writer or AtomicWriter()

    def save(self, path: Path, document: ProjectDocument) -> None:
        self._writer.write_text(
            path,
            json.dumps(document.to_dict(), ensure_ascii=False, indent=2),
        )

    def load(self, path: Path) -> ProjectDocument:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ProjectDocument(**payload)
