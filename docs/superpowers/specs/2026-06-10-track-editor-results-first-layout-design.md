# Track Editor Results-First Layout Design

## Goal

Reshape the track-editing and canvas-editing experience around a clearer workspace model:

1. keep the far-left import/sidebar area in place
2. rebuild the right-side track page into a results-first split layout
3. treat the imported track background image as a fixed full-bleed reference
4. move, scale, and rotate the telemetry/timing overlay layer instead of the background layer
5. add higher-precision nudge and zoom controls for track alignment
6. show lap and sector results directly in the track page instead of leaving the right-side area mostly blank
7. keep overlay widgets vector-rendered while making text scale with widget size, subject to a minimum readable font size

The core architectural rule for this change is:

`the background image becomes the fixed visual reference; the telemetry path and timing lines become the transformed alignment layer shown on top of it.`

## Current Problems

1. the track workspace still uses a sidebar-plus-editor composition that leaves too much empty space and does not prioritize lap results
2. the current background-image alignment model moves the background image itself, which is the opposite of the user's preferred mental model
3. the micro-adjust controls only support translation and still conceptually target the background transform
4. the track page does not use the available right-side space to show current lap, best lap, and sector timings prominently
5. the current operation controls are not grouped into a compact horizontal editing strip
6. widget rendering is vector-based, but the text sizing inside widgets does not scale together with the rest of the component geometry
7. splitter boundaries are not yet exposed as fully user-draggable workspace dividers

## Chosen Approach

The implementation will use four coordinated changes:

1. **Rebuild the main working area around a cleaner splitter composition**
   - Keep the existing far-left import/sidebar column unchanged.
   - Remove the old standalone right-side status column from the main shell.
   - Let the center tab area own the new track-specific nested splitter layout.
   - Use a vertical splitter for the right-side workspace:
     - top: main content
     - bottom: narrow operation bar
   - Use a horizontal splitter inside the top area:
     - left: results-first information panel
     - right: track/map editor
   - Allow every boundary between these areas to be resized by mouse drag.
   - Do not persist splitter sizes; each fresh app launch returns to default proportions.

2. **Invert the alignment model so the track layer moves and the background stays fixed**
   - When a background image is loaded, it fills the visible editor area as the fixed reference layer.
   - The existing transform state is repurposed to describe the overlay track layer, not the background item.
   - Empty-space drag pans the transformed track layer.
   - `Ctrl + wheel` zooms the transformed track layer.
   - Right-drag rotates the transformed track layer.
   - Sidebar arrow controls become precise translation nudges for the transformed track layer.
   - Two new buttons add precise zoom-in / zoom-out controls for the transformed track layer.

3. **Turn the track page into a results-first editing dashboard**
   - The top-left panel emphasizes performance outputs first:
     - current lap
     - best lap
     - sector times
   - Secondary details remain visible below or beside them:
     - telemetry import state
     - video canvas size
     - currently selected sample coordinates
     - line/edit status
   - The top-right panel remains focused on the visual track editor only.
   - The bottom operation strip uses the approved single-row grouped layout:
     - mode group
     - background group
     - track nudge/zoom group
     - line action group

4. **Make widget typography scale with widget geometry**
   - Keep direct `QPainter` vector rendering for preview and export.
   - Replace fixed font sizes, stroke widths, and spacing constants with geometry-derived values.
   - Clamp text sizing with a minimum font floor so small widgets remain readable.
   - Preserve the existing resize-handle workflow in the canvas editor.

## Components

### Track Workspace Layout

Files involved:

- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/ui/main_window.py`
- `kart_overlay/ui/project_panel.py`

Responsibilities:

1. keep the left import column unchanged
2. remove the standalone right-side workflow-status column
3. rebuild the track workspace into nested splitters
4. expose resizable boundaries without persistence
5. present the lower operation strip as one compact grouped row

The main application layout still preserves the import/project navigation structure on the far left, but the center working region is now simplified to a two-pane shell: import/project column plus tabbed workspace. The removed right-side status column is replaced by the richer results-first track panel.

### Track Editor Transform Model

Files involved:

- `kart_overlay/ui/track_editor.py`
- `kart_overlay/domain/track/models.py`
- `kart_overlay/ui/track_scene_items.py`
- `kart_overlay/ui/project_panel.py`

Responsibilities:

1. keep the background image visually fixed to the editor viewport
2. apply transform state to the telemetry path plus timing-line layer
3. make mouse gestures operate on the transformed track layer
4. keep timing-line editing and selection behavior compatible with the new transform model
5. preserve existing project save/load semantics through the same stored transform fields

The current `DisplayTransform` fields remain the persistence boundary:

1. `translate_x`
2. `translate_y`
3. `rotation_deg`
4. `scale`

What changes is their meaning inside the editor: they now describe how the track/timing overlay is positioned relative to the background image, rather than how the background image is positioned relative to canonical track coordinates.

### Results-First Information Panel

Files involved:

- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/ui/track_inspector_panel.py`
- potentially a small new `kart_overlay/ui/track_results_panel.py`

