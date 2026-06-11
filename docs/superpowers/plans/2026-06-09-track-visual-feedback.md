# Track Visual Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an easy-to-use visual timing-line editor with selectable line objects, endpoint handles, deletion/reset actions, and immediate timing recalculation feedback for karting users.

**Architecture:** Keep timing math in the existing domain/application layers and move only interaction feedback into explicit Qt scene items. `TrackEditor` remains the orchestrator that rebuilds `TrackDefinition`, triggers recalculation, and republishes shared `TrackAnalysisSummary`, while new scene-item classes handle selection, hover, labels, and drag feedback.

**Tech Stack:** Python 3.11, PySide6 `QGraphicsScene`/`QGraphicsItem`, existing `TrackAnalysisBuilder`, pytest

---

## Incremental Update 2026-06-09

Implemented in the current codebase beyond the original Phase 1 baseline:

1. sync selection now surfaces lap-aware sample feedback so chosen telemetry points can be identified as the Nth lap
2. canvas editing now supports per-widget width and height adjustments in shared session state
3. canvas preview performance is improved through cached overlay rendering and cached ffmpeg frame extraction
4. track basemap rendering now caches downloaded static-map imagery between rerenders
5. track workspace layout is now closer to a compact workbench with a left control rail, right primary editor, and explicit basemap status feedback

These updates should be treated as part of the ongoing usability pass before the next round of visual polish.

## File Structure

**Create**
- `kart_overlay/ui/track_scene_items.py`
- `tests/unit/test_track_editor_visual_feedback.py`

**Modify**
- `kart_overlay/ui/track_editor.py`
- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/ui/track_inspector_panel.py`
- `kart_overlay/application/project_session.py`
- `tests/unit/test_track_workspace.py`
- `tests/unit/test_track_editor_advanced.py`
- `tests/unit/test_track_editor_interactions.py`
- `tests/unit/test_track_inspector_panel.py`
- `README.md`

**Responsibilities**
- `kart_overlay/ui/track_scene_items.py`
  - own editable line presentation
  - own endpoint handle presentation
  - emit geometry and selection callbacks back to `TrackEditor`
- `kart_overlay/ui/track_editor.py`
  - build/remove scene items from `TrackDefinition`
  - track current mode and selected object
  - commit endpoint edits back into domain models
  - clear stale analysis and recalculate on completed edits
- `kart_overlay/ui/track_workspace.py`
  - add status-strip text and delete/reset buttons
  - bridge editor feedback into session and inspector
- `kart_overlay/ui/track_inspector_panel.py`
  - continue surfacing lap/sector summaries with last/best timing values
- `tests/unit/test_track_editor_visual_feedback.py`
  - verify selection, handle visibility, status messages, and delete/reset flows

## Scope Note

This plan intentionally covers **Phase 1 only** from the approved spec:

1. track visual editing feedback
2. shared recalculation refresh
3. non-modal status feedback

The Windows packaging phase should be executed as a separate follow-on plan after this phase is green and reviewed, because packaging is operationally independent from scene editing and should not be debugged in the same implementation batch.

### Task 1: Add Editable Scene Item Foundation

**Files:**
- Create: `kart_overlay/ui/track_scene_items.py`
- Create: `tests/unit/test_track_editor_visual_feedback.py`
- Modify: `kart_overlay/ui/track_editor.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from PySide6.QtWidgets import QApplication

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.ui.track_editor import TrackEditor


FIXTURE_DIR = Path(__file__).resolve().parents[2]


