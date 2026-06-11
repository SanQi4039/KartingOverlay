# Architecture Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production-grade architecture foundation for the kart overlay desktop app, including repository setup, dependency baseline, runnable package scaffold, project persistence, telemetry core models, and infrastructure contracts that support the approved Scheme C design.

**Architecture:** Use a layered Python package rooted at `kart_overlay`, with `ui`, `application`, `domain`, `infrastructure`, and `widgets` kept separate from the beginning. The first execution phase focuses on testable contracts and a minimal runnable shell instead of prematurely implementing every product feature.

**Tech Stack:** Python from `D:\Anaconda_env\karting`, PySide6 or PyQt5 fallback, pytest, numpy, pandas, gpxpy, FFmpeg/FFprobe adapters

---

### Task 1: Establish Environment Baseline And Dependency Manifest

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `tests/unit/test_dependency_manifest.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_dependency_manifest_lists_core_packages():
    text = Path("requirements.txt").read_text(encoding="utf-8")

    assert "pytest" in text
    assert "numpy" in text
    assert "pandas" in text
    assert "gpxpy" in text
    assert "PySide6" in text or "PyQt5" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_dependency_manifest.py -v`
Expected: FAIL because `requirements.txt` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```text
pytest
numpy
pandas
gpxpy
PySide6
```

```markdown
# Kart Overlay

Native Qt desktop application for building transparent telemetry overlay videos from GPX/VBO and source video files.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_dependency_manifest.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt README.md tests/unit/test_dependency_manifest.py
git commit -m "chore: add dependency manifest baseline"
```

### Task 2: Create The Root Package And Runnable App Bootstrap

**Files:**
- Create: `kart_overlay/__init__.py`
- Create: `kart_overlay/app.py`
- Create: `kart_overlay/main.py`
- Create: `tests/unit/test_app_bootstrap.py`

- [ ] **Step 1: Write the failing test**

```python
from kart_overlay.app import AppBootstrap


def test_app_bootstrap_exposes_application_metadata():
    bootstrap = AppBootstrap.build()

    assert bootstrap.app_name == "Kart Overlay"
    assert bootstrap.main_window_title == "Kart Overlay"
    assert bootstrap.qt_api in {"PySide6", "PyQt5"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_app_bootstrap.py -v`
Expected: FAIL because package modules do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class AppBootstrap:
    app_name: str
    main_window_title: str
    qt_api: str

    @classmethod
    def build(cls) -> "AppBootstrap":
        try:
            import PySide6  # noqa: F401
            qt_api = "PySide6"
        except ImportError:
            import PyQt5  # noqa: F401
            qt_api = "PyQt5"
        return cls(
            app_name="Kart Overlay",
            main_window_title="Kart Overlay",
            qt_api=qt_api,
        )
```

```python
from .app import AppBootstrap


def main() -> int:
    AppBootstrap.build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_app_bootstrap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/__init__.py kart_overlay/app.py kart_overlay/main.py tests/unit/test_app_bootstrap.py
git commit -m "feat: add runnable package bootstrap"
```

### Task 3: Add Project Models And Persistence Roundtrip

**Files:**
- Create: `kart_overlay/application/__init__.py`
- Create: `kart_overlay/application/project_service.py`
- Create: `kart_overlay/domain/project.py`
- Create: `kart_overlay/infrastructure/persistence/__init__.py`
- Create: `kart_overlay/infrastructure/persistence/atomic_writer.py`
- Create: `kart_overlay/infrastructure/persistence/project_repository.py`
- Create: `tests/unit/test_project_repository.py`

- [ ] **Step 1: Write the failing test**

```python
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
    assert loaded.sync.sync_offset_sec == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_project_repository.py -v`
Expected: FAIL because project model and repository classes do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class SyncState:
    sync_offset_sec: float = 0.0


@dataclass(frozen=True)
class ProjectDocument:
    schema_version: str
    project_name: str
    video: dict = field(default_factory=dict)
    telemetry: dict = field(default_factory=dict)
    track: dict = field(default_factory=dict)
    sync: SyncState = field(default_factory=SyncState)
    canvas: dict = field(default_factory=dict)
    widgets: list[dict] = field(default_factory=list)
    export: dict = field(default_factory=dict)
    quality_report: dict = field(default_factory=dict)

    @classmethod
    def create_empty(cls, project_name: str) -> "ProjectDocument":
        return cls(schema_version="1.0", project_name=project_name)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["sync"] = asdict(self.sync)
        return payload
```

