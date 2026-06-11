from pathlib import Path

from kart_overlay.domain.project import ProjectDocument
from kart_overlay.infrastructure.persistence.project_repository import ProjectRepository


def test_project_repository_roundtrip(tmp_path: Path):
    repository = ProjectRepository()
    project_path = tmp_path / "sample.kartoverlay"

    document = ProjectDocument.create_empty("Demo Project")

    repository.save(project_path, document)
    loaded = repository.load(project_path)

    assert loaded.project_name == "Demo Project"
    assert loaded.schema_version == "1.0"
    assert "sync" not in loaded.to_dict()
