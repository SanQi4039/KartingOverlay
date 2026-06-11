# Track/Canvas Map Interactions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add widget resize handles, vector-style canvas preview, basemap-only transform controls, and clearer timing-line visuals without changing telemetry analysis coordinates.

**Architecture:** Keep export rendering on the existing `FrameRenderer -> QImage` path, but give the interactive canvas preview a direct painter path for crisp on-screen rendering. Keep track geometry canonical while moving only the basemap display layer via `TrackDefinition.display_transform`, and update timing-line scene items so their visuals and hit-targets are separated cleanly.

**Tech Stack:** Python 3.11, PySide6, pytest, existing `ProjectSession`, `TrackEditor`, `CanvasWorkspace`, Amap static-map services

---

### Task 1: Basemap Request Investigation And Hardening

**Files:**
- Modify: `kart_overlay/infrastructure/map/amap_services.py`
- Modify: `kart_overlay/ui/track_editor.py`
- Test: `tests/unit/test_amap_services.py`
- Test: `tests/unit/test_track_editor_advanced.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

```python
def test_amap_static_map_service_can_build_coordinate_convert_url():
    ...

def test_track_editor_reports_provider_json_error_message():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_amap_services.py tests/unit/test_track_editor_advanced.py -q`

Expected: FAIL because coordinate conversion is not used and provider JSON error details are not surfaced.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. Amap GPS->GCJ coordinate conversion helper in `amap_services.py`
2. basemap request pipeline in `track_editor.py` that:
   - converts center coordinates before building the static-map URL
   - decodes JSON failure payloads when response is not an image
   - stores a clear `basemap_status_message`

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_amap_services.py tests/unit/test_track_editor_advanced.py -q`

Expected: PASS

### Task 2: Basemap-Only Transform State And Micro-Adjust Buttons

**Files:**
- Modify: `kart_overlay/ui/track_editor.py`
- Modify: `kart_overlay/ui/track_workspace.py`
- Modify: `kart_overlay/ui/project_panel.py`
- Test: `tests/unit/test_track_workspace.py`
- Test: `tests/unit/test_track_editor_advanced.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

```python
def test_track_workspace_arrow_buttons_adjust_display_transform():
    ...

def test_track_editor_applies_display_transform_to_basemap_item_only():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_workspace.py tests/unit/test_track_editor_advanced.py -q`

Expected: FAIL because the sidebar has no micro-adjust buttons and the basemap item does not use persistent transform state.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. four arrow buttons in `TrackWorkspace`
2. transform mutators in `TrackEditor` that update `TrackDefinition.display_transform`
3. basemap item positioning/scaling/rotation derived from the stored transform
4. project-session publication path so updates remain saveable

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_workspace.py tests/unit/test_track_editor_advanced.py -q`

Expected: PASS

### Task 3: Map-Like Track Editor Interaction Model

**Files:**
- Modify: `kart_overlay/ui/track_editor.py`
- Test: `tests/unit/test_track_editor_interactions.py`
- Test: `tests/unit/test_track_editor_click_flow.py`
- Test: `tests/unit/test_track_editor_advanced.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

```python
def test_track_editor_left_drag_on_empty_space_moves_basemap():
    ...

def test_track_editor_ctrl_wheel_scales_basemap():
    ...

def test_track_editor_right_drag_rotates_basemap():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_interactions.py tests/unit/test_track_editor_click_flow.py tests/unit/test_track_editor_advanced.py -q`

Expected: FAIL because empty-space drag currently behaves like generic view panning, not basemap alignment editing.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. interaction-state tracking for left-drag translation
2. `Ctrl+wheel` scale updates
3. right-drag rotation updates
4. redraw path that leaves track geometry unchanged while updating only the basemap transform

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_interactions.py tests/unit/test_track_editor_click_flow.py tests/unit/test_track_editor_advanced.py -q`

Expected: PASS

### Task 4: Timing-Line Visual Cleanup And Cursor Accuracy

**Files:**
- Modify: `kart_overlay/ui/track_scene_items.py`
- Modify: `kart_overlay/ui/track_editor.py`
- Test: `tests/unit/test_track_editor_visual_feedback.py`
- Test: `tests/unit/test_track_editor_widget.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

```python
def test_start_finish_uses_checkerboard_visual_without_text_label():
    ...

def test_sector_line_remains_colored_and_thin():
    ...

def test_drawing_mode_uses_cross_cursor():
    ...

def test_selected_line_has_visible_highlight_change():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_visual_feedback.py tests/unit/test_track_editor_widget.py -q`

Expected: FAIL because current lines still use text labels, thicker pens, and incomplete selection visuals.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. checkerboard start/finish rendering
2. thin sector rendering
3. no label text for either line type
4. stronger selected-state pen/handle feedback
5. crosshair cursor while drawing

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_editor_visual_feedback.py tests/unit/test_track_editor_widget.py -q`

Expected: PASS

### Task 5: Vector-Style Canvas Preview Path

**Files:**
- Modify: `kart_overlay/ui/canvas_workspace.py`
- Modify: `kart_overlay/widgets/base.py`
- Test: `tests/unit/test_canvas_workspace.py`
- Test: `tests/unit/test_frame_renderer.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

```python
def test_canvas_preview_widget_paints_selected_widget_with_resize_handles():
    ...

def test_canvas_preview_widget_resizes_widget_layout_via_drag_handle():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_canvas_workspace.py tests/unit/test_frame_renderer.py -q`

Expected: FAIL because the preview does not expose resize handles and does not support mouse-driven resize.

- [ ] **Step 3: Write minimal implementation**

Implement:

1. direct preview painting path in `CanvasPreviewWidget`
2. selected-widget handle geometry
3. resize drag logic that writes width/height/x/y back to session layouts
4. keep export-only `FrameRenderer` path unchanged

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_canvas_workspace.py tests/unit/test_frame_renderer.py -q`

Expected: PASS

### Task 6: Full Regression And Documentation

**Files:**
- Modify: `README.md`
- Test: `tests/unit`

- [ ] **Step 1: Update incremental documentation**

Add a README incremental update describing:

1. widget resize handles
2. vector-style canvas preview
3. basemap transform controls
4. checkerboard start/finish visual
5. improved basemap diagnostics

- [ ] **Step 2: Run the focused and full suites**

Run: `D:\Anaconda_env\karting\python.exe -m pytest tests/unit -q`

Expected: PASS

- [ ] **Step 3: Sanity-check spec coverage**

Confirm the implementation covered:

1. widget resize
2. vector-style preview
3. preserved video metadata import
4. basemap failure hardening
5. line visual cleanup
6. drawing cursor accuracy
7. selection highlight
8. micro-adjust buttons
9. map-like drag/scale/rotate with persistence
