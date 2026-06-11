# Track Editor Results-First Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the track-editing workspace into the approved results-first layout, invert alignment so the track layer moves over a fixed background image, and make overlay-widget text scale with a minimum readable font size.

**Architecture:** The main window keeps the left import/project column and removes the standalone right status column. The track tab becomes a nested-splitter workspace with a results panel, editor pane, and bottom operation strip. The track editor repurposes `DisplayTransform` as an overlay-layer transform, while widget rendering keeps the vector path but derives typography and spacing from widget geometry with a font floor.

**Tech Stack:** PySide6, Qt splitters/graphics view, project-session state propagation, pytest

---

### Task 1: Rebuild The Main Window And Track Workspace Layout

**Files:**
- Create: `tests/unit/test_main_window.py`
- Create: `tests/unit/test_track_results_panel.py`
- Create: `kart_overlay/ui/track_results_panel.py`
- Modify: `kart_overlay/ui/main_window.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `kart_overlay/ui/texts.py`
- Modify: `tests/unit/test_track_workspace.py`
- Delete: `kart_overlay/ui/workflow_status_panel.py`

- [ ] **Step 1: Write the failing layout and panel tests**

```python
from PySide6.QtWidgets import QApplication, QSplitter

from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.ui.main_window import create_main_window
from kart_overlay.ui.track_results_panel import TrackResultsPanel
from kart_overlay.ui.track_workspace import TrackWorkspace


def test_main_window_keeps_left_project_panel_and_removes_standalone_status_column():
    app = QApplication.instance() or QApplication([])
    window = create_main_window()
    splitter = window.centralWidget()

    assert isinstance(splitter, QSplitter)
    assert splitter.count() == 2
    app.quit()


def test_track_workspace_uses_nested_splitters_for_results_first_layout():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace(session=ProjectSession())

    splitters = workspace.findChildren(QSplitter)

    assert len(splitters) >= 2
    assert workspace.results_panel is not None
    assert workspace.editor is not None
    assert workspace.operation_bar is not None
    app.quit()


def test_track_results_panel_promotes_lap_and_sector_values():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = TrackWorkspace(session=session)
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")

    workspace.load_telemetry(telemetry)
    workspace.start_finish_button.click()
    workspace.editor.handle_scene_click((0.0, -5.0))
    workspace.editor.handle_scene_click((0.0, 5.0))

    assert workspace.results_panel.current_lap_value.text() != "--"
    assert workspace.results_panel.best_lap_value.text() != "--"
    app.quit()
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_main_window.py tests/unit/test_track_results_panel.py tests/unit/test_track_workspace.py -q
```

Expected: FAIL because `TrackResultsPanel` does not exist yet, `create_main_window()` still creates three panes, and `TrackWorkspace` still uses the old sidebar-plus-editor composition.

- [ ] **Step 3: Implement the results panel, nested splitters, and bottom operation bar**

```python
class TrackResultsPanel(QWidget):
    def __init__(self, *, session: ProjectSession | None = None) -> None:
        super().__init__()
        self._session = session or ProjectSession()
        self.current_lap_value = QLabel("--")
        self.best_lap_value = QLabel("--")
        self.sector_times_value = QLabel("--")
        self.telemetry_value = QLabel(app_text("workflow_status_not_loaded"))
        self.video_value = QLabel(app_text("workflow_status_not_loaded"))
        self.sample_value = QLabel(app_text("selection_none"))
        self.status_value = QLabel(app_text("view_mode"))
```

```python
def create_main_window() -> QMainWindow:
    window = QMainWindow()
    session = ProjectSession()

    splitter = QSplitter()
    tabs = QTabWidget()
    tabs.addTab(TrackWorkspace(session=session), app_text("tab_track"))
    tabs.addTab(CanvasWorkspace(session=session), app_text("tab_canvas"))
    tabs.addTab(ExportWorkspace(session=session), app_text("tab_export"))

    project_panel = ProjectPanel(session=session)
    splitter.addWidget(project_panel)
    splitter.addWidget(tabs)
    splitter.setSizes([260, 1540])
    window.setCentralWidget(splitter)
    return window
```

```python
self.results_panel = TrackResultsPanel(session=self._session)
self.operation_bar = QWidget()
self.precise_zoom_in_button = QPushButton("Zoom +")
self.precise_zoom_out_button = QPushButton("Zoom -")

top_splitter = QSplitter(Qt.Orientation.Horizontal)
top_splitter.addWidget(self.results_panel)
top_splitter.addWidget(self.editor)

