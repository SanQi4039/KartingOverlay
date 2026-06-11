from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ProjectDocument:
    schema_version: str
    project_name: str
    video: dict = field(default_factory=dict)
    telemetry: dict = field(default_factory=dict)
    track: dict = field(default_factory=dict)
    canvas: dict = field(default_factory=dict)
    widgets: list[dict] = field(default_factory=list)
    export: dict = field(default_factory=dict)
    quality_report: dict = field(default_factory=dict)

    @classmethod
    def create_empty(cls, project_name: str) -> "ProjectDocument":
        return cls(schema_version="1.0", project_name=project_name)

    def to_dict(self) -> dict:
        return asdict(self)
