# Local Background Images And Windows Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Amap-backed track backgrounds with local image backgrounds, then add Windows-installed app data/project path behavior and a `setup.exe` packaging stage.

**Architecture:** Keep telemetry and timing-line geometry canonical while treating the background image as an editor-only layer driven by `TrackDefinition.display_transform`. Remove Amap-specific runtime/config paths, persist `background_image_path` in projects, and add explicit Windows user-data path helpers so the installed build cleanly separates binaries from mutable user files.

**Tech Stack:** Python 3.11, PySide6, pytest, PyInstaller, Inno Setup-oriented packaging helpers, existing `ProjectSession`, `TrackEditor`, `ProjectPanel`

---

### Task 1: Simplify Track Model Persistence

**Files:**
- Modify: `kart_overlay/domain/track/models.py`
- Modify: `kart_overlay/ui/project_panel.py`
- Test: `tests/unit/test_track_definition.py`
- Test: `tests/unit/test_project_workflow_roundtrip.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert `DisplayTransform` no longer exposes `basemap_provider` and that `TrackDefinition` can round-trip a `background_image_path`.

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_definition.py tests/unit/test_project_workflow_roundtrip.py -q`

Expected: FAIL because the old model still requires `basemap_provider` semantics and the project file does not persist a background image path.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. `DisplayTransform` with only `translate_x`, `translate_y`, `rotation_deg`, and `scale`
2. `TrackDefinition.background_image_path`
3. project serialization/deserialization for `background_image_path`

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_definition.py tests/unit/test_project_workflow_roundtrip.py -q`

Expected: PASS

### Task 2: Replace Amap Editor Flow With Local Background Images

**Files:**
- Modify: `kart_overlay/ui/track_editor.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `kart_overlay/ui/texts.py`
- Test: `tests/unit/test_track_editor_advanced.py`
- Test: `tests/unit/test_track_workspace.py`

- [ ] **Step 1: Write the failing tests**

Add tests that cover:

```python
def test_track_editor_loads_background_image_from_track_definition():
    ...

def test_track_editor_clear_background_preserves_timing_lines():
    ...

def test_track_workspace_import_replace_clear_background_updates_status():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_advanced.py tests/unit/test_track_workspace.py -q`

Expected: FAIL because the editor still expects Amap/basemap flows and has no local-background controls.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. direct image-path loading into the track editor
2. background import/replace/clear/reset operations in the workspace
3. background status text and file-name reporting
4. transform persistence on the background layer only

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_advanced.py tests/unit/test_track_workspace.py -q`

Expected: PASS

### Task 3: Add Relative/Absolute Background Path Save Logic

**Files:**
- Modify: `kart_overlay/ui/project_panel.py`
- Test: `tests/unit/test_project_panel.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

```python
def test_project_panel_saves_background_image_relative_to_project_when_possible():
    ...

def test_project_panel_loads_project_when_background_image_is_missing():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_project_panel.py -q`

Expected: FAIL because background paths are not normalized relative to the project path and missing files are not surfaced through the new background workflow.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. relative-path save helper for project-bound background images
2. absolute-path fallback
3. safe load behavior when the saved image is missing

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_project_panel.py -q`

Expected: PASS

### Task 4: Introduce Installed-App Data Paths

**Files:**
- Modify: `kart_overlay/config.py`
- Modify: `kart_overlay/packaging.py`
- Create: `kart_overlay/app_paths.py`
- Modify: `kart_overlay/ui/project_panel.py`
- Test: `tests/unit/test_packaging_runtime.py`
- Test: `tests/unit/test_external_tools_config.py`
- Test: `tests/unit/test_project_panel.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:

```python
def test_app_paths_use_localappdata_and_documents_on_windows():
    ...

def test_project_panel_uses_default_projects_directory_for_dialogs():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_packaging_runtime.py tests/unit/test_external_tools_config.py tests/unit/test_project_panel.py -q`

Expected: FAIL because the runtime still assumes current-working-directory `.env.local` and save/load dialogs do not target the installed-app project directory.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. app-path helpers for install root, `%LOCALAPPDATA%\KartOverlay`, and `%USERPROFILE%\Documents\KartOverlay Projects`
2. lazy directory creation for user-data/project roots
3. dialog default-directory wiring in `ProjectPanel`
4. config loading that no longer depends on shipped Amap secrets

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_packaging_runtime.py tests/unit/test_external_tools_config.py tests/unit/test_project_panel.py -q`

Expected: PASS

### Task 5: Add Installer Packaging Stage

**Files:**
- Modify: `scripts/build_windows_dist.py`
- Create: `packaging/installer.iss`
- Test: `tests/unit/test_build_windows_dist.py`

- [ ] **Step 1: Write the failing tests**

Add tests that cover:

```python
def test_installer_script_path_is_reported_from_build_script():
    ...

def test_build_readme_mentions_setup_installer():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_build_windows_dist.py -q`

Expected: FAIL because the build pipeline only produces the portable bundle/zip and has no installer script metadata.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. Inno Setup script template under `packaging/installer.iss`
2. build-script helpers that locate the installer script and document the new `setup.exe` stage
3. readme/build text updates aligned with installer output

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_build_windows_dist.py -q`

Expected: PASS

### Task 6: Full Regression And Documentation

**Files:**
- Modify: `README.md`
- Test: `tests/unit`

- [ ] **Step 1: Run focused suites before full regression**

Run:

```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_definition.py tests/unit/test_track_editor_advanced.py tests/unit/test_track_workspace.py tests/unit/test_project_panel.py tests/unit/test_build_windows_dist.py tests/unit/test_packaging_runtime.py tests/unit/test_external_tools_config.py -q
```

Expected: PASS

- [ ] **Step 2: Run full unit suite**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit -q`

Expected: PASS

- [ ] **Step 3: Update README incrementally**

Document:

1. local background-image workflow replacing Amap
2. installer/data-directory behavior
3. non-export nature of the editor background layer

- [ ] **Step 4: Verify documentation and tests remain green**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit -q`

Expected: PASS