def test_track_editor_selects_timing_line_and_exposes_visual_state():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    line_item = editor.editable_items()[0]
    line_item.select_line()

    assert editor.selected_line_key == "start_finish"
    assert line_item.is_selected_visual is True
    assert line_item.handle_count == 2
    assert editor.status_message.startswith("Selected: Start/Finish")
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py::test_track_editor_selects_timing_line_and_exposes_visual_state -v`

Expected: FAIL with an attribute or import error because `track_scene_items.py`, `editable_items()`, `selected_line_key`, `status_message`, and item-level selection helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/track_scene_items.py
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsSimpleTextItem


class LineHandleItem(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, *, accent: QColor) -> None:
        super().__init__(-6.0, -6.0, 12.0, 12.0)
        self.setPos(x, y)
        self.setBrush(QBrush(accent))
        self.setPen(QPen(Qt.GlobalColor.white, 1.2))
        self.setVisible(False)


class EditableTimingLineItem(QGraphicsLineItem):
    def __init__(self, *, line_key: str, label: str, x1: float, y1: float, x2: float, y2: float, color: QColor, on_selected) -> None:
        super().__init__(x1, y1, x2, y2)
        self.line_key = line_key
        self.label = label
        self.is_selected_visual = False
        self._on_selected = on_selected
        self._base_pen = QPen(color, 2.5, Qt.PenStyle.DashLine)
        self._selected_pen = QPen(QColor("#ffffff"), 4.0, Qt.PenStyle.SolidLine)
        self.setPen(self._base_pen)
        self.label_item = QGraphicsSimpleTextItem(label, self)
        self.label_item.setBrush(QColor("#f8f9fa"))
        self.start_handle = LineHandleItem(x1, y1, accent=QColor("#4cc9f0"))
        self.end_handle = LineHandleItem(x2, y2, accent=QColor("#4cc9f0"))

    @property
    def handle_count(self) -> int:
        return 2

    def attach_handles(self, scene) -> None:
        scene.addItem(self.start_handle)
        scene.addItem(self.end_handle)

    def select_line(self) -> None:
        self.is_selected_visual = True
        self.setPen(self._selected_pen)
        self.start_handle.setVisible(True)
        self.end_handle.setVisible(True)
        self._on_selected(self.line_key, self.label)
```

```python
# kart_overlay/ui/track_editor.py
class TrackEditor(QGraphicsView):
    def __init__(self, ...):
        ...
        self._editable_items = []
        self._selected_line_key = None
        self._status_message = "Mode: view"

    @property
    def selected_line_key(self):
        return self._selected_line_key

    @property
    def status_message(self):
        return self._status_message

    def editable_items(self):
        return list(self._editable_items)

    def _handle_line_item_selected(self, line_key: str, label: str) -> None:
        self._selected_line_key = line_key
        self._status_message = f"Selected: {label}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py::test_track_editor_selects_timing_line_and_exposes_visual_state -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/track_scene_items.py kart_overlay/ui/track_editor.py tests/unit/test_track_editor_visual_feedback.py
git commit -m "feat: add editable timing line scene items"
```

### Task 2: Integrate Hover, Drag Handles, And Status Feedback

**Files:**
- Modify: `kart_overlay/ui/track_scene_items.py`
- Modify: `kart_overlay/ui/track_editor.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `tests/unit/test_track_editor_visual_feedback.py`
- Modify: `tests/unit/test_track_editor_advanced.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_track_editor_dragging_endpoint_updates_geometry_and_status():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))

    line_item = editor.editable_items()[0]
    line_item.select_line()
    editor.drag_selected_endpoint("start", (2.0, -3.0))
    editor.finish_endpoint_drag()

    assert editor.track_definition.start_finish.start.x == 2.0
    assert editor.track_definition.start_finish.start.y == -3.0
    assert editor.status_message.startswith("Recalculated:")
    app.quit()
```

```python
def test_track_workspace_shows_mode_and_selection_feedback():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()
    workspace.start_finish_button.click()

    assert workspace.editor_status_label.text() == "Mode: start_finish"
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py::test_track_editor_dragging_endpoint_updates_geometry_and_status tests\unit\test_track_workspace.py::test_track_workspace_shows_mode_and_selection_feedback -v`

Expected: FAIL because endpoint drag helpers and workspace status UI do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/track_scene_items.py
class EditableTimingLineItem(QGraphicsLineItem):
    ...
    def preview_endpoint(self, endpoint: str, x: float, y: float) -> None:
        line = self.line()
        if endpoint == "start":
            self.setLine(x, y, line.x2(), line.y2())
            self.start_handle.setPos(x, y)
        else:
            self.setLine(line.x1(), line.y1(), x, y)
            self.end_handle.setPos(x, y)

    def set_hover_visual(self, hovered: bool) -> None:
        if self.is_selected_visual:
            return
        self.setPen(QPen(self.pen().color(), 3.0 if hovered else 2.5, Qt.PenStyle.DashLine))
        self.start_handle.setVisible(hovered)
        self.end_handle.setVisible(hovered)
```

```python
# kart_overlay/ui/track_editor.py
class TrackEditor(QGraphicsView):
    def __init__(self, ...):
        ...
        self._pending_endpoint_drag = None

    def drag_selected_endpoint(self, endpoint: str, point: tuple[float, float]) -> None:
        item = self._selected_item()
        if item is None:
            return
        self._pending_endpoint_drag = (item.line_key, endpoint, point)
        item.preview_endpoint(endpoint, point[0], -point[1])
        self._status_message = "Releasing will recalculate timing"

    def finish_endpoint_drag(self) -> None:
        if self._pending_endpoint_drag is None:
            return
        line_key, endpoint, point = self._pending_endpoint_drag
        self._pending_endpoint_drag = None
        self.move_line_endpoint(line_key, endpoint, point)
        summary = self._analysis_state.summary if self._analysis_state is not None else None
        best_text = "--" if summary is None or summary.best_lap_time_sec is None else f"{summary.best_lap_time_sec:.3f} s"
        self._status_message = f"Recalculated: Best {best_text}"
```

