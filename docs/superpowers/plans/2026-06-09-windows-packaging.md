# Windows Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the Qt desktop app into a Windows one-folder distribution that runs without a preinstalled Python environment and prefers bundled `ffmpeg`/`ffprobe`.

**Architecture:** Keep packaging concerns out of the feature workflows by introducing a small runtime-path helper layer, then build a focused PyInstaller pipeline around it. The app should resolve bundled tools first when frozen, while preserving the current local-development behavior for the source checkout.

**Tech Stack:** Python 3.11, PySide6, PyInstaller, PowerShell build automation, pytest

---

## File Structure

**Create**
- `kart_overlay/packaging.py`
- `packaging/kart_overlay.spec`
- `scripts/build_windows_dist.py`
- `tests/unit/test_packaging_runtime.py`
- `tests/unit/test_build_windows_dist.py`

**Modify**
- `kart_overlay/config.py`
- `requirements.txt`
- `.gitignore`
- `README.md`

**Responsibilities**
- `kart_overlay/packaging.py`
  - expose runtime root detection
  - expose bundled tool directory helpers
  - keep frozen-app path logic isolated from business code
- `kart_overlay/config.py`
  - prefer packaged `ffmpeg`/`ffprobe` before generic cwd probes when frozen
  - keep explicit env overrides and normal PATH lookup behavior intact
- `packaging/kart_overlay.spec`
  - define the one-folder PyInstaller build entrypoint for the desktop app
- `scripts/build_windows_dist.py`
  - validate PyInstaller and tool availability
  - run the build
  - copy bundled `ffmpeg.exe` and `ffprobe.exe` into the dist layout
  - write a lightweight packaged-build readme
- `tests/unit/test_packaging_runtime.py`
  - verify frozen/runtime path calculation and bundled binary candidate generation
- `tests/unit/test_build_windows_dist.py`
  - verify build helper output paths, tool-copy layout, and failure behavior

### Task 1: Add Runtime Packaging Path Helpers

**Files:**
- Create: `kart_overlay/packaging.py`
- Modify: `kart_overlay/config.py`
- Create: `tests/unit/test_packaging_runtime.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
from types import SimpleNamespace

from kart_overlay.config import _default_binary_candidates
from kart_overlay.packaging import bundled_tools_bin_dir, runtime_root


def test_runtime_root_uses_executable_directory_when_frozen(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "kart_overlay.packaging.sys",
        SimpleNamespace(frozen=True, executable=str(tmp_path / "KartOverlay.exe")),
    )

    assert runtime_root() == tmp_path


def test_default_binary_candidates_prefer_bundled_tools_when_frozen(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("kart_overlay.config._runtime_root", lambda: tmp_path)
    monkeypatch.setattr("kart_overlay.config._is_frozen_runtime", lambda: True)
    monkeypatch.setattr("kart_overlay.config.os.name", "nt")
    monkeypatch.delenv("CONDA_PREFIX", raising=False)

    candidates = _default_binary_candidates("ffmpeg")

    assert candidates[0] == tmp_path / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_packaging_runtime.py -v`

Expected: FAIL because `kart_overlay.packaging` and the frozen-runtime helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/packaging.py
from pathlib import Path
import sys


def is_frozen_runtime() -> bool:
    return bool(getattr(sys, "frozen", False))


def runtime_root() -> Path:
    if is_frozen_runtime():
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def bundled_tools_bin_dir() -> Path:
    return runtime_root() / "tools" / "ffmpeg" / "bin"
```

```python
# kart_overlay/config.py
from kart_overlay.packaging import bundled_tools_bin_dir, is_frozen_runtime, runtime_root


def _runtime_root() -> Path:
    return runtime_root()


def _is_frozen_runtime() -> bool:
    return is_frozen_runtime()


