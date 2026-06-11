# Phase 4 Export Pipeline And Sync Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PNG-sequence export with direct raw-frame ffmpeg piping, tighten duration semantics around telemetry timestamps, and remove the remaining sync compatibility layer from shared session and project persistence.

**Architecture:** Keep the UI request surface mostly stable while changing the export contract underneath from `frames_dir -> ffmpeg image sequence` to `frame stream -> ffmpeg stdin`. Remove `sync` from `ProjectSession`, `ProjectDocument`, repository load/save, and project-panel roundtrip so the saved-project schema matches the overlay-first workflow.

**Tech Stack:** Python, PySide6, pytest, ffmpeg subprocess piping

---

### Task 1: Lock export streaming and duration behavior with tests

**Files:**
- Modify: `tests/unit/test_export_service.py`
- Modify: `tests/unit/test_export_execution.py`
- Modify: `tests/unit/test_ffmpeg_exporter.py`

- [ ] Add failing tests proving export no longer writes `frame_*.png`.
- [ ] Add failing tests for endpoint-inclusive frame sampling and exact-duration export expectations.
- [ ] Add failing tests for raw-frame ffmpeg command construction.

### Task 2: Lock sync removal with tests

**Files:**
- Modify: `tests/unit/test_project_workflow_roundtrip.py`
- Modify: `tests/unit/test_project_repository.py`
- Modify: `tests/unit/test_ui_texts.py`

- [ ] Add or adjust tests so saved projects no longer require `sync` in schema or session roundtrip.
- [ ] Remove tests that preserve old sync compatibility behavior.

### Task 3: Implement export contract refactor

**Files:**
- Modify: `kart_overlay/application/export_events.py`
- Modify: `kart_overlay/application/export_service.py`
- Modify: `kart_overlay/application/export_task_runner.py`
- Modify: `kart_overlay/infrastructure/render/ffmpeg_exporter.py`
- Modify: `kart_overlay/infrastructure/render/frame_renderer.py`

- [ ] Replace `frames_dir`-centric request/prepare/execute flow with raw-frame streaming.
- [ ] Keep progress/log/cancel behavior intact while moving encoding to stdin-based ffmpeg execution.
- [ ] Update frame scheduling to cover the full telemetry interval without reintroducing sync overlap logic.

### Task 4: Remove sync residue from session and persistence

**Files:**
- Modify: `kart_overlay/application/project_session.py`
- Modify: `kart_overlay/domain/project.py`
- Modify: `kart_overlay/infrastructure/persistence/project_repository.py`
- Modify: `kart_overlay/ui/project_panel.py`
- Modify: `kart_overlay/ui/texts.py`

- [ ] Remove `SyncModel` / `SyncState` usage from active workflow boundaries.
- [ ] Update project save/load to stop serializing sync state.
- [ ] Keep project roundtrip for telemetry/video/track/widgets/export intact.

### Task 5: Verify and document

**Files:**
- Modify: `README.md`
- Modify: `AI_HANDOFF.md`

- [ ] Run targeted export/persistence regression coverage and compile checks.
- [ ] Add incremental notes describing the raw-frame export path and removed sync compatibility layer.
