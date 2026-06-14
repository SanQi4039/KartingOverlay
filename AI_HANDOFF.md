### 2026-06-14 Packaging Run - Export widget visual scale build

The Windows package was rebuilt from the current workspace after fixing export-time widget visual scaling for reduced overlay resolutions such as 720p.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,155,318` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,299,544` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,570,364` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists (`6,971,904` bytes)
4. `README-Packaged.txt` exists (`554` bytes)
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - Export widget visual scale consistency

This pass fixes the mismatch where exporting to 720p/1080p scaled widget geometry but left widget internals visually close to the original canvas size.

Implemented:

1. `kart_overlay/ui/export_workspace.py`
   - `ExportWidgetScaleInfo` now records `visual_scale`
   - export-only widget copies still scale `x`, `y`, `width`, and `height`
   - export-only widget copies now also receive `visual_scale = min(scale_x, scale_y)`
   - export manifests now include `widget_visual_scale`
2. `kart_overlay/widgets/base.py`
   - overlay widgets now have `visual_scale`
   - text helpers use `effective_font_scale = font_scale * visual_scale`
   - length helpers scale line/marker dimensions for export copies
3. `kart_overlay/widgets/hud_theme.py`
   - HUD metrics/layout can use export visual ratios below the editor font lower bound
   - default 100% editor rendering remains unchanged
4. Widget renderers
   - custom components that directly computed `hud_card_layout` now use `effective_font_scale`
   - updated: coordinates, G-force, heading, height, and mini-track widgets
5. `tests/unit/test_export_workspace.py`
   - added regression coverage that 720p export records and applies widget visual scale without mutating session layouts

Verification:

1. Red test before implementation:
   - `tests\unit\test_export_workspace.py::test_export_workspace_scales_export_widget_copies_without_mutating_session`
   - failed because exported speed widget had `visual_scale == 1.0` instead of `720 / 1080`
2. Green target test:
   - same test now passed
3. Related suite:
   - `tests\unit\test_export_workspace.py tests\unit\test_hud_theme_scaling.py tests\unit\test_canvas_workspace.py`
   - result: `41 passed in 0.76s`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

### 2026-06-14 Packaging Run - Project panel per-section help build

The Windows package was rebuilt from the current workspace after moving each left panel explanation under its own file section.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,154,207` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,288,335` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,569,714` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists (`6,971,904` bytes)
4. `README-Packaged.txt` exists (`554` bytes)
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - Project panel help text per section

This pass moves each left panel file-purpose explanation back into its own section after the user requested that every section keep its own description below the related controls.

Implemented:

1. `kart_overlay/ui/project_panel.py`
   - `_build_file_section` now accepts an optional `help_label`
   - telemetry, background image, and video help labels are added inside their matching sections instead of being grouped below the project section
   - the top-level left panel order remains: telemetry data -> background image -> video -> project
2. `tests/unit/test_project_panel.py`
   - updated layout regression coverage so each help label must live inside its matching section
   - kept coverage that help labels are no longer direct children of the top-level layout

Verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed
2. `$env:QT_QPA_PLATFORM='offscreen'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_project_panel.py -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex-panel-layout`
   - result: `9 passed in 1.13s`

### 2026-06-14 Packaging Run - Project panel import section layout build

The Windows package was rebuilt from the current workspace after restructuring the left project panel import sections.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,154,183` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,303,830` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,570,249` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists (`6,971,904` bytes)
4. `README-Packaged.txt` exists (`554` bytes)
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - Project panel import section layout

This pass restructures the left project panel operation area so all file inputs use the same pattern and appear in the requested order.

Implemented:

1. `kart_overlay/ui/project_panel.py`
   - added `background_path_input` so background images have their own file field
   - split the operation area into ordered sections:
     `遥测数据` -> `背景图` -> `视频` -> `项目` -> helper text
   - each file section now uses the same structure:
     title, file field, browse button, status label, and progress bar where applicable
   - browsing or loading a background image now synchronizes the background file field
2. `tests/unit/test_project_panel.py`
   - added regression coverage for section order
   - added coverage that background browsing updates the new background file field

Verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_project_panel.py -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `9 passed in 0.44s`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

### 2026-06-14 Packaging Run - Project helper text placement build

The Windows package was rebuilt from the current workspace after moving the telemetry/video/background helper text below the left-side operation area.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,153,423` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,283,207` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,568,184` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists (`6,971,904` bytes)
4. `README-Packaged.txt` exists
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - Project panel helper text placement

This pass moves the telemetry/video/background helper text out of the middle of the left operation flow.

Implemented:

1. `kart_overlay/ui/project_panel.py`
   - the three helper labels now appear below the main operation area, after the project save/load status
   - file inputs, import buttons, progress bars, and status labels remain grouped above as the primary operation flow
2. `tests/unit/test_project_panel.py`
   - added layout-order coverage to keep the helper text below the operation area

Verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_project_panel.py -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `8 passed in 0.55s`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

### 2026-06-14 Packaging Run - HUD centering and editor guidance build

The Windows package was rebuilt from the current workspace after the HUD centering, project helper text, track shortcut help, and canvas widget selection sync fixes.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,153,424` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,313,775` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,569,182` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists (`6,971,904` bytes)
4. `README-Packaged.txt` exists
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - HUD centering and editor guidance

This pass improves canvas/editor usability without changing export formats or telemetry calculations.

Implemented:

1. `kart_overlay/widgets/hud_theme.py`
   - shared HUD card titles now draw centered in the card
   - shared main values draw centered; value + unit pairs are centered as one visual group
   - shared footer text draws centered
2. `kart_overlay/widgets/coordinates_widget.py`
   - latitude, longitude, and GPS footer text now align to the card center
3. `kart_overlay/ui/project_panel.py`
   - added left-panel helper text explaining telemetry files, video files, and background images
   - the video helper explicitly mentions alignment and first-frame preview
   - the background helper explains using screenshots to place start/finish and sector lines
4. `kart_overlay/ui/track_workspace.py`
   - added right-side shortcut help in the bottom operation bar:
     `左键拖动改变轨迹位置`, `右键旋转`, `Ctrl+滚轮放大缩小`
5. `kart_overlay/ui/canvas_workspace.py`
   - preview-canvas widget selection now calls `select_widget()` directly
   - this fixes the case where selecting the same list item from the preview did not refresh `_selected_widget_key`, leaving settings controls unable to write changes until another component was selected

Verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_hud_theme_restyle.py tests\unit\test_project_panel.py tests\unit\test_track_workspace.py tests\unit\test_canvas_workspace.py -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `64 passed in 15.26s`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `220 passed in 53.68s`

### 2026-06-14 Packaging Run - Font scale upper limit removal build

The Windows package was rebuilt from the current workspace after removing the selected-widget font scale upper bound.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,152,473` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,311,903` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,567,791` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists (`6,971,904` bytes)
4. `README-Packaged.txt` exists
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - Font scale upper limit removed

This pass removes the selected-widget font scale upper bound while keeping the `70%` lower bound. Large saved font scales now remain intact, and the font `+` button can continue stepping past `180%`.

Implemented:

1. `kart_overlay/widgets/hud_theme.py`
   - `clamp_font_scale()` now only clamps below `MIN_FONT_SCALE`
   - removed the `MAX_FONT_SCALE` cap so explicit values such as `250%` are preserved
2. `kart_overlay/ui/canvas_workspace.py`
   - removed the UI-side `180%` cap from the selected-widget font increase button
3. Tests
   - added coverage for preserving large explicit font scales
   - added coverage for button stepping beyond `180%` and retaining the `70%` lower limit

Verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_hud_theme_scaling.py tests\unit\test_canvas_workspace.py -q`
   - result: `31 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `216 passed in 52.13s`

### 2026-06-14 Packaging Run - Independent widget font scale build

