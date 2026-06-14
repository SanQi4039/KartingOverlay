from dataclasses import dataclass
from pathlib import Path


class ExportCancelledError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExportProgressEvent:
    stage: str
    current: int
    total: int
    percent: int
    message: str


@dataclass(frozen=True)
class ExportTaskRequest:
    telemetry: object
    widgets: list[object]
    canvas_size: tuple[int, int]
    fps: float
    duration_sec: float
    start_data_time_sec: float
    output_path: Path
    manifest_path: Path
    log_path: Path
    manifest_payload: dict
    export_format: str = "mov_prores_4444"