```python
import json
from pathlib import Path


class AtomicWriter:
    def write_text(self, path: Path, text: str) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(text, encoding="utf-8")
        temp_text = temp_path.read_text(encoding="utf-8")
        json.loads(temp_text)
        temp_path.replace(path)
```

```python
import json
from pathlib import Path

from kart_overlay.domain.project import ProjectDocument, SyncState
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
        payload["sync"] = SyncState(**payload.get("sync", {}))
        return ProjectDocument(**payload)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_project_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/application/__init__.py kart_overlay/application/project_service.py kart_overlay/domain/project.py kart_overlay/infrastructure/persistence/__init__.py kart_overlay/infrastructure/persistence/atomic_writer.py kart_overlay/infrastructure/persistence/project_repository.py tests/unit/test_project_repository.py
git commit -m "feat: add project persistence foundation"
```

### Task 4: Add Telemetry Domain Contracts And Interpolation Boundary

**Files:**
- Create: `kart_overlay/domain/telemetry/__init__.py`
- Create: `kart_overlay/domain/telemetry/models.py`
- Create: `kart_overlay/domain/telemetry/store.py`
- Create: `kart_overlay/domain/telemetry/frame_provider.py`
- Create: `tests/unit/test_telemetry_store.py`

- [ ] **Step 1: Write the failing test**

```python
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore


def test_telemetry_store_exposes_duration_and_sample_count():
    samples = [
        TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0),
        TelemetrySample(sample_index=1, elapsed_sec=1.5, x_m=10.0, y_m=5.0),
    ]

    store = TelemetryStore(samples=samples)

    assert store.sample_count == 2
    assert store.duration_sec == 1.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_telemetry_store.py -v`
Expected: FAIL because telemetry domain modules do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TelemetrySample:
    sample_index: int
    elapsed_sec: float
    x_m: float | None = None
    y_m: float | None = None
    speed_kmh: float | None = None
    heading_deg: float | None = None
    accel_long_g: float | None = None
    accel_lat_g: float | None = None
    lap_id: int | None = None
    sector_id: int | None = None
    quality: dict[str, str] = field(default_factory=dict)
```

```python
from dataclasses import dataclass

from kart_overlay.domain.telemetry.models import TelemetrySample


@dataclass(frozen=True)
class TelemetryStore:
    samples: list[TelemetrySample]

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def duration_sec(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].elapsed_sec - self.samples[0].elapsed_sec
```

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetryFrame:
    data_elapsed_sec: float
    x_m: float | None
    y_m: float | None
    speed_kmh: float | None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_telemetry_store.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/domain/telemetry/__init__.py kart_overlay/domain/telemetry/models.py kart_overlay/domain/telemetry/store.py kart_overlay/domain/telemetry/frame_provider.py tests/unit/test_telemetry_store.py
git commit -m "feat: add telemetry domain contracts"
```

### Task 5: Add Infrastructure Contract Stubs For Video Probe And Telemetry Parsers

**Files:**
- Create: `kart_overlay/infrastructure/video/__init__.py`
- Create: `kart_overlay/infrastructure/video/ffprobe_service.py`
- Create: `kart_overlay/infrastructure/parsers/__init__.py`
- Create: `kart_overlay/infrastructure/parsers/gpx_parser.py`
- Create: `kart_overlay/infrastructure/parsers/vbo_parser.py`
- Create: `tests/unit/test_ffprobe_service.py`

- [ ] **Step 1: Write the failing test**

```python
from kart_overlay.infrastructure.video.ffprobe_service import FfprobeService


def test_ffprobe_service_builds_safe_command():
    service = FfprobeService(binary_path="ffprobe")

    command = service.build_command("sample.mp4")

    assert command[0] == "ffprobe"
    assert "sample.mp4" in command
    assert isinstance(command, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_ffprobe_service.py -v`
Expected: FAIL because ffprobe service does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class FfprobeService:
    def __init__(self, binary_path: str = "ffprobe") -> None:
        self._binary_path = binary_path

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
```

```python
class GpxParser:
    format_name = "gpx"
```

```python
class VboParser:
    format_name = "vbo"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_ffprobe_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/infrastructure/video/__init__.py kart_overlay/infrastructure/video/ffprobe_service.py kart_overlay/infrastructure/parsers/__init__.py kart_overlay/infrastructure/parsers/gpx_parser.py kart_overlay/infrastructure/parsers/vbo_parser.py tests/unit/test_ffprobe_service.py
git commit -m "feat: add infrastructure adapter contracts"
```