```python
# kart_overlay/ui/track_workspace.py
self.editor_status_label = QLabel("Mode: view")
...
self.view_button.clicked.connect(lambda: self._set_mode("view"))
self.start_finish_button.clicked.connect(lambda: self._set_mode("start_finish"))
self.sector_button.clicked.connect(lambda: self._set_mode("sector"))
...
def _set_mode(self, mode: str) -> None:
    self.editor.set_edit_mode(mode)
    self.editor_status_label.setText(f"Mode: {mode}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py::test_track_editor_dragging_endpoint_updates_geometry_and_status tests\unit\test_track_workspace.py::test_track_workspace_shows_mode_and_selection_feedback -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/track_scene_items.py kart_overlay/ui/track_editor.py kart_overlay/ui/track_workspace.py tests/unit/test_track_editor_visual_feedback.py tests/unit/test_track_workspace.py
git commit -m "feat: add endpoint drag feedback for timing lines"
```

### Task 3: Add Delete/Reset Actions And Recalculation Clearing

**Files:**
- Modify: `kart_overlay/ui/track_editor.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `kart_overlay/application/project_session.py`
- Modify: `tests/unit/test_track_editor_visual_feedback.py`
- Modify: `tests/unit/test_track_workspace.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_track_editor_can_delete_selected_sector_and_clear_stale_analysis():
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_edit_mode("start_finish")
    editor.commit_line_from_points((0.0, -5.0), (0.0, 5.0))
    editor.set_edit_mode("sector")
    editor.commit_line_from_points((10.0, -5.0), (10.0, 5.0))

    sector_item = editor.editable_items()[1]
    sector_item.select_line()
    editor.delete_selected_line()

    assert editor.track_definition is not None
    assert editor.track_definition.sectors == []
    assert editor.analysis_state is not None
    assert editor.analysis_state.summary is not None
    assert editor.status_message.startswith("Recalculated:")
    app.quit()
```

```python
def test_track_workspace_reset_start_finish_clears_shared_analysis():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    workspace.reset_start_finish_button.click()

    assert session.track_definition is None
    assert session.track_analysis is None
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py::test_track_editor_can_delete_selected_sector_and_clear_stale_analysis tests\unit\test_track_workspace.py::test_track_workspace_reset_start_finish_clears_shared_analysis -v`

Expected: FAIL because delete/reset actions do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/track_editor.py
def delete_selected_line(self) -> None:
    if self._track_definition is None or self._selected_line_key is None:
        self._status_message = "No sector selected"
        return
    if not self._selected_line_key.startswith("sector:"):
        self._status_message = "Only sector lines can be deleted"
        return
    sector_name = self._selected_line_key.split(":", 1)[1]
    sectors = [sector for sector in self._track_definition.sectors if sector.name != sector_name]
    self._track_definition = TrackDefinition(
        start_finish=self._track_definition.start_finish,
        sectors=sectors,
        display_transform=self._track_definition.display_transform,
    )
    self._selected_line_key = None
    self._refresh_analysis()
    self._render()

def reset_start_finish(self) -> None:
    self._track_definition = None
    self._selected_line_key = None
    self._refresh_analysis()
    self._render()
    self._status_message = "Start/Finish reset"
```

```python
# kart_overlay/ui/track_workspace.py
self.delete_selected_button = QPushButton("Delete Selected")
self.reset_start_finish_button = QPushButton("Reset Start/Finish")
self.delete_selected_button.clicked.connect(self._delete_selected_line)
self.reset_start_finish_button.clicked.connect(self._reset_start_finish)

def _delete_selected_line(self) -> None:
    self.editor.delete_selected_line()
    self._sync_analysis_panel()
    self.editor_status_label.setText(self.editor.status_message)

def _reset_start_finish(self) -> None:
    self.editor.reset_start_finish()
    self._sync_analysis_panel()
    self.editor_status_label.setText(self.editor.status_message)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py::test_track_editor_can_delete_selected_sector_and_clear_stale_analysis tests\unit\test_track_workspace.py::test_track_workspace_reset_start_finish_clears_shared_analysis -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/track_editor.py kart_overlay/ui/track_workspace.py kart_overlay/application/project_session.py tests/unit/test_track_editor_visual_feedback.py tests/unit/test_track_workspace.py
git commit -m "feat: add delete and reset actions for timing lines"
```

