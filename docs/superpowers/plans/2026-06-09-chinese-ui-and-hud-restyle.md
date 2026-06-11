# Chinese UI And HUD Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the app to a Chinese-first desktop product with a draggable custom title bar and a restrained karting telemetry sticker HUD style without breaking the current workflow chain.

**Architecture:** Add one focused text catalog for Chinese labels, one focused custom window-chrome module for drag/maximize/minimize behavior, and one HUD theme restyle pass that propagates through the existing widget factory and renderer. Keep the current session, workflow pages, export pipeline, and widget factory architecture intact while improving presentation and interaction.

**Tech Stack:** Python 3.11, PySide6, pytest, existing `ProjectSession` / widget factory / frame renderer pipeline

---

## File Structure

**Create**
- `kart_overlay/ui/texts.py`
- `kart_overlay/ui/window_chrome.py`
- `tests/unit/test_ui_texts.py`
- `tests/unit/test_window_chrome.py`
- `tests/unit/test_hud_theme_restyle.py`

**Modify**
- `kart_overlay/ui/main_window.py`
- `kart_overlay/ui/project_panel.py`
- `kart_overlay/ui/sync_workspace.py`
- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/ui/track_inspector_panel.py`
- `kart_overlay/ui/canvas_workspace.py`
- `kart_overlay/ui/export_workspace.py`
- `kart_overlay/ui/export_dialog.py`
- `kart_overlay/ui/workflow_status_panel.py`
- `kart_overlay/widgets/hud_theme.py`
- `kart_overlay/widgets/widget_factory.py`
- `kart_overlay/widgets/speed_widget.py`
- `kart_overlay/widgets/timer_widget.py`
- `kart_overlay/widgets/altitude_widget.py`
- `kart_overlay/widgets/heading_widget.py`
- `kart_overlay/widgets/g_force_widget.py`
- `kart_overlay/widgets/lap_summary_widget.py`
- `kart_overlay/widgets/best_lap_widget.py`
- `kart_overlay/widgets/sector_state_widget.py`
- `kart_overlay/widgets/coordinates_widget.py`
- `kart_overlay/widgets/mini_track_widget.py`
- `tests/unit/test_main_window.py`
- `tests/unit/test_canvas_workspace.py`
- `tests/unit/test_widget_factory_analysis.py`
- `README.md`

**Responsibilities**
- `kart_overlay/ui/texts.py`
  - own all Chinese-first UI strings and HUD display labels
  - provide one stable lookup boundary for pages and widgets
- `kart_overlay/ui/window_chrome.py`
  - own custom title bar visuals
  - own drag, double-click maximize, minimize, maximize/restore, and close button wiring
- `kart_overlay/ui/main_window.py`
  - compose the custom title bar shell with the existing workflow pages
- `kart_overlay/widgets/hud_theme.py`
  - own the sticker-style HUD primitives, colors, typography, gauge accents, and divider language
- widget files
  - consume centralized Chinese labels and the lighter HUD primitives instead of heavy card rendering
- `kart_overlay/ui/canvas_workspace.py`
  - keep widget dragging stable in both X and Y and make selection feedback clearer

### Task 1: Add A Central Chinese Text Catalog

**Files:**
- Create: `kart_overlay/ui/texts.py`
- Create: `tests/unit/test_ui_texts.py`
- Modify: `kart_overlay/widgets/widget_factory.py`

- [ ] **Step 1: Write the failing tests**

```python
from kart_overlay.ui.texts import app_text, widget_display_name
from kart_overlay.widgets.widget_factory import widget_labels


def test_app_text_defaults_to_chinese_window_and_tab_labels():
    assert app_text("window_title") == "卡丁车数据叠层"
    assert app_text("tab_sync") == "视频同步"
    assert app_text("tab_track") == "赛道编辑"
    assert app_text("tab_canvas") == "画布编辑"
    assert app_text("tab_export") == "导出视频"


def test_widget_display_name_defaults_to_chinese():
    assert widget_display_name("speed") == "速度"
    assert widget_display_name("timer") == "当前圈"
    assert widget_display_name("mini_track") == "赛道图"


