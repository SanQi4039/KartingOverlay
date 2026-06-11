# Track/Canvas Map Interactions Design

## Goal

Upgrade the native Qt editing workflow so the user can:

1. resize overlay widgets directly with the mouse
2. see crisp vector-like widget previews instead of bitmap-looking scaled previews
3. keep importing video metadata for canvas sizing
4. align the basemap to the track by moving, scaling, and rotating the basemap layer only
5. use clearer, lighter timing-line visuals and more accurate editor interaction feedback

The core architectural rule for this change is:

`track telemetry and timing-analysis coordinates remain canonical; only the basemap display layer moves.`

## Current Problems

1. overlay widgets are rendered into a full `QImage` before preview scaling, so the preview looks rasterized when zoomed or resized
2. canvas widgets can be moved, but not resized with mouse handles
3. the track display model already stores `translate_x`, `translate_y`, `rotation_deg`, and `scale`, but the editor does not expose a complete basemap interaction model that uses them
4. the current start/finish and sector lines rely on text labels and thick dashed pens, so they are harder to distinguish cleanly
5. the editor still uses a hand-style interaction feel while drawing lines, which is inaccurate for line-placement work
6. basemap failures are surfaced only as “response is not image”, without enough evidence to distinguish API errors from image-decoding failures

## Chosen Approach

The implementation will use four focused changes:

1. **Canvas vector preview path**
   - Keep `FrameRenderer -> QImage` for export.
   - Add a preview-only direct painter path in `CanvasPreviewWidget` so widgets are drawn live with `QPainter` into the preview surface instead of scaling one pre-rendered bitmap.
   - Add resize handles around the selected widget and write geometry changes back into session layout state.

2. **Basemap-only display transform**
   - Continue treating telemetry and timing lines as canonical scene geometry.
   - Apply `TrackDefinition.display_transform` only to the basemap item.
   - Support left-drag to move the basemap, `Ctrl+wheel` to scale it, right-drag to rotate it, and sidebar arrow buttons for micro-adjustment.
   - Persist all transform edits through the existing project save/load path.

3. **Timing-line visual and interaction cleanup**
   - Remove timing-line text labels.
   - Render start/finish as a black/white checker pattern.
   - Keep sector lines as colored thin lines.
   - Make selected lines visibly highlighted and preserve wide hit areas even when the visible line becomes thinner.
   - Switch the cursor to a crosshair while drawing lines and avoid map-pan cursor during line placement.

4. **Basemap request investigation and hardening**
   - Capture richer failure context from static-map responses.
   - Convert GPS coordinates to Amap coordinates before requesting the static basemap.
   - Surface decoded API failure messages when the response is JSON instead of an image.

## Components

### Canvas Preview

Files involved:

- `kart_overlay/ui/canvas_workspace.py`
- `kart_overlay/widgets/base.py`
- `kart_overlay/widgets/*`

Responsibilities:

1. render selected-widget outlines and resize handles
2. perform direct widget painting into the preview surface
3. support mouse drag for move and corner/edge drag for resize
4. keep export rendering unchanged

The preview widget will compute a canvas-to-preview transform, paint the checkerboard background, then invoke each overlay widget’s `render(...)` method inside painter transforms that preserve vector quality on screen. Resize handles will be preview-only controls and will write width/height/x/y back into session widget layouts.

### Basemap Interaction

Files involved:

- `kart_overlay/ui/track_editor.py`
- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/domain/track/models.py`
- `kart_overlay/ui/project_panel.py`

Responsibilities:

1. keep track lines and telemetry path in scene coordinates
2. apply translation / scale / rotation only to the basemap item
3. expose micro-adjust buttons in the left sidebar
4. persist transform state through project save/load

The basemap item becomes the only object that receives the stored display transform. Scene pan/zoom is separated from basemap alignment behavior: non-line left drag adjusts the basemap transform, `Ctrl+wheel` scales the basemap around its center, and right drag rotates it.

### Timing-Line Visuals

Files involved:

- `kart_overlay/ui/track_scene_items.py`
- `kart_overlay/ui/track_editor.py`

Responsibilities:

1. render start/finish as checkerboard
2. render sectors as thin colored lines
3. preserve large hit target via `shape()`
4. show selection/highlight clearly without label text

The visible pen will become thinner, but `shape()` will remain wider so selection stays easy. Selection state will change both line stroke and endpoint-handle visibility.

### Amap Request Path

Files involved:

- `kart_overlay/infrastructure/map/amap_services.py`
- `kart_overlay/ui/track_editor.py`

Responsibilities:

1. convert GPS center coordinates to Amap coordinates before static-map lookup
2. distinguish image response vs JSON API error
3. preserve a user-facing failure message with decoded API feedback

## Interaction Model

### Canvas

1. click widget body: select widget
2. drag widget body: move widget
3. drag handle: resize widget
4. selection outline and handles remain visible while selected

### Track Editor

1. line-draw modes use crosshair cursor
2. clicking existing line selects it and highlights it
3. dragging empty map space with left mouse moves only the basemap
4. dragging with right mouse rotates only the basemap
5. `Ctrl+wheel` scales only the basemap
6. sidebar arrows apply small translation deltas for micro-adjustment

## Persistence

No new top-level persistence document is needed.

Existing `TrackDefinition.display_transform` fields remain the persistence boundary:

1. `translate_x`
2. `translate_y`
3. `rotation_deg`
4. `scale`
5. `basemap_provider`

Project save/load already serializes these fields. The change is to make the editor truly use and update them.

## Error Handling

1. If coordinate conversion fails, the basemap status should show a clear failure reason and keep the editor usable.
2. If static-map response is JSON, parse the payload and surface the provider error message.
3. If image decoding fails despite image headers, surface “image decode failed” instead of the generic “response is not image”.
4. If the user has no telemetry geo-coordinates, keep the current “no geo coordinates” status.

## Testing Strategy

1. add widget-resize tests in `tests/unit/test_canvas_workspace.py`
2. add preview-path tests ensuring the canvas preview paints widgets directly rather than depending on bitmap background scaling
3. add basemap-transform tests in `tests/unit/test_track_editor_advanced.py` and `tests/unit/test_track_workspace.py`
4. add timing-line visual-state tests in `tests/unit/test_track_editor_visual_feedback.py`
5. add Amap service tests for coordinate conversion and non-image JSON failures
6. run the relevant focused suites first, then `tests/unit -q`

## Non-Goals

1. do not change export rendering away from `QImage`
2. do not alter raw telemetry sample coordinates
3. do not couple basemap alignment to timing analysis
4. do not reintroduce sync/video alignment workflow