### Task 4: Expand Inspector Messaging And Full Regression

**Files:**
- Modify: `kart_overlay/ui/track_inspector_panel.py`
- Modify: `tests/unit/test_track_inspector_panel.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
from PySide6.QtWidgets import QApplication

from kart_overlay.domain.timing.lap_detector import LapDetectionResult, LapRecord
from kart_overlay.domain.timing.line_crossing import LineCrossing
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import SectorSplitRecord, TrackAnalysisSummary
from kart_overlay.ui.track_inspector_panel import TrackInspectorPanel


def test_track_inspector_formats_status_summary_with_recalculated_text():
    app = QApplication.instance() or QApplication([])
    panel = TrackInspectorPanel()
    summary = TrackAnalysisSummary(
        lap_result=LapDetectionResult(
            crossings=[LineCrossing(cross_time_sec=1.0, ratio=0.5)],
            laps=[LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0)],
            best_lap=LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0),
        ),
        sector_result=SectorDetectionResult(sector_crossings={"S1": [LineCrossing(cross_time_sec=2.0, ratio=0.2)]}),
        sector_splits=[SectorSplitRecord(lap_index=1, segment_name="S1", start_time_sec=0.0, end_time_sec=2.0, duration_sec=2.0, order=1)],
    )

    panel.update_analysis(
        lap_result=summary.lap_result,
        sector_result=summary.sector_result,
        analysis_summary=summary,
    )

    assert panel.last_lap_value.text() == "10.000 s"
    assert panel.best_sector_times_value.text() == "S1 2.000 s"
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_inspector_panel.py::test_track_inspector_formats_status_summary_with_recalculated_text -v`

Expected: FAIL if inspector formatting or labels do not match the new feedback plan.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/track_workspace.py
def _sync_analysis_panel(self) -> None:
    state = self.editor.analysis_state
    self.inspector.update_analysis(
        lap_result=None if state is None else state.lap_result,
        sector_result=None if state is None else state.sector_result,
        analysis_summary=None if state is None else state.summary,
    )
    self._session.set_track_definition(self.editor.track_definition)
    self._session.set_track_analysis(None if state is None else state.summary)
    self.editor_status_label.setText(self.editor.status_message)
```

```python
# README.md
## Incremental Update: Visual Timing-Line Editing

1. timing lines now support selection highlighting and endpoint handles
2. dragging a handle updates geometry visually and recalculates timing on release
3. sector deletion and start/finish reset now clear stale shared timing state
4. track status feedback now exposes current mode, selection, and recalculation messages
```

- [ ] **Step 4: Run targeted and full regression**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_track_editor_visual_feedback.py tests\unit\test_track_editor_advanced.py tests\unit\test_track_editor_interactions.py tests\unit\test_track_workspace.py tests\unit\test_track_inspector_panel.py -v`

Expected: PASS

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit -q`

Expected: `68 passed` or higher with the new visual-feedback test count included.

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/track_workspace.py kart_overlay/ui/track_inspector_panel.py README.md tests/unit/test_track_inspector_panel.py tests/unit/test_track_editor_visual_feedback.py tests/unit/test_track_editor_advanced.py tests/unit/test_track_editor_interactions.py tests/unit/test_track_workspace.py
git commit -m "feat: improve track editing feedback workflow"
```

## Self-Review

### Spec coverage

Covered in this plan:

1. selected line highlighting
2. hover and handle visibility
3. endpoint dragging
4. delete/reset actions
5. visible recalculation feedback
6. track inspector timing refresh
7. shared-session analysis refresh

Intentionally deferred to the separate packaging plan:

1. PyInstaller spec
2. bundled ffmpeg/ffprobe
3. Windows distributable smoke tests

### Placeholder scan

Checked for:

1. `TODO`
2. `TBD`
3. vague “implement later” phrasing
4. missing file paths

No placeholders remain.

### Type consistency

Planned names are consistent across tasks:

1. `EditableTimingLineItem`
2. `LineHandleItem`
3. `TrackEditor.editable_items()`
4. `TrackEditor.drag_selected_endpoint()`
5. `TrackEditor.finish_endpoint_drag()`
6. `TrackEditor.delete_selected_line()`
7. `TrackEditor.reset_start_finish()`