def test_widget_labels_returns_chinese_names_for_canvas_list():
    labels = widget_labels()

    assert "速度" in labels
    assert "当前圈" in labels
    assert "赛道图" in labels
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_ui_texts.py -v`

Expected: FAIL because `kart_overlay.ui.texts` does not exist and `widget_labels()` still returns English keys.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/texts.py
APP_TEXT = {
    "window_title": "卡丁车数据叠层",
    "tab_sync": "视频同步",
    "tab_track": "赛道编辑",
    "tab_canvas": "画布编辑",
    "tab_export": "导出视频",
}

WIDGET_DISPLAY_NAMES = {
    "speed": "速度",
    "timer": "当前圈",
    "altitude": "海拔",
    "heading": "航向",
    "g_force": "G值",
    "lap_summary": "圈速摘要",
    "best_lap": "最佳圈",
    "sector_state": "分段状态",
    "coordinates": "坐标",
    "mini_track": "赛道图",
}


def app_text(key: str) -> str:
    return APP_TEXT.get(key, key)


def widget_display_name(widget_key: str) -> str:
    return WIDGET_DISPLAY_NAMES.get(widget_key, widget_key)
```

```python
# kart_overlay/widgets/widget_factory.py
from kart_overlay.ui.texts import widget_display_name


def widget_labels() -> list[str]:
    return [widget_display_name(key) for key in default_widget_layouts().keys()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_ui_texts.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/texts.py kart_overlay/widgets/widget_factory.py tests/unit/test_ui_texts.py
git commit -m "feat: add chinese ui text catalog"
```

### Task 2: Build A Custom Chinese Title Bar Shell

**Files:**
- Create: `kart_overlay/ui/window_chrome.py`
- Modify: `kart_overlay/ui/main_window.py`
- Modify: `tests/unit/test_main_window.py`
- Create: `tests/unit/test_window_chrome.py`

- [ ] **Step 1: Write the failing tests**

```python
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication

from kart_overlay.ui.main_window import create_main_window
from kart_overlay.ui.window_chrome import TitleBarWidget


def test_create_main_window_uses_chinese_custom_title_bar():
    app = QApplication.instance() or QApplication([])
    window = create_main_window()

    title_bar = window.findChild(TitleBarWidget)

    assert window.windowTitle() == "卡丁车数据叠层"
    assert title_bar is not None
    assert title_bar.title_label.text() == "卡丁车数据叠层"
    app.quit()


def test_title_bar_buttons_control_window_state():
    app = QApplication.instance() or QApplication([])
    window = create_main_window()
    title_bar = window.findChild(TitleBarWidget)

    title_bar.minimize_button.click()
    assert window.isMinimized() is True
    window.showNormal()

    title_bar.toggle_maximize_restore()
    assert window.isMaximized() is True

    title_bar.toggle_maximize_restore()
    assert window.isMaximized() is False
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_main_window.py tests\unit\test_window_chrome.py -v`

Expected: FAIL because `TitleBarWidget` does not exist and the main window still uses default shell composition.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/window_chrome.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QWidget


class TitleBarWidget(QWidget):
    def __init__(self, *, owner: QMainWindow, title: str) -> None:
        super().__init__(owner)
        self._owner = owner
        self.title_label = QLabel(title)
        self.minimize_button = QPushButton("最小化")
        self.maximize_button = QPushButton("最大化")
        self.close_button = QPushButton("关闭")

        layout = QHBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

        self.minimize_button.clicked.connect(owner.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)
        self.close_button.clicked.connect(owner.close)

    def toggle_maximize_restore(self) -> None:
        if self._owner.isMaximized():
            self._owner.showNormal()
            self.maximize_button.setText("最大化")
        else:
            self._owner.showMaximized()
            self.maximize_button.setText("还原")
```

```python
# kart_overlay/ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QVBoxLayout, QWidget
from kart_overlay.ui.texts import app_text
from kart_overlay.ui.window_chrome import TitleBarWidget