main_splitter = QSplitter(Qt.Orientation.Vertical)
main_splitter.addWidget(top_splitter)
main_splitter.addWidget(self.operation_bar)
```

- [ ] **Step 4: Re-run the focused tests to verify the new layout passes**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_main_window.py tests/unit/test_track_results_panel.py tests/unit/test_track_workspace.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_main_window.py tests/unit/test_track_results_panel.py tests/unit/test_track_workspace.py kart_overlay/ui/main_window.py kart_overlay/ui/track_results_panel.py kart_overlay/ui/track_workspace.py kart_overlay/ui/texts.py
git rm kart_overlay/ui/workflow_status_panel.py
git commit -m "feat: rebuild track workspace into results-first layout"
```

### Task 2: Invert The Track Alignment Model To Move The Overlay Layer

**Files:**
- Modify: `kart_overlay/ui/track_editor.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `tests/unit/test_track_editor_advanced.py`
- Modify: `tests/unit/test_track_workspace.py`

- [ ] **Step 1: Write the failing transform-behavior tests**

```python
def test_track_editor_display_transform_moves_overlay_layer_without_shifting_background(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    telemetry = TelemetryImportService().import_file(FIXTURE_DIR / "test.gpx")
    image_path = tmp_path / "track-background.png"
    _write_png(image_path)
    editor = TrackEditor()
    editor.load_telemetry(telemetry)
    editor.set_background_image_path(str(image_path))

    before_rect = editor._background_item.sceneBoundingRect()
    editor.nudge_display_transform(delta_x=12.0, delta_y=-8.0)
    after_rect = editor._background_item.sceneBoundingRect()

    assert before_rect == after_rect
    app.quit()


def test_track_editor_precise_scale_controls_change_display_transform_scale():
    app = QApplication.instance() or QApplication([])
    workspace = TrackWorkspace()

    before_scale = workspace.editor.display_transform.scale
    workspace.precise_zoom_in_button.click()
    workspace.precise_zoom_out_button.click()

    assert workspace.editor.display_transform.scale != before_scale
    app.quit()
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_advanced.py tests/unit/test_track_workspace.py -q
```

Expected: FAIL because the current implementation applies `DisplayTransform` to the background pixmap and has no precise zoom buttons.

- [ ] **Step 3: Implement overlay-layer transform mapping and precise controls**

```python
def _map_track_point(self, point: QPointF) -> QPointF:
    transform = QTransform()
    transform.translate(self._display_transform.translate_x, -self._display_transform.translate_y)
    transform.rotate(self._display_transform.rotation_deg)
    transform.scale(self._display_transform.scale, self._display_transform.scale)
    return transform.map(point)


def _scene_to_track_point(self, point: QPointF) -> tuple[float, float]:
    transform = QTransform()
    transform.translate(self._display_transform.translate_x, -self._display_transform.translate_y)
    transform.rotate(self._display_transform.rotation_deg)
    transform.scale(self._display_transform.scale, self._display_transform.scale)
    inverted, ok = transform.inverted()
    mapped = inverted.map(point) if ok else point
    return mapped.x(), -mapped.y()
```

```python
def _render_background(self, track_bounds: QRectF) -> None:
    pixmap = QPixmap(self._background_image_path)
    background_rect = self._fit_background_rect(track_bounds=track_bounds, pixmap=pixmap)
    self._background_item = QGraphicsPixmapItem(pixmap)
    self._background_item.setPos(background_rect.topLeft())
    self._background_item.setScale(background_rect.height() / max(float(pixmap.height()), 1.0))
```

```python
def _nudge_scale(self, factor: float) -> None:
    self.editor.scale_display_transform(factor)
    self._sync_analysis_panel()
```

- [ ] **Step 4: Re-run the focused tests to verify the interaction model passes**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_advanced.py tests/unit/test_track_workspace.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_track_editor_advanced.py tests/unit/test_track_workspace.py kart_overlay/ui/track_editor.py kart_overlay/ui/track_workspace.py
git commit -m "feat: move track overlay layer over fixed background"
```

### Task 3: Make Widget Typography Scale With Geometry And A Minimum Font Floor

**Files:**
- Create: `tests/unit/test_hud_theme_scaling.py`
- Modify: `kart_overlay/widgets/base.py`
- Modify: `kart_overlay/widgets/hud_theme.py`
- Modify: `kart_overlay/widgets/speed_widget.py`
- Modify: `kart_overlay/widgets/timer_widget.py`
- Modify: `kart_overlay/widgets/altitude_widget.py`
- Modify: `kart_overlay/widgets/heading_widget.py`
- Modify: `kart_overlay/widgets/g_force_widget.py`
- Modify: `kart_overlay/widgets/lap_summary_widget.py`
- Modify: `kart_overlay/widgets/best_lap_widget.py`
- Modify: `kart_overlay/widgets/sector_state_widget.py`
- Modify: `kart_overlay/widgets/coordinates_widget.py`
- Modify: `kart_overlay/widgets/mini_track_widget.py`

- [ ] **Step 1: Write the failing typography-scaling tests**

```python
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.speed_widget import SpeedWidget


def test_overlay_widget_font_px_scales_with_width_and_respects_floor():
    widget = SpeedWidget(x=0, y=0, width=420, height=160)

    assert widget.font_px(20, minimum=10) > 20
    assert SpeedWidget(x=0, y=0, width=90, height=40).font_px(20, minimum=10) == 10
```

```python
def test_draw_hud_card_metrics_expand_for_large_widget():
    metrics = hud_card_metrics(width=420, height=160)

    assert metrics.value_px > metrics.title_px
    assert metrics.title_px >= 10
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_hud_theme_scaling.py tests/unit/test_canvas_workspace.py tests/unit/test_widget_factory_analysis.py -q
```

Expected: FAIL because there are no shared scaling helpers yet and widget text sizes are still fixed.

- [ ] **Step 3: Add shared geometry helpers and update widgets to use them**

```python
class OverlayWidget(ABC):
    def scale_ratio(self, *, base_width: int | None = None, base_height: int | None = None) -> float:
        width_ratio = self.width / max(base_width or self.default_width, 1)
        height_ratio = self.height / max(base_height or self.default_height, 1)
        return max(0.45, min(width_ratio, height_ratio))

    def font_px(self, px: int, *, minimum: int = 10) -> int:
        return max(minimum, int(round(px * self.scale_ratio())))
```

```python
@dataclass(frozen=True)
class HudCardMetrics:
    title_px: int
    value_px: int
    subtitle_px: int
    underline_h: float


def hud_card_metrics(*, width: float, height: float) -> HudCardMetrics:
    ratio = max(0.45, min(width / 260.0, height / 110.0))
    return HudCardMetrics(
        title_px=max(10, int(round(9 * ratio))),
        value_px=max(14, int(round(20 * ratio))),
        subtitle_px=max(9, int(round(8 * ratio))),
        underline_h=max(2.0, 3.0 * ratio),
    )
```

```python
def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
    draw_hud_card(
        painter,
        self.bounds_rect(),
        title=self.display_name,
        value=value_text,
        subtitle=subtitle_text,
        accent=ACCENT,
    )
```

- [ ] **Step 4: Re-run the focused tests to verify typography scales correctly**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_hud_theme_scaling.py tests/unit/test_canvas_workspace.py tests/unit/test_widget_factory_analysis.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_hud_theme_scaling.py kart_overlay/widgets/base.py kart_overlay/widgets/hud_theme.py kart_overlay/widgets/speed_widget.py kart_overlay/widgets/timer_widget.py kart_overlay/widgets/altitude_widget.py kart_overlay/widgets/heading_widget.py kart_overlay/widgets/g_force_widget.py kart_overlay/widgets/lap_summary_widget.py kart_overlay/widgets/best_lap_widget.py kart_overlay/widgets/sector_state_widget.py kart_overlay/widgets/coordinates_widget.py kart_overlay/widgets/mini_track_widget.py
git commit -m "feat: scale widget typography with geometry"
```

### Task 4: Refresh Documentation And Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-06-10-track-editor-results-first-layout-design.md`

- [ ] **Step 1: Add the regression tests and focused verification commands to the docs**

```markdown
The track page now uses a results-first nested-splitter layout:

1. left import/project column remains fixed
2. top-left results panel surfaces lap and sector outputs
3. top-right editor keeps the background fixed while the overlay track layer moves
4. bottom strip groups alignment and timing-line operations
```

- [ ] **Step 2: Run the full test suite**

Run:

```bash
D:\Anaconda_env\karting\python.exe -m pytest -q
```

Expected: PASS across the repository.

- [ ] **Step 3: Rebuild the Windows distribution after tests pass**

Run:

```bash
$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; D:\Anaconda_env\karting\python.exe scripts\build_windows_dist.py
```

Expected: refreshed `dist/KartOverlay/KartOverlay.exe`, `dist/KartOverlay-Setup.exe`, and `dist/KartOverlay-windows-x64.zip`

- [ ] **Step 4: Commit**

```bash
git add README.md docs/superpowers/specs/2026-06-10-track-editor-results-first-layout-design.md
git commit -m "docs: record results-first track workspace update"
```

## Self-Review

1. **Spec coverage:** The plan covers the approved layout, the fixed-background / moving-track interaction model, precision zoom controls, the results-first information panel, non-persistent splitter resizing, and minimum-font widget scaling.
2. **Placeholder scan:** No `TODO`/`TBD` markers remain. Each task lists exact files, test commands, and concrete code targets.
3. **Type consistency:** The plan consistently uses `TrackResultsPanel`, `precise_zoom_in_button`, `precise_zoom_out_button`, and the existing `DisplayTransform` fields without renaming them mid-plan.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-10-track-editor-results-first-layout-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