Responsibilities:

1. promote lap and sector results into the primary display area
2. keep secondary telemetry/video/sample metadata visible without dominating the page
3. refresh results immediately when timing lines are added, moved, deleted, or reset

The panel should present:

1. current lap time
2. best lap time
3. sector timing summary
4. telemetry/video/sample metadata
5. current track-editing status text

This panel is primarily read-only status/UI composition. It should not own alignment gestures or scene editing logic.

### Operation Strip

Files involved:

- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/ui/texts.py`

Responsibilities:

1. regroup controls into one horizontal action strip
2. add zoom-in / zoom-out buttons near the arrow nudge controls
3. preserve background import/replace/clear/reset controls
4. keep line reset/delete actions easy to find

The approved grouping is:

1. mode
   - view
   - start/finish
   - sector
2. background
   - import
   - replace
   - clear
   - opacity
3. track adjustment
   - up
   - down
   - left
   - right
   - zoom in
   - zoom out
4. line actions
   - delete selected
   - reset start/finish

### Canvas Widget Scaling

Files involved:

- `kart_overlay/ui/canvas_workspace.py`
- `kart_overlay/widgets/base.py`
- `kart_overlay/widgets/*`
- `kart_overlay/widgets/hud_theme.py`

Responsibilities:

1. derive font sizes from widget geometry
2. apply minimum readable font constraints
3. keep line widths, spacing, and label placement visually proportional
4. preserve current vector rendering quality and mouse-resize workflow

Each widget should continue to define its own visual structure, but shared helpers should be used where possible so minimum font logic does not diverge across the widget set.

## Interaction Model

### Track Page Layout

1. the left import/sidebar column stays in its current place
2. the right workspace is split vertically:
   - top main area
   - bottom operation strip
3. the top main area is split horizontally:
   - left results-first information panel
   - right map/track editor
4. users can drag each splitter handle to resize panels during the current session
5. on next launch, the layout returns to the default proportions

### Track Alignment Gestures

When the editor is in `view` mode:

1. left-drag on empty space moves the transformed track layer
2. `Ctrl + wheel` scales the transformed track layer
3. right-drag rotates the transformed track layer
4. arrow buttons perform smaller, more precise translation nudges than mouse dragging
5. zoom-in / zoom-out buttons perform smaller, more precise scale changes than mouse wheel input

When the editor is in `start_finish` or `sector` mode:

1. the cursor remains appropriate for drawing/editing lines
2. line placement and endpoint dragging still target the transformed track layer correctly
3. empty-space pan/rotate gestures should not interfere with line drawing

### Background Image Behavior

1. importing a background image makes it fill the editor view as the fixed visual reference
2. the background image is no longer the moved/scaled/rotated object
3. background opacity remains adjustable
4. clearing the background does not delete timing lines or transform state

## Persistence

No new persistence document shape is required.

Project files will continue to save:

1. track-definition timing lines
2. `background_image_path`
3. `DisplayTransform`

The key change is semantic:

1. existing transform fields now represent the edited overlay track layer
2. splitter sizes are not saved
3. temporary UI proportions reset on each fresh application launch

## Error Handling

1. if the background image fails to load, keep the previous background state unchanged and surface a clear status message
2. if no background image is loaded, the editor remains usable with the transformed telemetry/timing layer alone
3. if no analysis results are available yet, the results-first panel should show clear empty states such as `--`
4. if widget geometry becomes very small, clamp text size at the defined minimum font floor rather than letting labels disappear

## Testing Strategy

1. add track-editor tests that verify transform updates now move the track/timing layer rather than the background layer
2. add track-workspace tests for:
   - nested splitter construction
   - operation-strip control presence
   - zoom-in / zoom-out precision controls
3. add results-panel tests that verify current lap, best lap, and sector summaries surface in the new high-priority region
4. add regression tests ensuring background load/clear behavior still preserves timing lines and project-save state
5. add canvas-widget tests that verify resized widgets scale typography up and down while respecting a minimum font size
6. run focused suites first, then `tests/unit -q`

## Non-Goals

1. do not redesign the far-left import/project column
2. do not persist splitter dimensions between launches
3. do not reintroduce video alignment or preview-alignment workflows into the track page
4. do not convert overlay export into a bitmap-based rendering path
5. do not add multiple layered backgrounds or background editing beyond the existing single-image model