def create_main_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle(app_text("window_title"))
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    ...
    shell = QWidget()
    shell_layout = QVBoxLayout(shell)
    shell_layout.setContentsMargins(0, 0, 0, 0)
    shell_layout.setSpacing(0)
    title_bar = TitleBarWidget(owner=window, title=app_text("window_title"))
    shell_layout.addWidget(title_bar)
    shell_layout.addWidget(splitter, 1)
    window.setCentralWidget(shell)
    return window
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_main_window.py tests\unit\test_window_chrome.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/window_chrome.py kart_overlay/ui/main_window.py tests/unit/test_main_window.py tests/unit/test_window_chrome.py
git commit -m "feat: add chinese custom title bar shell"
```

### Task 3: Translate The Main Workflow UI Into Chinese

**Files:**
- Modify: `kart_overlay/ui/main_window.py`
- Modify: `kart_overlay/ui/project_panel.py`
- Modify: `kart_overlay/ui/sync_workspace.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `kart_overlay/ui/track_inspector_panel.py`
- Modify: `kart_overlay/ui/canvas_workspace.py`
- Modify: `kart_overlay/ui/export_workspace.py`
- Modify: `kart_overlay/ui/export_dialog.py`
- Modify: `kart_overlay/ui/workflow_status_panel.py`
- Modify: `kart_overlay/ui/texts.py`
- Modify: `tests/unit/test_main_window.py`
- Modify: `tests/unit/test_canvas_workspace.py`

- [ ] **Step 1: Write the failing tests**

```python
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QTabWidget

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.ui.canvas_workspace import CanvasWorkspace
from kart_overlay.ui.main_window import create_main_window


def test_main_window_tabs_are_chinese():
    app = QApplication.instance() or QApplication([])
    window = create_main_window()
    tabs = window.findChild(QTabWidget)

    assert [tabs.tabText(index) for index in range(tabs.count())] == [
        "视频同步",
        "赛道编辑",
        "画布编辑",
        "导出视频",
    ]
    app.quit()


def test_canvas_workspace_lists_chinese_widget_names():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    listed = [workspace.widget_list.item(index).text() for index in range(workspace.widget_list.count())]

    assert "速度" in listed
    assert "当前圈" in listed
    assert "赛道图" in listed
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_main_window.py tests\unit\test_canvas_workspace.py -v`

Expected: FAIL because the current pages and tabs still expose English labels.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/texts.py
APP_TEXT.update(
    {
        "project_workflow": "项目流程",
        "button_browse_telemetry": "选择遥测文件",
        "button_import_telemetry": "导入遥测",
        "button_browse_video": "选择视频",
        "button_import_video": "导入视频",
        "button_save_project": "保存项目",
        "button_load_project": "加载项目",
        "button_read_video_info": "读取视频信息",
        "button_pick_sample": "选择遥测点",
        "button_apply_sync": "应用同步点",
        "button_refresh_preview": "刷新预览",
        "button_track_view": "查看",
        "button_start_finish": "起终点",
        "button_add_sector": "添加分段",
        "button_toggle_basemap": "切换底图",
        "button_delete_selected": "删除选中",
        "button_reset_start_finish": "重置起终点",
        "button_apply_position": "应用位置",
        "button_export_mov": "导出 MOV",
        "button_cancel_export": "取消导出",
    }
)
```

```python
# kart_overlay/ui/main_window.py
tabs.addTab(SyncWorkspace(session=session), app_text("tab_sync"))
tabs.addTab(TrackWorkspace(session=session), app_text("tab_track"))
tabs.addTab(CanvasWorkspace(session=session), app_text("tab_canvas"))
tabs.addTab(ExportWorkspace(session=session), app_text("tab_export"))
```

```python
# kart_overlay/ui/canvas_workspace.py
from kart_overlay.ui.texts import app_text, widget_display_name, widget_key_from_display_name