The Windows package was rebuilt from the current workspace after the independent per-widget font scale controls were added.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,152,549` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,282,178` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,568,678` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists
4. `README-Packaged.txt` exists
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-14 Incremental Update - Independent widget font scale controls

This pass separates widget text scale from widget container resize. It keeps the prior content-driven card sizing behavior, but adds an explicit per-widget font scale control so users can enlarge or shrink text without using the resize handles as an implicit font control.

Implemented:

1. `kart_overlay/widgets/hud_theme.py`
   - added `DEFAULT_FONT_SCALE`, `MIN_FONT_SCALE`, and `clamp_font_scale()`
   - `hud_card_metrics()` and `hud_card_layout()` now accept `font_scale`
   - title/value/unit/footer text keep their relative proportions while scaling together
   - progress bars, track graphics, and card backgrounds continue to use the actual widget rectangle rather than font scale
2. `kart_overlay/widgets/base.py`
   - `OverlayWidget` now stores clamped `font_scale`
   - `font_px()` follows explicit font scale instead of widget width/height
   - `length_px()` stays geometry-stable so graph/marker strokes do not scale with text
   - minimum widget dimensions can grow with font scale to avoid clipping when text is enlarged
3. `kart_overlay/widgets/*`
   - metric widgets pass `card_kwargs()` to static/full render paths and `text_kwargs()` to dynamic text paths
   - custom widgets such as coordinates, heading, G-force cards, G-force ball, mini-track, and height chart pass `font_scale` into `hud_card_layout()`
   - static-layer export remains consistent because static titles and dynamic values use the same scale
4. `kart_overlay/widgets/widget_factory.py`
   - default widget layouts now carry `font_scale=1.0`
   - widget construction passes saved `font_scale` into widget instances
5. `kart_overlay/ui/canvas_workspace.py`
   - added selected-widget `字体 -` and `字体 +` buttons with a `字体 N%` label
   - buttons step the selected widget by `10%`, clamped only to a `70%` lower bound
   - drag resize remains container-only; if enlarged text would no longer fit, the widget clamps up to the scaled minimum bounds
6. `kart_overlay/ui/project_panel.py`
   - project loading now restores saved `font_scale`
7. Tests
   - added coverage for explicit font scaling, canvas font buttons, widget factory propagation, and project save/load roundtrip

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_hud_theme_scaling.py tests\unit\test_canvas_workspace.py tests\unit\test_widget_factory_analysis.py -q`
   - result: `34 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_project_workflow_roundtrip.py -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `1 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `213 passed in 71.27s`

Remaining notes:

1. Font scale is per component and persists through project files.
2. Shrinking text does not auto-shrink the card; this avoids unexpected layout movement. Users can manually drag the card smaller afterward.
3. The implementation intentionally does not scale mini-track strokes, G-ball geometry, or chart bars with text scale.

### 2026-06-13 Packaging Run - Opacity and content-size clamp build

The Windows package was rebuilt from the current workspace after the widget opacity, content-driven size clamp, and default desktop export directory fixes.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe` (`2,149,304` bytes)
2. `dist\KartOverlay-Setup.exe` (`149,290,776` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,564,970` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists (`227,398,656` bytes)
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists (`227,193,344` bytes)
3. bundled `_internal\python312.dll` exists
4. `README-Packaged.txt` exists
5. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-13 Packaging Run - HUD static-layer export optimization build

The Windows package was rebuilt from the current workspace after the standard HUD static-layer export optimization.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe`
2. `dist\KartOverlay-Setup.exe` (`149,287,697` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,563,186` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists
3. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-13 Incremental Update - Standard HUD static-layer export optimization

This pass further optimizes transparent overlay export speed without changing export duration, frame count, alpha format, or widget layout semantics.

Root cause:

1. The renderer already supported a cached static layer, but only `MiniTrackWidget` opted into it.
2. Standard metric cards still redrew card backgrounds, borders, titles, and static scales every exported frame.
3. At 50 fps over a 25-minute export, that repeated static HUD chrome can be drawn roughly 75,000 times per enabled widget.

Implemented:

1. `kart_overlay/widgets/hud_theme.py`
   - split metric card drawing into `draw_metric_card_static()` and `draw_metric_card_dynamic()`
   - kept `draw_metric_card()` as the compatibility wrapper
   - retained the speed-card rule that hides the old km/h progress/tick visual
2. `kart_overlay/widgets/speed_widget.py`
   - opted into `supports_static_render`
   - static layer draws card background/title only once per renderer
   - dynamic layer draws the speed value per frame
3. `kart_overlay/widgets/timer_widget.py`
   - opted into `supports_static_render`
   - static layer draws card background/title once
   - dynamic layer draws lap time and progress per frame
4. `kart_overlay/widgets/altitude_widget.py`
   - opted into `supports_static_render`
   - static layer draws card chrome once
   - dynamic layer draws altitude value per frame
5. `kart_overlay/widgets/height_widget.py`
   - opted into `supports_static_render`
   - static layer draws card chrome, tick labels, and mini chart once
   - dynamic layer draws relative height value per frame
6. `kart_overlay/widgets/lap_summary_widget.py`
   - opted into `supports_static_render`
   - static layer draws card chrome once
   - dynamic layer draws lap count/progress per frame

Tests and verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_frame_renderer.py -q`
   - result: `7 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_frame_renderer.py tests\unit\test_hud_theme_restyle.py tests\unit\test_hud_theme_scaling.py tests\unit\test_export_execution.py tests\unit\test_export_workspace.py tests\unit\test_export_widget_layout_bridge.py -q`
   - result: `34 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
   - result: `205 passed in 75.84s`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

Remaining performance notes:

1. This reduces repeated Python/Qt painting work for common metric cards.
2. Full-frame RGBA byte conversion and ffmpeg pipe/encoder throughput still remain major costs for long transparent exports.
3. Dynamic-heavy widgets such as G-force bars, heading, coordinates, lap distance, sector status, and best-lap gap can be split in a future pass if profiling shows render time is still dominant.

### 2026-06-13 Packaging Run - Per-widget opacity build

The Windows package was rebuilt from the current workspace after the per-widget opacity/default-hidden HUD changes.

Command:

1. `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_windows_dist.py`

Generated artifacts:

1. `dist\KartOverlay\KartOverlay.exe`
2. `dist\KartOverlay-Setup.exe` (`149,285,430` bytes)
3. `dist\KartOverlay-windows-x64.zip` (`221,560,822` bytes)

Verification:

1. bundled `tools\ffmpeg\bin\ffmpeg.exe` exists
2. bundled `tools\ffmpeg\bin\ffprobe.exe` exists
3. portable `dist\KartOverlay\KartOverlay.exe` launched and stayed alive for 5 seconds, then was stopped intentionally

### 2026-06-13 Incremental Update - Per-widget HUD opacity and default hidden widgets

This pass implements the latest canvas/HUD behavior request without changing the export background model or broader page layout.

Implemented:

1. `kart_overlay/widgets/widget_factory.py`
   - default widget layouts now start with `enabled=False`
   - each default layout carries `background_opacity=96`
   - speed default height is now `86`, matching the simplified value-only speed card
   - widget construction passes per-widget opacity into the render widget copy
2. `kart_overlay/widgets/base.py` and HUD widgets
   - `OverlayWidget` now stores clamped `background_opacity` from 0 to 100
   - shared HUD card drawing accepts custom opacity while preserving the old default visual alpha
   - metric, coordinate, G-force, heading, and mini-track cards all use the same background opacity path
   - speed cards no longer draw the lower progress/tick bar in the shared metric renderer
3. `kart_overlay/ui/canvas_workspace.py`
   - added a selected-widget `背景透明度` percent control
   - selected widget visibility now defaults unchecked for new sessions
   - clicking the visible checkbox is the explicit action that enables a component
4. `kart_overlay/ui/project_panel.py`
   - project load now preserves saved `background_opacity` in widget layouts

Tests and verification:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_widget_factory_analysis.py tests\unit\test_canvas_workspace.py tests\unit\test_hud_theme_restyle.py tests\unit\test_project_workflow_roundtrip.py -q`
   - result: `36 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_widget_layout_bridge.py tests\unit\test_project_session_bridge.py tests\unit\test_project_panel.py tests\unit\test_frame_renderer.py tests\unit\test_export_workspace.py -q`
   - result: `24 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
   - result: `202 passed in 72.95s`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

Notes:

1. Existing projects that explicitly saved `enabled=True` still load visible.
2. New projects now start with every widget hidden, so export tests and workflows must enable at least one component before exporting.
3. The canvas background first-frame preview remains unchanged by this pass.

### 2026-06-12 Incremental Update

This pass implemented the scope from `本次修改指导总文档.md` around best-lap gap, track-line edit performance, bottom-bar spacing, and overlay export constraints.

1. best-lap gap data and UI
   - `kart_overlay/domain/timing/track_analysis.py`
   - `kart_overlay/ui/track_results_panel.py`
   - `kart_overlay/widgets/best_lap_gap_widget.py`
   - `kart_overlay/widgets/widget_factory.py`
   - `kart_overlay/ui/texts.py`
   - added centralized gap formatting/status semantics: `BEST`, `--`, `+x.xxx`, `-x.xxx`
   - negative delta is faster/green, positive delta is slower/red
   - sector gap now compares against the fastest lap's same sector, not the global theoretical-best sector
   - realtime gap uses precomputed lap distance profiles and interpolation instead of per-frame full telemetry scans
2. track editor drag responsiveness
   - `kart_overlay/ui/track_editor.py`
   - endpoint dragging keeps the existing preview-only path and recomputes on release
   - pending new-line preview now reuses a single `QGraphicsPathItem` instead of calling full `_render()` on every mouse move
   - added recompute/endpoint commit/pending preview timing logs
3. track workspace bottom operation bar
   - `kart_overlay/ui/track_workspace.py`
   - line/background/track groups now place titles next to their action controls
   - operation bar minimum height was reduced so the title/button cluster reads as one compact control group
4. overlay export resolution and performance
   - `kart_overlay/ui/export_workspace.py`
   - `kart_overlay/application/project_session.py`
   - `kart_overlay/application/export_service.py`
   - `kart_overlay/infrastructure/render/frame_renderer.py`
   - `kart_overlay/infrastructure/render/ffmpeg_exporter.py`
   - custom export width/height controls were removed from the export page
   - export now exposes only `原始视频尺寸`, `1080p`, and `720p`, preserving source aspect ratio
   - frame rendering reuses an RGBA buffer and handles non-tight image strides
   - export logs now include render/to-bytes/pipe-write timing summaries
   - `MiniTrackWidget` caches the static track path for the current geometry and only redraws the moving marker per frame

Verification evidence:

1. focused regression run
   - `D:\Anaconda_env\karting\python.exe -m pytest -q --basetemp=tmp_pytest_run\base -o cache_dir=tmp_pytest_run\cache tests/unit/test_track_analysis.py tests/unit/test_track_results_panel.py tests/unit/test_track_editor_visual_feedback.py tests/unit/test_track_workspace.py tests/unit/test_widget_factory_analysis.py tests/unit/test_ui_texts.py tests/unit/test_export_workspace.py tests/unit/test_project_session_bridge.py tests/unit/test_project_workflow_roundtrip.py tests/unit/test_export_execution.py tests/unit/test_ffmpeg_exporter.py`
   - result: `59 passed in 50.81s`
2. full unit suite
   - `D:\Anaconda_env\karting\python.exe -m pytest -q --basetemp=tmp_pytest_run\base -o cache_dir=tmp_pytest_run\cache`
   - result: `171 passed in 92.64s`
3. environment note
   - bare `pytest` and default `python -m pytest` are still not usable from this shell
   - sandboxed pytest hit temp-directory `PermissionError`, so the successful verification used the explicit project interpreter and an approved non-sandbox run

### 2026-06-11 Incremental Update B

This follow-up pass closed the three remaining tail items from the prior handoff:

1. export encoder visibility
   - `kart_overlay/application/export_service.py`
   - `kart_overlay/infrastructure/render/ffmpeg_exporter.py`
   - `kart_overlay/ui/export_workspace.py`
   - export preparation/results now carry an `encoder_label`
   - the export page now shows the selected encoder in preflight and completion status
2. reload-safe widget geometry
   - `kart_overlay/ui/project_panel.py`
   - project reload now restores `width`, `height`, and `enabled` for widget layouts instead of dropping size back to defaults
   - this fixes the preview/export geometry drift after manual resize + save + reload
3. HUD copy consistency
   - `kart_overlay/ui/texts.py`
   - `kart_overlay/widgets/lap_summary_widget.py`
   - `kart_overlay/widgets/best_lap_widget.py`
   - `kart_overlay/widgets/sector_state_widget.py`
   - `kart_overlay/widgets/mini_track_widget.py`
   - `kart_overlay/widgets/heading_widget.py`
   - `kart_overlay/widgets/g_force_widget.py`
   - `kart_overlay/widgets/hud_theme.py`
   - `lap_summary` display naming now matches the compact component intent as `圈数`
   - heading directions now use Chinese compass labels
   - several HUD card titles/labels are now explicit class-level text sources, which also makes regression tests easier

Important clarification:

1. the earlier “乱码源码” suspicion was not confirmed as widespread source corruption
2. runtime inspection showed `ui/texts.py` was already valid UTF-8
3. the real work here was copy consistency, not large-scale encoding repair

Verification evidence:

1. focused regression batch
   - `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_project_workflow_roundtrip.py tests\unit\test_project_panel.py tests\unit\test_project_session_bridge.py tests\unit\test_export_workspace.py tests\unit\test_export_workspace_errors.py tests\unit\test_export_widget_layout_bridge.py tests\unit\test_export_runner.py tests\unit\test_export_execution.py tests\unit\test_export_service.py tests\unit\test_ffmpeg_exporter.py tests\unit\test_ffprobe_service.py tests\unit\test_ui_texts.py tests\unit\test_hud_theme_restyle.py tests\unit\test_heading_widget.py tests\unit\test_g_force_widget.py tests\unit\test_mini_track_widget.py tests\unit\test_canvas_workspace.py tests\unit\test_frame_renderer.py tests\unit\test_track_workspace.py tests\unit\test_track_analysis.py tests\unit\test_track_results_panel.py tests\unit\test_track_inspector_panel.py -q`
   - result: `94 passed`
2. full unit suite
   - `D:\Anaconda_env\karting\python.exe -m pytest -q`
   - result: `157 passed in 59.97s`
3. compile check
   - `D:\Anaconda_env\karting\python.exe -m compileall kart_overlay tests`
   - result: passed

### 2026-06-11 Incremental Update C

This pass implements the latest UI grouping and export-stability feedback:

1. track workspace controls
   - line operations are grouped under `线操作`
   - background image import moved to `ProjectPanel`, next to telemetry import
   - track workspace background controls now focus on clear, opacity, reset alignment, and transform nudges
   - background opacity defaults to `100%`
   - right-drag rotation direction is reversed
2. canvas component visibility
   - the visible duplicate `隐藏组件` button is no longer placed in the controls layout
   - the `显示组件` checkbox remains the explicit visible toggle
   - keyboard `Delete` now hides the selected component by writing `enabled=False`, preserving position and size
3. HUD simplification
   - numeric HUD widgets now render only the primary value
   - G-force, heading, and mini-track components keep their main visual subject but drop small title/subtitle chrome
4. MOV export stability
   - transparent MOV export now stays on CPU `prores_ks` with `yuva444p10le`
   - the previous automatic `prores_ks_vulkan` preference is superseded because the Vulkan encoder can stall after the first frame on current Windows FFmpeg builds

Verification evidence:

1. focused regression batch
   - `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_ffmpeg_exporter.py tests\unit\test_canvas_workspace.py tests\unit\test_track_workspace.py tests\unit\test_project_panel.py tests\unit\test_project_workflow_roundtrip.py tests\unit\test_hud_theme_restyle.py tests\unit\test_g_force_widget.py -q`
   - result: `54 passed`
2. full unit suite
   - `D:\Anaconda_env\karting\python.exe -m pytest -q`
   - result: `163 passed in 58.44s`
3. compile check
   - `D:\Anaconda_env\karting\python.exe -m compileall kart_overlay tests`
   - result: passed

### 2026-06-11 Packaging Run

The Windows package was rebuilt from the current workspace:

1. command
   - `$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe'; D:\Anaconda_env\karting\python.exe scripts\build_windows_dist.py`
2. generated artifacts
   - `dist\KartOverlay\KartOverlay.exe`
   - `dist\KartOverlay-Setup.exe` (`149,448,249` bytes)
   - `dist\KartOverlay-windows-x64.zip` (`221,827,170` bytes)
3. bundled runtime checks
   - `ffmpeg.exe` and `ffprobe.exe` are present under `dist\KartOverlay\tools\ffmpeg\bin`
   - required Conda DLLs are present under `dist\KartOverlay\_internal`
4. smoke verification
   - portable `dist\KartOverlay\KartOverlay.exe` launched and stayed running for 5 seconds
   - the smoke process was then stopped intentionally
5. environment note
   - Inno Setup was already installed via winget under `C:\Users\Z\AppData\Local\Programs\Inno Setup 6\ISCC.exe`, but it was not on the script's default lookup path, so the build used `KART_OVERLAY_INNO_SETUP_PATH`

# AI Handoff

## 1. Current Goal

当前仓库的实现重心已经从“在应用内完成视频同步”转向“先完成透明遥测图层的生成，再在剪辑软件中手动对齐”。现阶段核心目标是继续稳定这个 overlay-first 的桌面工作流：导入遥测、编辑赛道线与背景图、调整画布组件、导出透明 `MOV ProRes 4444`，并补齐 Windows 分发路径。  
从代码和 README 的真实状态看，主流程已经具备可运行骨架，当前边界不再是“有没有架构”，而是“清理历史分支、收敛 UI/文档、验证打包链路”。  
不确定项：下一优先级究竟是继续做 UI/产品打磨，还是优先完成 Windows 安装包实机验证，仓库内没有主理人最新明确指令。

### 2026-06-11 Phase 4 Update

- Export now uses direct raw-frame piping into `ffmpeg` instead of writing PNG intermediates to disk.
- The active project workflow no longer stores or restores sync state through `ProjectSession`, `ProjectDocument`, `ProjectRepository`, or `ProjectPanel`.
- Export range handling is now fixed to `full_telemetry`, matching the current overlay-first product path.
- Remaining sync-domain helper modules are dormant only; they are no longer part of the active session/export/save-load chain.

### 2026-06-11 Phase 5 Update

- The last active UI copy gaps in the final workflow path have been tightened, including localized preview-time feedback and explicit Chinese confirm/cancel buttons in `ExportDialog`.
- `TrackEditor` no longer accepts the removed `sync_pick` mode through the active API.
- The dormant sync helper modules have now been deleted, so the current repository no longer keeps that compatibility tail in executable code.

### 2026-06-11 Phase 6 Update

- The Windows installer now targets a per-user install location under `{localappdata}\Programs\KartOverlay`, which removes the earlier elevation requirement from smoke verification.
- `packaging/installer.iss` now declares `PrivilegesRequired=lowest`, and the packaging test suite asserts that contract directly.
- Real Windows distribution verification has been rerun successfully across build, portable app launch, silent installer execution, and installed app launch.

### 2026-06-11 Phase 7 Update

- The HUD-only implementation phase has started landing without touching the main application UI layout.
- `widget_factory` now carries an explicit non-overlapping default HUD geometry baseline for the default `1280x720` canvas.
- `TelemetryInterpolator` now normalizes invalid heading values, preserves an internal acceleration-source marker at frame level, and falls back to conservative estimated G-force values when acceleration channels are missing.
- `MiniTrackWidget` now renders a stronger broadcast-style current-position marker with halo plus an optional heading arrow when heading data is available.
- Shared HUD card metrics have been tightened, and `CoordinatesWidget` has been reduced to a smaller tertiary footprint.
- Added regression coverage for HUD geometry, heading safety, G-force estimation, mini-track arrow behavior, and preview/export hidden-state parity.

## 2. Repository Status

- 2026-06-10 补充：本次已清理工作区中的缓存、构建输出和临时导出目录，当前顶层已不再保留 `build/`、`dist/`、`.pytest_cache/`、`tmp_export_frames/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`、`tmp_ui_export/`。
- 2026-06-10 补充：递归 `__pycache__/` 目录已清理完成；随后进一步确认 `.superpowers/` 内 pid 均为死进程后，整个 `.superpowers/` 目录也已删除。
- 2026-06-10 补充：`.gitignore` 已追加 `.superpowers/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`，用于减少后续重复噪声。

- 当前分支：`main`（来自 `git status --short --branch`）。
- `git status` 摘要：
  - 1 个已跟踪文件被修改：`docs/superpowers/specs/2026-06-09-track-visual-feedback-and-windows-packaging-design.md`
  - 存在大量未跟踪文件，包括：`README.md`、`requirements.txt`、`.gitignore`、`.env.local.example`、`kart_overlay/`、`packaging/`、`scripts/`、`tests/`、`docs/superpowers/plans/`、多个设计文档、样例数据和临时输出目录。
- 是否存在未提交修改：是。
- 是否存在未跟踪文件：是，且数量较多。
- 当前工作区是否干净：否。
- 备注：
  - 当前仓库并不是“少量增量修改”，而是“只有少量已跟踪 diff，但主体应用代码仍未加入版本控制”的状态。
  - `git diff` 只显示了一个已跟踪设计文档的增量更新；大量核心代码因尚未跟踪，不会出现在 `git diff` 中。

## 3. Modified Files

以下仅列出已核查到的关键文件与模块，完整未跟踪列表以 `git status` 为准。

### 已跟踪变更

- `docs/superpowers/specs/2026-06-09-track-visual-feedback-and-windows-packaging-design.md`：新增了一段 `Incremental Update 2026-06-09`，把实现状态补充到设计文档中；这说明设计文档仍在被当作演进记录使用，后续更新文档时不要粗暴覆盖历史内容。

### 仓库根目录与说明文件

- `README.md`：当前最完整的进度总览，记录了从架构骨架、遥测导入、赛道编辑、画布、导出、打包，到 2026-06-10 results-first 布局的连续增量状态；后续接手时应先对照它和实际代码是否继续一致。
- `requirements.txt`：定义当前 Python 依赖（`pytest`、`numpy`、`pandas`、`gpxpy`、`PySide6`、`pyinstaller`）；影响本地验证、GUI 运行和打包。
- `.gitignore`：当前忽略了 `build/`、`dist/`、部分缓存和局部导出目录，但没有覆盖 `.superpowers/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`、样例数据等，导致工作区噪声偏大。
- `.env.local.example`：提供本地环境变量示例；真实 `.env.local` 已存在但未跟踪，属于本地配置边界。

### 应用入口与共享状态

- `kart_overlay/ui/main_window.py`：当前主窗口只保留左侧 `ProjectPanel` 和中间标签页区域，标签页为 `Track / Canvas / Export`；说明旧的独立状态列和旧同步页已不在主壳层。
- `kart_overlay/application/project_session.py`：集中维护遥测、视频、赛道定义、分析结果、组件布局和导出设置，是跨页面共享状态的核心边界；后续改动如果破坏这里，影响范围会直接波及整个工作流。
- `kart_overlay/domain/project.py`：项目文档结构定义，仍保留 `sync` 字段；这与当前“移除主同步流程”的方向形成了历史兼容层。

### 项目导入/保存/加载

- `kart_overlay/ui/project_panel.py`：负责导入遥测、导入视频、保存项目、加载项目；会把背景图路径、赛道定义、组件布局、导出设置写入项目文件，并在加载时重新导入遥测和视频。
- `kart_overlay/infrastructure/persistence/project_repository.py`：使用 JSON 持久化 `ProjectDocument`，实际写入边界较清晰；影响项目文件的稳定性和兼容性。

### 赛道编辑与分析

- `kart_overlay/ui/track_workspace.py`：当前赛道页是 results-first 布局，包含结果面板、编辑器和底部操作条；负责把编辑器分析结果回写到共享 session。
- `kart_overlay/ui/track_editor.py`：实现背景图加载、起终线/分段线编辑、拖拽端点、实时重算、背景固定/轨迹层变换、缩放和平移，是当前业务最敏感的 UI 逻辑文件之一。
- `kart_overlay/ui/track_results_panel.py`、`kart_overlay/ui/track_inspector_panel.py`：承载圈速、分段和状态信息展示；影响当前“结果优先”的交互方向。
- `kart_overlay/domain/timing/*.py`：圈速、分段、穿线和分析汇总逻辑；这些模块当前已有测试覆盖，属于稳定核心。
- `kart_overlay/domain/track/models.py`：定义 `DisplayTransform`、`TimingLine`、`SectorLine`、`TrackDefinition`；当前 transform 语义与旧设计稿存在历史切换，需要谨慎维护。

### 画布与组件渲染

- `kart_overlay/ui/canvas_workspace.py`：实现组件列表、坐标编辑、启用/禁用、预览时间轴，以及直接在预览面板中拖拽/缩放组件。
- `kart_overlay/widgets/*.py`：当前已有速度、计时、海拔、航向、G 值、圈速摘要、最佳圈、分段状态、坐标、小地图等组件；影响预览和最终导出的一致性。
- `kart_overlay/infrastructure/render/frame_renderer.py`：Qt 向量渲染出口；如果未来预览和导出出现不一致，这里是关键排查点。

### 导出与视频信息

- `kart_overlay/ui/export_workspace.py`：当前导出页已实现视频元数据读取、工具状态展示、导出预检、后台导出、进度、取消和日志预览；业务导出目标固定为透明 `MOV`。
- `kart_overlay/application/export_service.py`、`export_task_runner.py`、`export_events.py`：导出编排和后台任务层。
- `kart_overlay/infrastructure/render/ffmpeg_exporter.py`、`export_manifest.py`：生成 `ffmpeg` 编码命令和导出 manifest；影响最终交付资产格式。
- `kart_overlay/infrastructure/video/ffprobe_service.py`：读取视频尺寸、旋转和 FPS；README 已说明这里做过 Windows/编码兼容性加固。

### 打包与 Windows 路径

- `scripts/build_windows_dist.py`：当前 Windows 打包总入口；会调用 PyInstaller、复制 `ffmpeg/ffprobe`、复制 Conda 运行时 DLL、调用 Inno Setup、输出 zip。
- `packaging/kart_overlay.spec`、`packaging/installer.iss`：分别定义 PyInstaller 打包和 Inno Setup 安装器；这条链路存在，但本次未重新执行。
- `kart_overlay/app_paths.py`、`kart_overlay/packaging.py`：定义 `%LOCALAPPDATA%`、`Documents\KartOverlay Projects`、打包运行时工具目录等路径策略；影响安装版和开发态的行为边界。

### 测试与样例

- `tests/unit/*.py`：当前存在 123 个通过的单元测试，覆盖导入、分析、UI、导出、打包路径、项目 roundtrip 等关键模块。
- `test.gpx`、`test.vbo`：仓库内样例遥测文件；测试与手工验证依赖它们，修改会影响回归结果。
- `tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`：临时/验证产物目录，不应手工修改业务内容。

## 4. Completed Work

- 2026-06-11 补充：`Phase 3` 已开始落地，当前范围只覆盖 Canvas 侧组件可见性语义、尺寸标注和相关文案收口，没有进入导出基础设施或 sync 清理。
- 2026-06-11 补充：`CanvasWorkspace` 的可见 UI 已收口到 `显示组件` 勾选；键盘 `Delete` 会把当前组件写成 `enabled=False`，不会删除布局数据。
- 2026-06-11 补充：Canvas 左侧勾选语义已收口为 `显示组件`，和底层 `enabled` 状态保持一致，避免“按钮文案和实际行为相反”。
- 2026-06-11 补充：`CanvasPreviewWidget` 现在会在预览画布边缘绘制尺寸边框与宽高标注。
- 2026-06-11 补充：导出桥接已验证继续按 `enabled` 过滤隐藏组件，因此本轮没有引入额外兼容层。
- 2026-06-11 补充：`Phase 2` 已开始落地，当前范围只覆盖 Track 侧交互和结果面板，没有进入 Canvas、sync 清理或 ffmpeg 管道重构。
- 2026-06-11 补充：`TrackEditor` 现在在起终线/分段线首点之后会显示跟随鼠标移动的预览线，并在交互式两点成线后自动回到 `view` 模式。
- 2026-06-11 补充：`TrackWorkspace` 已新增逐点轨迹滑条、当前点索引标签、当前圈号标签，以及更细的平移/缩放/旋转微调按钮。
- 2026-06-11 补充：`TrackResultsPanel` 已新增可滚动圈速列表，并且会跟随当前选中轨迹点同步圈选择。
- 2026-06-11 补充：当前 timing domain 仍未提供显式“无效圈”标记，因此本轮只先把全量圈速列表和当前圈联动做完，未实现基于 invalid flag 的弱化样式。
- 2026-06-11 补充：`Phase 1` 已开始落地，当前只实现导入流程和导出文件命名状态，没有提前进入 track 交互或 ffmpeg 管道重构。
- 2026-06-11 补充：`ProjectPanel` 现在改为“选中文件后直接导入”，遥测和视频都去掉了额外导入按钮；重复选择同一路径也会重新导入。
- 2026-06-11 补充：项目流程面板新增遥测/视频导入进度条，当前实现是轻量级同步进度反馈，不是独立后台导入任务。
- 2026-06-11 补充：`ExportWorkspace` 新增导出目录选择和自定义文件名输入，导出时会把文件名规范化为 `.mov`，并把该状态写回 `ProjectSession.export_settings`。
- 2026-06-11 补充：项目保存/加载的 export roundtrip 已扩展到 `output_filename`，对应定向 pytest 已通过。

- 已完成一次安全范围内的工作区清理，只删除了缓存、构建产物、工具会话残留和临时导出目录，没有删除源码、文档、样例数据或本地环境文件。
- 已递归清理 `kart_overlay/`、`scripts/`、`tests/` 下的全部 `__pycache__/` 目录，减少了当前工作区噪声。
- 已删除 `.superpowers/` 会话残留目录，并把相关忽略规则补入 `.gitignore`，减少后续无关未跟踪文件反复出现。

- 已建立完整的 Python/Qt 桌面应用目录结构，包含 `ui / application / domain / infrastructure / widgets` 分层，且入口可定位到 `kart_overlay/ui/main_window.py` 与 `kart_overlay/main.py`。
- 已实现 GPX/VBO 导入主路径，README 与测试显示样例 `test.gpx`、`test.vbo` 已接入真实解析链路，统一归一化为 `TelemetryStore`。
- 已实现赛道定义与计时分析基础能力，包括起终线、分段线、圈速、分段结果、最佳圈与分析汇总，对应 `kart_overlay/domain/timing/` 与 `kart_overlay/ui/track_editor.py`。
- 已实现赛道编辑页的 results-first 布局，包含顶部结果/编辑双栏和底部操作条；说明“结果优先 + 可拖拽布局”的 UI 方向已经落地到代码。
- 已完成本地背景图工作流，背景图入口位于项目流程面板并靠近遥测导入；赛道页保留清除、透明度调整、持久化背景图路径，并把 `DisplayTransform` 用于轨迹层对齐。
- 已实现画布编辑器与矢量预览，支持组件启停、位置/尺寸修改、直接拖拽与缩放；当前组件集已超过 README 中列举的最小值。
- 已实现透明 MOV 导出工作流，包括视频元数据读取、导出预检、后台任务、进度、取消、日志和 manifest 写出；当前 UI 暴露的最终导出格式为 `mov_prores_4444`。
- 已实现项目保存/加载，能保存并恢复遥测路径、视频路径、赛道定义、背景图路径、组件布局和导出设置；说明当前工作流已经具备“可复用项目文件”的基础闭环。
- 已补入 Windows 分发相关脚本和安装器资源，但本次仅验证了脚本/测试存在，没有重新跑出新的安装包。
- 已执行全量 Python 验证：
  - `D:\Anaconda_env\karting\python.exe -m compileall kart_overlay scripts tests` 通过。
  - `D:\Anaconda_env\karting\python.exe -m pytest -q` 通过，结果为 `123 passed in 54.10s`。

## 5. Key Decisions

- 决策：当前主流程已转为 overlay-first，而不是在应用内完成视频同步。
  - 原因：README 的最新增量更新明确说明旧 `Sync` 页已从主壳层移除，导出统一回到 `full_telemetry`。
  - 影响：`kart_overlay/ui/main_window.py`、`kart_overlay/ui/export_workspace.py`、`ProjectSession`、项目保存逻辑、后续产品文档。
  - 待确认：是否彻底删除遗留的 `sync` 领域模型与保存字段，还是暂时保留兼容壳层。

- 决策：赛道背景图采用本地图片，不再依赖 Amap 或远程底图。
  - 原因：最新 2026-06-10 设计文档明确转向本地背景图，且当前 `track_workspace.py` / `track_editor.py` 已按本地图片工作流实现。
  - 影响：`track_editor` 背景图交互、项目文件中的 `background_image_path`、Windows 安装包分发策略。
  - 待确认：是否还需要彻底清理历史 Amap 相关文件和测试命名。

- 决策：当前轨迹对齐模型采用“固定背景图，移动/缩放/旋转轨迹层”。
  - 原因：`2026-06-10-track-editor-results-first-layout-design.md` 与 `tests/unit/test_track_editor_advanced.py` 都验证了这一最新语义，且 `track_editor.py` 的实现确实如此。
  - 影响：`DisplayTransform` 的语义、赛道编辑交互、项目文件兼容理解、后续文档说明。
  - 待确认：旧的 `2026-06-10-local-background-and-windows-installer-design.md` 仍写的是“移动背景图”，历史文档存在语义冲突，需要后续统一说明。

- 决策：跨页面状态通过 `ProjectSession` 统一传递，而不是页面之间直接互调。
  - 原因：当前已经有遥测、视频、赛道定义、分析结果、组件布局和导出设置的共享信号边界。
  - 影响：主窗口组装方式、项目保存/加载、导出默认值、画布/赛道页联动。
  - 待确认：若后续要清理 sync 历史代码，需要一起评估 `ProjectSession` 中的 sync 字段是否保留。

- 决策：Windows 安装态路径使用 `%LOCALAPPDATA%\KartOverlay` 与 `%USERPROFILE%\Documents\KartOverlay Projects`。
  - 原因：`app_paths.py` 与打包脚本已采用该策略，目的是把安装目录和用户数据目录分离。
  - 影响：安装器脚本、项目默认保存位置、运行时日志/缓存放置位置。
  - 待确认：是否需要再补“首次启动迁移/目录创建”方面的手工烟测。

## 6. Validation

```bash
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Select-Object -ExpandProperty FullName
```

结果：

- 通过；
- 当前无输出，说明工作区内已无残留 `__pycache__/` 目录。

```bash
git status --short --branch
```

结果：

- 通过；
- 清理后已确认 `build/`、`dist/`、`.pytest_cache/`、各类 `tmp_*` 目录以及 `.superpowers/` 均不再出现在工作区顶层。

```bash
Get-ChildItem '.superpowers' -Recurse -Filter 'server.pid' | ForEach-Object { (Get-Content $_.FullName -Raw).Trim() }
```

结果：

- 通过；
- 已读到 3 个历史 pid 值和 1 个空 pid 文件，说明目录内主要是会话残留。

```bash
Get-Process -Id 11960,34984,34096
```

结果：

- 未通过 / 等价确认失败；
- 实际通过 `Get-Process -Id <pid> -ErrorAction SilentlyContinue` 核查后，这 3 个 pid 均不存在，判断为死进程残留，因此 `.superpowers/` 被删除。

```bash
git status --short --branch
```

结果：

- 通过；
- 输出显示当前分支为 `main`，工作区不干净，存在 1 个已跟踪修改和大量未跟踪文件。

```bash
git diff --stat
```

结果：

- 通过；
- 仅显示 `docs/superpowers/specs/2026-06-09-track-visual-feedback-and-windows-packaging-design.md` 有 12 行新增、1 行删除。

```bash
git diff
```

结果：

- 通过；
- 已核实唯一 tracked diff 为上述设计文档的增量更新。

```bash
pytest -q
```

结果：

- 失败；
- 报错摘要：当前 shell 的 `PATH` 中没有 `pytest`，PowerShell 返回 `pytest is not recognized as the name of a cmdlet...`。

```bash
python -m compileall kart_overlay scripts tests
```

结果：

- 失败；
- 现象：当前 shell 默认 `python` 入口不可用，未得到有效编译结果；后续改用显式解释器执行。

```bash
D:\Anaconda_env\karting\python.exe -m compileall kart_overlay scripts tests
```

结果：

- 通过；
- 已成功遍历并编译 `kart_overlay`、`scripts`、`tests`。

```bash
D:\Anaconda_env\karting\python.exe -m pytest -q
```

结果：

- 通过；
- 输出摘要：`123 passed in 54.10s`。

## 7. Known Issues

- 问题：仓库工作区噪声较大，主体应用代码和测试当前仍未加入版本控制。

  - 现象：`git status` 显示 `kart_overlay/`、`packaging/`、`scripts/`、`tests/`、`README.md` 等大量未跟踪文件。
  - 依据：已执行 `git status --short --branch`。
  - 当前判断：这不是单一文件遗漏，而是整个项目主体尚未进入 Git 跟踪的状态；后续提交时极易混入无关内容。
  - 下一步建议：先明确“哪些目录应进入版本控制、哪些应忽略”，再分批整理提交。

- 问题：同步功能在 UI 层已被移出主流程，但 sync 领域模型和项目字段仍然保留。

  - 现象：主窗口只有 `Track / Canvas / Export`，但 `ProjectSession`、`ProjectDocument`、`ProjectPanel`、`tests/unit/test_sync_model.py` 仍保留 sync 相关结构。
  - 依据：`kart_overlay/ui/main_window.py`、`kart_overlay/application/project_session.py`、`kart_overlay/domain/project.py`、`kart_overlay/ui/project_panel.py`。
  - 当前判断：当前不是崩溃级问题，但属于历史分支残留，容易让后续接手者误以为 sync 仍是主路径。
  - 下一步建议：由主理人确认是否彻底清理 sync 残留；若暂时保留，需要在 README 和项目 schema 中明确说明用途。

- 问题：UI 中文化不彻底，部分赛道编辑页控件仍为英文硬编码。

  - 现象：`TrackWorkspace` 中存在 `Import Background`、`Replace Background`、`Clear Background`、`Reset Transform`、`Zoom +`、`Zoom -`、分组标题 `Mode / Background / Track Adjust / Line Actions` 等硬编码英文。
  - 依据：`kart_overlay/ui/track_workspace.py`。
  - 当前判断：功能不受影响，但与 README 中“中国化产品 UI”描述不完全一致。
  - 下一步建议：如果下一阶段做产品 polish，应统一收口到 `ui/texts.py` 文本边界。

- 问题：有一条通过中的测试没有真正验证“缩小后 scale 恢复”。

  - 现象：`tests/unit/test_track_workspace.py` 末尾断言为 `assert workspace.editor.display_transform.scale <= workspace.editor.display_transform.scale`，该断言恒为真。
  - 依据：已检查测试文件源码。
  - 当前判断：这是测试质量问题，不代表业务一定有 bug，但它削弱了对 `precise_zoom_out_button` 的回归保护。
  - 下一步建议：修正为和点击前或放大后的 scale 做对比，再重跑相关测试。

- 问题：历史设计文档对 `DisplayTransform` 语义存在冲突。

  - 现象：`2026-06-10-local-background-and-windows-installer-design.md` 仍描述“移动背景图”，而 `2026-06-10-track-editor-results-first-layout-design.md` 与代码实现已经转为“固定背景、移动轨迹层”。
  - 依据：已阅读两份设计文档，并核对 `track_editor.py` 与 `test_track_editor_advanced.py`。
  - 当前判断：当前实现方向明确，但文档历史存在分叉，容易误导后续维护。
  - 下一步建议：后续若更新设计文档，应显式标注旧方案已过期或被新方案替代。

## 8. Risks

- 当前 `.gitignore` 虽已覆盖 `.superpowers/` 和已知临时目录，但仍未覆盖未来可能新增的其他工具状态目录；如果继续使用同类插件，工作区仍可能再出现新噪声。

- 当前最大风险是误提交无关 diff。仓库主体代码、测试、样例和临时目录大量未跟踪，后续若直接 `git add .`，很容易把临时文件、设计文档和业务代码一次性混在一起。
- 打包链路虽有代码和测试覆盖，但本次没有重新执行 `scripts/build_windows_dist.py`，也没有验证 Inno Setup、`ffmpeg/ffprobe`、Conda DLL 在当前机器上的真实可用性；继续推进安装包工作时存在环境风险。
- 当前默认 shell 的 `python` / `pytest` 不可直接使用，必须依赖显式解释器 `D:\Anaconda_env\karting\python.exe`；如果后续接手者忽略这一点，会误判仓库“无法运行”。
- `DisplayTransform` 的业务语义已经切换，如果后续有人按旧设计稿去改背景图行为，可能会直接破坏当前测试通过的轨迹对齐模型。
- 项目文件会保存外部背景图路径；跨机器、移动目录或清理素材时，用户已有项目可能丢失背景图引用，尽管赛道线本身不会丢。
- 当前导出依赖 Qt 向量渲染 + FFmpeg 编码双路径；如果后续只改预览组件、不改导出组件构建，可能出现“画布预览正常、导出内容不一致”的回归。
- 仓库当前明显偏向 Windows 路径与安装器，跨平台运行没有承诺；若后续在非 Windows 环境继续开发，需要特别注意路径和打包假设。

## 9. Remaining Work

- [ ] 待办事项：确认是否保留 sync 相关领域模型、项目字段和测试。

  - 依赖条件：主理人确认“未来是否还会恢复应用内同步功能”。
  - 建议处理方式：先用 `rg -n "sync_model|SyncState|sync_service|sync_offset" kart_overlay tests` 做范围盘点，再决定保留兼容层还是整体清理。
  - 优先级：高。

- [ ] 待办事项：整理版本控制边界，减少当前未跟踪噪声。

  - 依赖条件：先区分“应纳入仓库的源码/测试/说明文件”和“应忽略的临时产物/本地状态”。
  - 建议处理方式：补充 `.gitignore` 或分批 `git add`，避免一次性引入无关目录。
  - 优先级：高。

- [ ] 待办事项：修正 `tests/unit/test_track_workspace.py` 中的无效缩放断言。

  - 依赖条件：无。
  - 建议处理方式：把 zoom-out 断言改为和点击前或 zoom-in 后的数值比较，再跑定向测试。
  - 优先级：中。

- [ ] 待办事项：决定 UI 文案是否继续统一中文化。

  - 依赖条件：确认当前阶段是功能收尾还是产品 polish。
  - 建议处理方式：优先把 `TrackWorkspace` 中硬编码英文迁移到 `ui/texts.py`，避免多语言边界继续分散。
  - 优先级：中。

- [ ] 待办事项：重新执行 Windows 打包烟测。

  - 依赖条件：当前机器已安装 Inno Setup，并提供可用的 `ffmpeg/ffprobe` 与 Conda 运行时 DLL。
  - 建议处理方式：用显式解释器运行 `scripts/build_windows_dist.py`，再检查 `dist/` 产物是否齐全且可启动。
  - 优先级：高。

## 10. Next Step

1. 先执行 `rg -n "sync_model|SyncState|sync_service|sync_offset" kart_overlay tests`，盘点遗留 sync 边界到底还有哪些文件。
2. 打开 `tests/unit/test_track_workspace.py`，修正 `precise_zoom_out_button` 的无效断言。
3. 用 `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_workspace.py tests/unit/test_track_editor_advanced.py -q` 重跑赛道编辑相关回归。
4. 如果主理人确认不再需要应用内同步，再清理 `ProjectSession`、`ProjectDocument`、`ProjectPanel` 中对应残留。
5. 完成任何改动后，重新更新本文件。

## 11. Do Not Touch

- `.env.local`：本地运行环境配置，当前未跟踪，不应在没有明确需求时修改或提交。
- `test.gpx`、`test.vbo`：当前测试和手工验证依赖的样例数据，除非是有意更新 fixture，否则不要改。
- `tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`：临时导出/烟测产物目录，不应手工编辑业务内容。
- `docs/superpowers/specs/*.md` 与 `docs/superpowers/plans/*.md`：这些文件兼具历史记录和当前参考作用，更新时应增量追加或显式标注过期，不要粗暴重写历史。
- `kart_overlay/domain/timing/*.py`：当前已被全量测试覆盖且属于计时核心，除非有明确缺陷或需求，不要顺手重构。

## 12. Suggested Verification Commands

```bash
git status --short --branch
D:\Anaconda_env\karting\python.exe -m compileall kart_overlay scripts tests
D:\Anaconda_env\karting\python.exe -m pytest -q
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_workspace.py tests/unit/test_track_editor_advanced.py -q
$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Path\To\ISCC.exe'; D:\Anaconda_env\karting\python.exe scripts\build_windows_dist.py
```

## 13. Handoff Summary

本次还额外完成了一轮工作区清理：已删除缓存、构建输出、临时导出目录、`.superpowers/` 会话残留和全部 `__pycache__/`，但没有动源码、样例数据和本地环境文件。  
为避免同类噪声反复出现，`.gitignore` 已补充 `.superpowers/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`。  
当前仓库已经不是“空壳原型”，而是一个拥有真实 Qt 界面、遥测导入、赛道编辑、画布编辑、透明 MOV 导出、项目保存/加载和 Windows 打包脚本的完整工作流雏形。  
本次核查确认：当前分支是 `main`，工作区不干净，只有 1 个 tracked 文档有 diff，但主体源码和测试大量处于未跟踪状态。  
最新实现方向已经从“应用内同步”收敛到“overlay-first 导出”，并采用“固定背景图、移动轨迹层”的赛道对齐模型。  
本次没有改业务代码，只新增本交接文档；验证方面，显式解释器下 `compileall` 通过，`pytest` 全量通过，结果为 `123 passed in 54.10s`。  
当前最重要的风险不是单个功能崩溃，而是版本控制边界混乱、sync 历史残留、打包链路尚未重新烟测。  
如果下一位接手者继续推进，建议先从 sync 残留盘点和无效测试断言修正开始，再决定是否进入打包实测或 UI 文案收尾。  
另外，更新设计/交接文档时应保留历史增量，不要把旧设计直接覆盖掉，因为当前 docs 仍承担实现演进记录的作用。
### 2026-06-11 Incremental Update

This pass completed three concrete slices:

1. track timing and lap-results fixes
   - `kart_overlay/domain/timing/track_analysis.py`
   - `kart_overlay/ui/track_results_panel.py`
   - the builder now emits `N + 1` timed segments for `N` sector lines, including the tail segment back to start/finish
   - `current_sector_name_at()` now reports the active segment, not the last completed one
   - the results panel now appends per-lap split text (`S1 / S2 / S3 ...`) into each lap row and allows horizontal scrolling
2. HUD mini-track live marker correction
   - `kart_overlay/widgets/mini_track_widget.py`
   - the moving dot and heading arrow now use the same track-bounds normalization as the rendered polyline, so the live point stays on the displayed path
3. export subprocess stability and acceleration groundwork
   - `kart_overlay/infrastructure/render/ffmpeg_exporter.py`
   - `kart_overlay/infrastructure/video/ffprobe_service.py`
   - `ffmpeg`/`ffprobe` now launch with hidden-window flags on Windows
   - `ffmpeg` logging no longer keeps long-running `stderr` buffered in a pipe
   - superseded: the exporter no longer prefers `prores_ks_vulkan`; transparent MOV output now stays on CPU `prores_ks` because the Vulkan path can stall after the first frame

Tests added or strengthened in this pass:

1. `tests/unit/test_track_analysis.py`
2. `tests/unit/test_track_results_panel.py`
3. `tests/unit/test_mini_track_widget.py`
4. `tests/unit/test_ffmpeg_exporter.py`
5. `tests/unit/test_ffprobe_service.py`

Verification evidence:

1. targeted regression run
   - `D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_ffmpeg_exporter.py tests\unit\test_ffprobe_service.py tests\unit\test_export_service.py tests\unit\test_export_execution.py tests\unit\test_export_workspace.py tests\unit\test_export_workspace_errors.py tests\unit\test_export_widget_layout_bridge.py tests\unit\test_project_workflow_roundtrip.py tests\unit\test_project_panel.py tests\unit\test_canvas_workspace.py tests\unit\test_frame_renderer.py tests\unit\test_track_workspace.py tests\unit\test_track_analysis.py tests\unit\test_track_results_panel.py tests\unit\test_track_inspector_panel.py tests\unit\test_mini_track_widget.py -q`
   - result: `74 passed`
2. full unit suite
   - `D:\Anaconda_env\karting\python.exe -m pytest -q`
   - result: `153 passed in 60.65s`
3. compile check
   - `D:\Anaconda_env\karting\python.exe -m compileall kart_overlay tests`
   - result: passed

Known remaining tail items after this pass:

1. export workspace status text still does not surface which encoder path was selected at runtime
2. broader export-geometry parity after manual resize + project reload is still only partially covered
3. several older UI files still contain legacy mojibake text and should be cleaned in a dedicated localization pass instead of mixed into timing/export work

### 2026-06-12 Incremental Update - Full-sequence export time-series lookup

This pass keeps full telemetry sequence export intact. It does not crop duration, skip frames, or limit the export range.

Implemented:

1. `kart_overlay/domain/telemetry/interpolator.py`
   - replaced per-frame linear scanning from the beginning of the telemetry samples with a cursor-backed lookup for monotonic export timestamps
   - added binary-search fallback for random/backward access, so timeline scrubbing and preview queries remain correct
   - preserved existing boundary behavior for empty stores, first sample, final sample, and post-end timestamps
2. `tests/unit/test_telemetry_interpolator.py`
   - added coverage proving sequential full-export access advances the cached sample index
   - added coverage proving random access remains correct after the cursor has advanced

Why this matters:

- previous full-sequence export lookup cost was effectively `frames * samples` in the worst case
- sequential export now advances through the telemetry series once, so lookup cost is close to `frames + samples`
- rendering and encoding cost still remain; this only removes repeated time-series search work

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_telemetry_interpolator.py -q`
   - result: `3 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_g_force_estimation.py -q`
   - result: `2 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_execution.py -q`
   - result: `3 passed`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_workspace.py -q`
   - result: `9 passed`
5. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
   - result: `187 passed in 50.87s`
6. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

Remaining performance work:

1. renderer-level static card/background caching is still not implemented
2. export still writes every full RGBA frame to ffmpeg, so transparent alpha formats can remain large and CPU-heavy
3. any further acceleration should be measured separately around frame rendering, byte conversion, and encoder input throughput

### 2026-06-12 Incremental Update - Track-analysis timeline lookup indexes

This pass continues the full-sequence export optimization. It still preserves the complete telemetry timeline and does not crop, skip, or window the export.

Implemented:

1. `kart_overlay/domain/timing/track_analysis.py`
   - `TrackAnalysisSummary` now precomputes crossing times, lap records by index, sector splits by lap, sector end times, sector names, and sector split lookup maps in `__post_init__`
   - `current_lap_number_at()`, `current_lap_time_at()`, `current_sector_time_at()`, and `current_sector_name_at()` now use indexed/bisect-based lookups instead of repeated per-frame scans and sorting
   - `lap_gap_to_best()`, `sector_gap_to_best_lap()`, and `best_lap_sector_times` now reuse precomputed maps where possible
2. `tests/unit/test_track_analysis.py`
   - added coverage proving the lookup indexes are built
   - added boundary coverage preserving the existing sector transition rule: at an exact sector end time, the current sector advances to the next segment

Why this matters:

- HUD widgets such as timer, lap distance, best-lap gap, and sector status query track-analysis state every rendered frame
- those queries previously walked crossings or sector splits repeatedly during full-sequence export
- export still renders all frames, but per-frame timing lookup work is now bounded by tuple/dict lookup and binary search

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_track_analysis.py -q`
   - result: `6 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_widget_factory_analysis.py tests\unit\test_lap_distance_widget.py tests\unit\test_hud_theme_restyle.py tests\unit\test_frame_renderer.py -q`
   - result: `15 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_execution.py tests\unit\test_export_workspace.py tests\unit\test_export_widget_layout_bridge.py -q`
   - result: `16 passed`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
   - result: `188 passed in 53.08s`
5. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

Remaining performance work:

1. static HUD card/background caching is still a separate renderer/widget-layer task
2. RGBA byte conversion and ffmpeg pipe throughput remain likely bottlenecks for long transparent exports
3. transparent format choice still dominates final file size; lookup optimization mainly reduces Python-side CPU overhead

### 2026-06-12 Incremental Update - Static render layer for mini-track HUD

This pass adds a small renderer-layer optimization without changing export duration, frame count, transparency format, or widget layout.

Implemented:

1. `kart_overlay/infrastructure/render/frame_renderer.py`
   - added optional static-layer caching for widgets that declare `supports_static_render = True`
   - static widgets render their fixed content once into an RGBA layer
   - each frame composites that cached layer, then calls the widget dynamic render path
   - widgets that do not opt in continue using the original `render(painter, frame)` path
2. `kart_overlay/widgets/mini_track_widget.py`
   - opted `MiniTrackWidget` into static rendering
   - static path draws card background, title, inner panel, and track path
   - dynamic path draws only the current marker and heading arrow
   - direct `render()` remains as static + dynamic for preview and existing tests
3. `tests/unit/test_frame_renderer.py`
   - added a probe widget proving static content is rendered once while dynamic content renders every frame
4. `tests/unit/test_mini_track_widget.py`
   - added coverage for the split static/dynamic mini-track render paths

Why this matters:

- the mini-track card and track polyline are expensive fixed geometry during a full export
- this avoids redrawing that fixed part for every frame while preserving the moving point and heading arrow
- broader HUD card caching remains possible later, but this pass keeps the opt-in boundary narrow

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_mini_track_widget.py -q`
   - result: `5 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_frame_renderer.py -q`
   - result: `4 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_hud_theme_restyle.py tests\unit\test_g_force_widget.py tests\unit\test_heading_widget.py tests\unit\test_lap_distance_widget.py tests\unit\test_widget_factory_analysis.py -q`
   - result: `15 passed`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_execution.py tests\unit\test_export_workspace.py tests\unit\test_export_widget_layout_bridge.py -q`
   - result: `16 passed`
5. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
   - result: `190 passed in 65.04s`
6. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

Remaining performance work:

1. other metric cards still redraw their card backgrounds and text every frame
2. RGBA byte conversion and ffmpeg pipe/encode throughput are still likely to dominate long transparent exports
3. exact before/after export timing should be captured with a representative 25-minute project before choosing the next optimization target

### 2026-06-13 Incremental Update - Canvas video first-frame reference

This pass changes only the canvas editing preview. It does not affect transparent overlay export, export background handling, widget layout coordinates, or project save data.

Implemented:

1. `kart_overlay/infrastructure/video/video_frame_extractor.py`
   - added `VideoFrameExtractor`
   - uses the configured `ffmpeg` binary to extract the first frame as PNG over stdout
   - decodes the frame into `QImage`
   - returns `None` for invalid image data and raises a clear `FileNotFoundError` if `ffmpeg` is missing
2. `kart_overlay/ui/canvas_workspace.py`
   - `CanvasPreviewWidget` now accepts an optional frame extractor for tests
   - preview background first draws the existing checkerboard fallback, then draws the cached first video frame into the canvas target rect when available
   - the first-frame image is cached by video path, so repaint does not rerun `ffmpeg`
   - cache is invalidated when the shared session video path changes
   - `CanvasWorkspace` passes the extractor through to the preview widget without changing normal construction
3. `tests/unit/test_video_frame_extractor.py`
   - added command-building, PNG decode, invalid-image, and missing-ffmpeg coverage
4. `tests/unit/test_canvas_workspace.py`
   - added coverage proving the preview draws the video first frame as the reference background
   - added coverage proving the cached first frame is reused until the video path changes

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_video_frame_extractor.py -q`
   - result: `4 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_canvas_workspace.py -q`
   - result: `19 passed`
3. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_project_panel.py tests\unit\test_project_session_bridge.py tests\unit\test_project_workflow_roundtrip.py -q`
   - result: `8 passed`
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_ffprobe_service.py tests\unit\test_packaging_runtime.py tests\unit\test_build_windows_dist.py -q`
   - result: `23 passed`
5. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
   - result: `196 passed in 66.26s`
6. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed

Remaining notes:

1. first-frame extraction currently happens synchronously on first preview paint for a new video path; it is cached afterwards
2. if the first extraction fails, the preview keeps the checkerboard fallback instead of blocking editing
3. a future polish pass could extract the first frame during video import and store it in the session if startup latency becomes noticeable

### 2026-06-13 Incremental Update - Widget opacity, content sizing, desktop export default

This pass addresses the canvas widget styling controls and export default path only. It does not change export encoding formats, telemetry calculation, or the existing hidden-by-default widget workflow.

Implemented:

1. `kart_overlay/widgets/hud_theme.py`
   - added `card_border_for_opacity()`
   - made card borders use the same opacity percentage as card fill, so `0%` background opacity now removes both fill and border
   - changed core HUD card metrics to fixed text sizing; resizing the widget no longer continuously scales title/value/unit fonts
2. `kart_overlay/widgets/base.py`
   - made `font_px()` and `length_px()` content-stable instead of deriving from widget container scale
   - added `minimum_dimensions()` / `minimum_size()` for content-driven resize clamps
3. `kart_overlay/widgets/speed_widget.py` and `kart_overlay/widgets/widget_factory.py`
   - tightened the speed widget default box to `136x72`
   - added `minimum_widget_dimensions()` so canvas resizing can clamp to each widget's content minimum
4. `kart_overlay/ui/canvas_workspace.py`
   - resize handles and apply-geometry now clamp width/height to widget minimum content dimensions
   - kept larger widths valid, so bars/charts can still use horizontal space while text stays fixed
   - restored the canvas control label to `背景透明度`
5. `kart_overlay/application/project_session.py`
   - default export output directory now resolves to the Windows Desktop shell folder when available
   - falls back to `~/Desktop`, then `D:/Desktop`, then the user home directory
6. Tests
   - added regression coverage for transparent fill+border pixels
   - updated HUD scaling expectations to fixed text metrics
   - added resize clamp coverage for canvas preview
   - added export default output directory coverage

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_hud_theme_restyle.py tests\unit\test_hud_theme_scaling.py tests\unit\test_canvas_workspace.py tests\unit\test_project_session_bridge.py tests\unit\test_widget_factory_analysis.py -q`
   - result: `42 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall kart_overlay tests`
   - result: passed
3. Initial full pytest attempts inside the sandbox failed because pytest could not create/list temp/cache directories in `C:\Users\Z\AppData\Local\Temp`, `.pytest_tmp`, or `C:\tmp`.
4. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex`
   - result: `209 passed in 71.75s`

Remaining notes:

1. The new resize clamp is based on widget class minimum dimensions, not live font-measured `QFontMetrics`; this keeps the fix stable and small, but a future editor polish pass could measure exact rendered text for every data state.
2. Width expansion remains allowed; fixed typography means large cards may show extra horizontal room, while trend/scale/minimap visuals can occupy that space.

### 2026-06-14 Incremental Update - Track line replacement and widget interaction robustness

This pass fixes four focused editor/runtime interaction issues. It does not change export encoding, telemetry parsing rules, widget layout serialization, or the hidden-by-default widget workflow.

Implemented:

1. `kart_overlay/ui/track_editor.py`
   - confirmed the start/finish line remains a single `TrackDefinition.start_finish` field
   - when a new start/finish line is committed, the editor selection now explicitly points to the new `start_finish` item
   - existing sector lines are preserved when replacing the start/finish line
2. `kart_overlay/ui/canvas_workspace.py`
   - added a selected-widget fallback that restores the current list item before applying opacity, visibility, font, geometry, or hide operations
   - Delete now hides the selected widget from list focus, preview focus, and geometry/opacity input focus
   - the hide operation still only sets `enabled=False`; it does not delete widget layout data
3. `kart_overlay/widgets/mini_track_widget.py`
   - doubled the mini-track current-position marker radius from 5 px to 10 px
   - marker radius continues to use `visual_scale`, so export/downscale paths preserve relative marker size
   - mini-track inner panel fill/border now follow widget background opacity, so `0%` removes that panel background as well
4. Tests
   - added coverage for replacing an existing start/finish line while keeping sectors
   - added coverage for opacity edits after preview selection is cleared
   - added coverage for Delete from preview and settings focus
   - added coverage for the larger, visual-scale-aware mini-track marker
   - added coverage for mini-track `0%` background opacity on the inner panel

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_canvas_workspace.py tests\unit\test_mini_track_widget.py tests\unit\test_track_editor_interactions.py::test_track_editor_replaces_existing_start_finish_with_new_line -q --basetemp=C:\tmp\video-tip-pytest-codex-current-green-3`
   - result: `37 passed`
2. Manual VBO chain with `D:\Desktop\test.vbo`
   - result: imported as `vbo`, `31565` samples, `1314.908` seconds
   - replacing start/finish produced `start_x=2.0`, `start_y=-6.0`, `sectors=1`, `start_finish_items=1`
3. Earlier broader related-suite attempt showed the remaining blocker is missing repository fixture `D:\Desktop\Video Tip\test.gpx`, which is referenced by several pre-existing tests.

Remaining notes:

1. Full repository pytest should be rerun after restoring or replacing the missing `test.gpx` fixture.
2. Delete is intentionally treated as hide for the currently selected widget and remains non-destructive to saved layout coordinates.

### 2026-06-14 Incremental Update - Cancelled export partial MOV cleanup

This pass fixes cancelled export residue. It does not change export codecs, transparency settings, frame rendering, or normal completed-export overwrite behavior.

Implemented:

1. `kart_overlay/application/export_service.py`
   - wraps manifest writing, frame streaming, and ffmpeg execution in a cancellation cleanup boundary
   - on `ExportCancelledError`, deletes the current request's output video path, including half-written `.mov` files
   - deletes the current request's `export_manifest.json` so the next export cannot read stale resolution/format metadata
   - preserves `export.log` and appends `[cancel_cleanup]` entries with deleted file names or cleanup errors
2. `kart_overlay/ui/export_workspace.py`
   - cancellation callback resets progress to `0`
   - clears `_active_output_path` and `_active_encoder_label` after cancellation
   - continues loading the cancellation log preview for diagnostics
3. Tests
   - added a regression test that simulates ffmpeg writing a partial `overlay.mov` before cancellation and verifies the partial video and manifest are removed
   - added UI callback coverage proving cancelled export state is cleared

Verification evidence:

1. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_service.py::test_export_service_cleans_partial_mov_and_manifest_when_cancelled tests\unit\test_export_workspace.py::test_export_workspace_cancel_callback_clears_active_output_state -q`
   - result: `2 passed`
2. `C:\Users\Z\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\unit\test_export_service.py tests\unit\test_export_workspace.py tests\unit\test_export_execution.py tests\unit\test_ffmpeg_exporter.py -q --basetemp=C:\Users\Z\AppData\Local\Temp\video-tip-pytest-codex-cancel`
   - result: `22 passed`

Remaining notes:

1. Cleanup is intentionally scoped to explicit cancellation only. Non-cancel failures still keep their output/log state for debugging.
2. If Windows keeps a half-written movie locked after ffmpeg termination, cleanup logs the deletion error in `export.log`; the current ffmpeg cancellation path waits for process exit before service-level cleanup.

### 2026-06-14 Incremental Update - Workspace cache cleanup

This pass removes generated files and local caches only. It does not delete source code, packaged release artifacts, project documentation, or the `tests` source tree.

Removed:

1. Python bytecode/cache directories
   - `kart_overlay/**/__pycache__`
   - `scripts/**/__pycache__`
   - `tests/unit/__pycache__`
2. Pytest caches and temporary directories
   - `.pytest_cache`
   - `.pytest_tmp`
   - `.pytest_tmp_run_da6ee3bd0a8c4ade97a5da8105e01bc4`
3. Build/test intermediate output
   - `build`
4. Old generated archive
   - `kart_overlay.zip`

Kept:

1. `dist/KartOverlay-Setup.exe`
2. `dist/KartOverlay-windows-x64.zip`
3. `dist/KartOverlay/KartOverlay.exe`
4. `tests` source files

Verification evidence:

1. `Get-ChildItem -Path kart_overlay,scripts,tests -Force -Recurse -Directory -Filter '__pycache__'`
   - result: no remaining `__pycache__` directories
2. `Get-ChildItem -Path kart_overlay,scripts,tests -Force -Recurse -File -Include *.pyc,*.pyo`
   - result: no remaining Python bytecode files
3. Top-level listing now contains only `.git`, `dist`, `docs`, `kart_overlay`, `packaging`, `scripts`, `tests`, config files, README, and project docs.
