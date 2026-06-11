from pathlib import Path

from kart_overlay.domain.project import ProjectDocument
from kart_overlay.infrastructure.persistence.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self._repository = repository or ProjectRepository()

    def create_project(self, project_name: str) -> ProjectDocument:
        return ProjectDocument.create_empty(project_name)

    def save_project(self, path: Path, document: ProjectDocument) -> None:
        self._repository.save(path, document)

    def load_project(self, path: Path) -> ProjectDocument:
        return self._repository.load(path)