self.enabled_toggle = QCheckBox("组件启用")
self.video_reference_toggle = QCheckBox("显示视频参考")
self.apply_position_button = QPushButton(app_text("button_apply_position"))
self.position_label = QLabel("位置: --")
self.preview_label = QLabel("画布组件预览")
self.preview_time_label = QLabel("预览时间: 0.000 秒")
...
controls_layout.addWidget(QLabel("画布组件"))
preview_layout.addWidget(QLabel("预览"))
...
def select_widget(self, widget_label: str) -> None:
    widget_key = widget_key_from_display_name(widget_label)
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_main_window.py tests\unit\test_canvas_workspace.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/texts.py kart_overlay/ui/main_window.py kart_overlay/ui/project_panel.py kart_overlay/ui/sync_workspace.py kart_overlay/ui/track_workspace.py kart_overlay/ui/track_inspector_panel.py kart_overlay/ui/canvas_workspace.py kart_overlay/ui/export_workspace.py kart_overlay/ui/export_dialog.py kart_overlay/ui/workflow_status_panel.py tests/unit/test_main_window.py tests/unit/test_canvas_workspace.py
git commit -m "feat: translate workflow ui to chinese"
```

### Task 4: Restyle HUD Theme And Default Chinese Widget Labels

**Files:**
- Modify: `kart_overlay/widgets/hud_theme.py`
- Modify: `kart_overlay/widgets/widget_factory.py`
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
- Create: `tests/unit/test_hud_theme_restyle.py`
- Modify: `tests/unit/test_widget_factory_analysis.py`

- [ ] **Step 1: Write the failing tests**

```python
from PySide6.QtGui import QColor

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.widgets.hud_theme import ACCENT, PANEL_FILL_ALPHA, PRIMARY_TEXT
from kart_overlay.widgets.widget_factory import build_widgets_from_session


def test_hud_theme_matches_lightweight_sticker_palette():
    assert PRIMARY_TEXT == QColor("#f8f9fa")
    assert ACCENT == QColor("#2fb5ff")
    assert PANEL_FILL_ALPHA == 0


def test_widget_factory_builds_chinese_named_widgets_for_overlay():
    session = ProjectSession()
    widgets = build_widgets_from_session(session)
    display_names = {widget.display_name for widget in widgets}

    assert "速度" in display_names
    assert "当前圈" in display_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_hud_theme_restyle.py tests\unit\test_widget_factory_analysis.py -v`

Expected: FAIL because the theme still uses card-heavy fills and the widget display names are still English.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/widgets/hud_theme.py
from PySide6.QtGui import QColor

PRIMARY_TEXT = QColor("#f8f9fa")
SECONDARY_TEXT = QColor("#d9e4ec")
ACCENT = QColor("#2fb5ff")
THROTTLE = QColor("#4fe21f")
BRAKE = QColor("#ff3b30")
RPM_WARN = QColor("#ff9f0a")
PANEL_FILL_ALPHA = 0


def draw_sticker_label(...):
    ...


def draw_value_with_shadow(...):
    ...


def draw_divider_line(...):
    ...
```

```python
# kart_overlay/widgets/speed_widget.py
class SpeedWidget(OverlayWidget):
    display_name = "速度"
```

```python
# kart_overlay/widgets/timer_widget.py
class TimerWidget(OverlayWidget):
    display_name = "当前圈"
```

```python
# kart_overlay/widgets/mini_track_widget.py
class MiniTrackWidget(OverlayWidget):
    display_name = "赛道图"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_hud_theme_restyle.py tests\unit\test_widget_factory_analysis.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/widgets/hud_theme.py kart_overlay/widgets/widget_factory.py kart_overlay/widgets/speed_widget.py kart_overlay/widgets/timer_widget.py kart_overlay/widgets/altitude_widget.py kart_overlay/widgets/heading_widget.py kart_overlay/widgets/g_force_widget.py kart_overlay/widgets/lap_summary_widget.py kart_overlay/widgets/best_lap_widget.py kart_overlay/widgets/sector_state_widget.py kart_overlay/widgets/coordinates_widget.py kart_overlay/widgets/mini_track_widget.py tests/unit/test_hud_theme_restyle.py tests/unit/test_widget_factory_analysis.py
git commit -m "feat: restyle hud widgets for chinese telemetry stickers"
```

### Task 5: Fix Canvas Dragging And Selection Feedback

**Files:**
- Modify: `kart_overlay/ui/canvas_workspace.py`
- Modify: `tests/unit/test_canvas_workspace.py`

- [ ] **Step 1: Write the failing tests**

