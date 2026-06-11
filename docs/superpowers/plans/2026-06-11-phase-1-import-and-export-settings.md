# Phase 1 Import And Export Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make telemetry/video selection import immediately, preserve same-path re-import behavior, add import progress UI, and add export directory/filename state without touching the ffmpeg pipeline yet.

**Architecture:** Keep `ProjectSession` as the shared UI state boundary. Limit this phase to `ProjectPanel`, `ExportWorkspace`, `ProjectSession`, persistence round-trip, and localized texts. Reuse existing import/export service entry points instead of creating alternate code paths.

**Tech Stack:** Python, PySide6, pytest

---

### Task 1: Lock direct import behavior with tests

**Files:**
- Modify: `tests/unit/test_project_panel.py`

- [ ] Add failing tests for telemetry/video browse actions importing immediately.
- [ ] Add a failing test proving the same selected path is still re-imported.

### Task 2: Lock export filename state with tests

**Files:**
- Modify: `tests/unit/test_export_workspace.py`
- Modify: `tests/unit/test_project_workflow_roundtrip.py`

- [ ] Add failing tests for `output_filename` persistence and `.mov` suffix normalization.
- [ ] Add a failing test for directory selection state if a browse action is introduced in this phase.

### Task 3: Implement minimal ProjectPanel changes

**Files:**
- Modify: `kart_overlay/ui/project_panel.py`
- Modify: `kart_overlay/ui/texts.py`

- [ ] Remove the extra import buttons from the workflow UI.
- [ ] Trigger import directly from the browse actions.
- [ ] Add lightweight import progress bars and status transitions without expanding into a new background import system.

### Task 4: Implement minimal export settings changes

**Files:**
- Modify: `kart_overlay/application/project_session.py`
- Modify: `kart_overlay/ui/export_workspace.py`
- Modify: `kart_overlay/ui/texts.py`

- [ ] Add `output_filename` to session export settings.
- [ ] Add output filename input and output directory browse action in the export workspace.
- [ ] Normalize output names to `.mov` and feed the normalized name into the existing export request.

### Task 5: Preserve project round-trip state

**Files:**
- Modify: `tests/unit/test_project_workflow_roundtrip.py`
- Modify: `kart_overlay/ui/project_panel.py`

- [ ] Ensure project save/load still round-trips the extended export settings unchanged.

### Task 6: Verify and document

**Files:**
- Modify: `README.md`
- Modify: `AI_HANDOFF.md`

- [ ] Run targeted pytest coverage for the touched workflow.
- [ ] Add a small incremental note to the handoff/readme describing the new direct-import and export filename behavior.