def _default_binary_candidates(binary_name: str) -> list[Path]:
    ...
    candidates: list[Path] = []
    if _is_frozen_runtime():
        candidates.append(bundled_tools_bin_dir() / executable_name)
    ...
    workspace_root = _runtime_root()
    candidates.extend(
        [
            workspace_root / "tools" / "ffmpeg" / "bin" / executable_name,
            workspace_root / executable_name,
            ...
        ]
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_packaging_runtime.py -v`

Expected: PASS

### Task 2: Add Build Helpers And Packaging Script

**Files:**
- Create: `scripts/build_windows_dist.py`
- Create: `tests/unit/test_build_windows_dist.py`
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from scripts.build_windows_dist import bundled_tool_targets, validate_tool_paths


def test_bundled_tool_targets_use_tools_ffmpeg_bin_layout(tmp_path: Path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffprobe_path = tmp_path / "ffprobe.exe"

    targets = bundled_tool_targets(dist_dir=tmp_path / "dist", ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)

    assert targets["ffmpeg"] == tmp_path / "dist" / "KartOverlay" / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    assert targets["ffprobe"] == tmp_path / "dist" / "KartOverlay" / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"


def test_validate_tool_paths_requires_existing_binaries(tmp_path: Path):
    try:
        validate_tool_paths(tmp_path / "missing-ffmpeg.exe", tmp_path / "missing-ffprobe.exe")
    except FileNotFoundError as error:
        assert "ffmpeg" in str(error)
    else:
        raise AssertionError("Expected FileNotFoundError")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_build_windows_dist.py -v`

Expected: FAIL because the script module and helper functions do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/build_windows_dist.py
from pathlib import Path
import shutil
import subprocess
import sys

from kart_overlay.config import ExternalToolsConfig


APP_NAME = "KartOverlay"


def bundled_tool_targets(*, dist_dir: Path, ffmpeg_path: Path, ffprobe_path: Path) -> dict[str, Path]:
    bin_dir = dist_dir / APP_NAME / "tools" / "ffmpeg" / "bin"
    return {
        "ffmpeg": bin_dir / ffmpeg_path.name,
        "ffprobe": bin_dir / ffprobe_path.name,
    }


def validate_tool_paths(ffmpeg_path: Path, ffprobe_path: Path) -> None:
    missing = [str(path) for path in (ffmpeg_path, ffprobe_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing packaged tools: {', '.join(missing)}")
```

```python
# requirements.txt
pytest
numpy
pandas
gpxpy
PySide6
pyinstaller
```

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.env.local
tmp_export_frames/
tmp_ui_export/
build/
dist/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_build_windows_dist.py -v`

Expected: PASS

### Task 3: Add PyInstaller Spec And End-To-End Build Flow

**Files:**
- Create: `packaging/kart_overlay.spec`
- Modify: `scripts/build_windows_dist.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from scripts.build_windows_dist import build_readme_text


def test_build_readme_mentions_windows_and_bundled_tools():
    text = build_readme_text()

    assert "Windows" in text
    assert "ffmpeg.exe" in text
    assert "ffprobe.exe" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_build_windows_dist.py::test_build_readme_mentions_windows_and_bundled_tools -v`

Expected: FAIL because the packaged-readme helper does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/build_windows_dist.py
def build_readme_text() -> str:
    return (
        "KartOverlay packaged build for Windows.\n"
        "Run KartOverlay.exe from this folder.\n"
        "Bundled tools: ffmpeg.exe, ffprobe.exe.\n"
    )


def main() -> int:
    tools = ExternalToolsConfig.from_env()
    ffmpeg_path = Path(tools.ffmpeg_path)
    ffprobe_path = Path(tools.ffprobe_path)
    validate_tool_paths(ffmpeg_path, ffprobe_path)

    root = Path(__file__).resolve().parents[1]
    dist_dir = root / "dist"
    build_dir = root / "build" / "pyinstaller"
    spec_path = root / "packaging" / "kart_overlay.spec"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        str(spec_path),
    ]
    subprocess.run(command, check=True, cwd=root)

    targets = bundled_tool_targets(dist_dir=dist_dir, ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)
    for source_name, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ffmpeg_path if source_name == "ffmpeg" else ffprobe_path, target)

    (dist_dir / APP_NAME / "README-Packaged.txt").write_text(build_readme_text(), encoding="utf-8")
    return 0
```

```python
# packaging/kart_overlay.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path.cwd()
hiddenimports = collect_submodules("kart_overlay.widgets")

datas = [
    (str(ROOT / ".env.local.example"), "."),
]

block_cipher = None

a = Analysis(
    [str(ROOT / "kart_overlay" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KartOverlay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="KartOverlay",
)
```

```markdown
## Incremental Update: Windows One-Folder Packaging

The project now includes a first Windows packaging path:

1. PyInstaller one-folder build entrypoint
2. packaged-runtime tool resolution for bundled `ffmpeg.exe` and `ffprobe.exe`
3. build script that stages the executable and copies the required video tools
4. packaged-launch notes for Windows-only distribution
```

- [ ] **Step 4: Run targeted tests and the real packaging command**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_packaging_runtime.py tests\unit\test_build_windows_dist.py -v`

Expected: PASS

Run: `D:\Anaconda_env\karting\python.exe -m scripts.build_windows_dist`

Expected: creates `dist\KartOverlay\KartOverlay.exe` and bundled `tools\ffmpeg\bin\ffmpeg.exe` plus `ffprobe.exe`

### Task 4: Smoke-Check Packaged Build And Full Regression

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run packaged-build smoke checks**

Run: `Test-Path dist\KartOverlay\KartOverlay.exe`

Expected: `True`

Run: `Test-Path dist\KartOverlay\tools\ffmpeg\bin\ffmpeg.exe`

Expected: `True`

Run: `Test-Path dist\KartOverlay\tools\ffmpeg\bin\ffprobe.exe`

Expected: `True`

- [ ] **Step 2: Run full regression**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit -q`

Expected: all tests pass, count at or above the current baseline.

## Self-Review

### Spec coverage

Covered in this plan:

1. one-folder PyInstaller packaging
2. bundled `ffmpeg` and `ffprobe`
3. packaged runtime path preference
4. build automation
5. Windows-only launch notes
6. packaging smoke checks

Out of scope and intentionally deferred:

1. installer creation
2. code signing
3. auto-update flow
4. one-file packaging

### Placeholder scan

Checked for:

1. `TODO`
2. `TBD`
3. vague future-only instructions
4. missing paths

No placeholders remain.

### Type consistency

Planned names remain consistent across tasks:

1. `runtime_root`
2. `bundled_tools_bin_dir`
3. `bundled_tool_targets`
4. `validate_tool_paths`
5. `build_readme_text`