```python
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.ui.canvas_workspace import CanvasWorkspace


def test_canvas_workspace_drag_updates_widget_x_and_y():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)
    workspace.select_widget("速度")

    workspace.preview_widget._selected_widget_key = "speed"
    workspace.preview_widget._dragging = True
    workspace.preview_widget._drag_offset = QPoint(0, 0)

    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(220.0, 180.0),
        QPointF(220.0, 180.0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    workspace.preview_widget.mouseMoveEvent(event)

    assert session.widget_layouts["speed"]["x"] > 56
    assert session.widget_layouts["speed"]["y"] > 48
    app.quit()


def test_canvas_workspace_selection_label_is_chinese():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)
    workspace.select_widget("速度")

    assert workspace.position_label.text().startswith("位置:")
    app.quit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_canvas_workspace.py::test_canvas_workspace_drag_updates_widget_x_and_y tests\unit\test_canvas_workspace.py::test_canvas_workspace_selection_label_is_chinese -v`

Expected: FAIL because the canvas selection flow still expects English widget keys and the label copy is still mixed.

- [ ] **Step 3: Write minimal implementation**

```python
# kart_overlay/ui/texts.py
DISPLAY_TO_WIDGET_KEY = {value: key for key, value in WIDGET_DISPLAY_NAMES.items()}


def widget_key_from_display_name(value: str) -> str:
    return DISPLAY_TO_WIDGET_KEY.get(value, value)
```

```python
# kart_overlay/ui/canvas_workspace.py
def select_widget(self, widget_label: str) -> None:
    widget_key = widget_key_from_display_name(widget_label)
    if not widget_key:
        return
    self._selected_widget_key = widget_key
    self.preview_widget.set_selected_widget_key(widget_key)
    layout = self._session.widget_layouts.get(widget_key, {"x": 0, "y": 0})
    ...
    self.position_label.setText(f"位置: {self.x_input.value()}, {self.y_input.value()}")
```

```python
# kart_overlay/ui/canvas_workspace.py
def move_selected_widget(self, x: int, y: int) -> None:
    ...
    self.position_label.setText(f"位置: {x}, {y}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_canvas_workspace.py::test_canvas_workspace_drag_updates_widget_x_and_y tests\unit\test_canvas_workspace.py::test_canvas_workspace_selection_label_is_chinese -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kart_overlay/ui/canvas_workspace.py kart_overlay/ui/texts.py tests/unit/test_canvas_workspace.py
git commit -m "fix: polish chinese canvas drag interaction"
```

### Task 6: Full UI/HUD Regression And Documentation Update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update incremental documentation**

```markdown
## Incremental Update: Chinese Product UI And HUD Restyle

The desktop product is now Chinese-first by default:

1. the main window uses a custom Chinese title bar with draggable shell controls
2. workflow tabs, page controls, and status text now default to Chinese
3. overlay widget labels now default to Chinese in both preview and export
4. the HUD visual language now favors lightweight telemetry stickers instead of heavy boxed cards
5. canvas widget selection and dragging now remain clear with Chinese labels and stable X/Y updates
```

- [ ] **Step 2: Run targeted regression**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_ui_texts.py tests\unit\test_window_chrome.py tests\unit\test_main_window.py tests\unit\test_canvas_workspace.py tests\unit\test_widget_factory_analysis.py tests\unit\test_hud_theme_restyle.py -v`

Expected: PASS

- [ ] **Step 3: Run full regression**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests\unit -q`

Expected: all tests pass at or above the current baseline count.

- [ ] **Step 4: Commit**

```bash
git add README.md tests/unit/test_ui_texts.py tests/unit/test_window_chrome.py tests/unit/test_main_window.py tests/unit/test_canvas_workspace.py tests/unit/test_widget_factory_analysis.py tests/unit/test_hud_theme_restyle.py
git commit -m "feat: finalize chinese ui and hud restyle"
```

## Self-Review

### Spec coverage

Covered in this plan:

1. custom Chinese title bar
2. full Chinese default UI copy
3. Chinese default HUD labels
4. sticker-style HUD visual direction
5. canvas drag and selection polish
6. regression coverage and docs

Intentionally deferred:

1. multi-language switching
2. full workflow IA redesign
3. export-pipeline rewrites

### Placeholder scan

Checked for:

1. `TODO`
2. `TBD`
3. vague “implement later” wording
4. undefined file paths

No placeholders remain.

### Type consistency

Planned names are consistent across tasks:

1. `app_text`
2. `widget_display_name`
3. `widget_key_from_display_name`
4. `TitleBarWidget`
5. `toggle_maximize_restore`
6. `draw_sticker_label`
7. `PANEL_FILL_ALPHA`
