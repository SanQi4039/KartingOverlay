# Kart Overlay

Native Qt desktop application for building transparent telemetry overlay videos
from GPX/VBO data and source video files.

## Incremental Update: UI Grouping, Minimal HUD, and Stable MOV Export

This pass tightens the active workflow around the latest UI feedback:

1. Track line actions are grouped together in the track workspace operation bar: view mode, add start/finish, add sector, delete sector line, and reset start/finish now live in one `线操作` group.
2. Background image import moved next to telemetry import in `ProjectPanel`; the track workspace now keeps only background clear, opacity, and alignment controls.
3. Background images now default to full opacity (`100%`) instead of the previous semi-transparent default.
4. Right-drag rotation in the track editor now uses the opposite horizontal drag direction.
5. Canvas component hiding is controlled by the `显示组件` checkbox and the keyboard `Delete` key; `Delete` maps to `enabled=False` and preserves layout data.
6. HUD widgets have been simplified away from card-like copy: numeric widgets now render only the primary value, and graphical widgets no longer add small title/subtitle chrome.
7. MOV export now always uses CPU `prores_ks` with `yuva444p10le` for transparent ProRes 4444 output, even if `prores_ks_vulkan` is present, because the Vulkan encoder path can stall after the first frame on current Windows FFmpeg builds.

## Incremental Update: Phase 1 Direct Import And Export Naming

The first implementation phase for the new workflow refinement is now in place:

1. `ProjectPanel` no longer requires a second click to import telemetry or video.
2. Selecting a telemetry or video file now imports immediately, and selecting the same path again still re-runs the import.
3. The project workflow panel now shows lightweight import progress bars for both file types.
4. `ExportWorkspace` now carries both an output directory and a user-defined output filename.
5. Export filenames are normalized to `.mov` at launch time without changing the rest of the current export pipeline yet.
6. Extended export settings now round-trip through saved project documents via `ProjectSession`.

This keeps the current implementation deliberately narrow:

1. the ffmpeg pipe rewrite now lands in Phase 4
2. the active sync-layer cleanup now lands in Phase 4
3. no track-editor interaction changes yet

Those items were intentionally deferred at the time because they touched deeper application and infrastructure boundaries.

## Incremental Update: Phase 2 Track Interaction And Lap Review

The next track-focused phase is now in place:

1. `TrackEditor` now shows a live dashed preview line after the first click in both start/finish and sector drawing modes.
2. Finishing an interactive line creation now returns the editor to `view` mode automatically instead of leaving the add-line mode latched on.
3. `TrackWorkspace` now exposes checkable mode buttons and finer micro-adjust controls for translate, zoom, and rotation.
4. The track page now includes a point-by-point slider under the map so a user can step through every raw telemetry sample.
5. The slider updates the selected point marker and shows both the current point index and the lap number for that point.
6. `TrackResultsPanel` now includes a scrollable lap list and keeps the current lap selection synchronized with the chosen telemetry point.

This phase still deliberately stops short of the deeper export-side refactors:

1. the ffmpeg stdin pipeline now lands in Phase 4
2. the active sync-domain/session cleanup now lands in Phase 4
3. no invalid-lap classification yet, because the current timing domain still does not expose an explicit invalid-lap signal

That keeps the current work inside the track UI and shared-session boundary while preserving nearby behavior.

## Incremental Update: Phase 3 Canvas Visibility And Edge Guides

The canvas-focused phase is now in place:

1. `CanvasWorkspace` now exposes an explicit `隐藏组件` action instead of treating removal as destructive deletion.
2. Hiding a component now maps to `enabled=False`, which means the widget stays in the shared layout state and can be shown again later without losing position or size.
3. The existing visibility toggle is now framed as `显示组件`, so the checkbox meaning matches the underlying enabled-state bridge.
4. `CanvasPreviewWidget` now draws canvas edge guides and size annotations directly on the preview frame.
5. The export bridge still respects the same `enabled` state, so hidden widgets stay out of export output without needing a separate compatibility layer.

This phase remains intentionally narrow:

1. no widget deletion from project state
2. no export-pipeline refactor
3. no new overlay widget types

That keeps the behavior aligned with the confirmed product decision: component removal is a visibility change, not a destructive content operation.

## Incremental Update: Phase 4 Raw-Frame Export And Sync Cleanup

The export/persistence cleanup phase is now in place:

1. `ExportService` no longer writes `frame_*.png` intermediates before encoding.
2. `FrameRenderer` now exposes direct `RGBA` frame bytes for export, and `FfmpegExporter` now consumes those frames through stdin-based `rawvideo` piping.
3. Export frame scheduling is now endpoint-inclusive, so the overlay covers the full telemetry interval while keeping the final MOV duration aligned with telemetry timestamps.
4. `ExportWorkspace` and the background export runner now use the streamlined export contract without `frames_dir`.
5. `ProjectSession`, `ProjectDocument`, `ProjectRepository`, and `ProjectPanel` no longer carry sync state through the active save/load workflow.
6. Export range handling remains fixed to `full_telemetry`, which matches the current overlay-first product path.

This supersedes the earlier Phase 1 and Phase 2 notes that intentionally deferred the ffmpeg pipe rewrite and sync cleanup.

## Incremental Update: Phase 5 Final UI And Dead-Code Cleanup

The final cleanup phase is now in place:

1. `CanvasWorkspace` preview-time feedback is now localized instead of falling back to the old English label.
2. `ExportDialog` now exposes explicit Chinese confirm/cancel buttons instead of relying on platform-default `OK / Cancel` text.
3. `TrackEditor` no longer accepts the removed `sync_pick` mode through the active editing API.
4. The old dormant sync helper modules have been removed from the codebase, so the active product path no longer carries that dead code tail.

This phase closes the remaining cleanup loop after Phase 4:

1. active export, save/load, and editing flows are now aligned with the overlay-first product direction
2. remaining sync-first sections deeper in this README should be treated as historical implementation notes, not the current workflow contract

## Incremental Update: Phase 6 Windows Installer Verification

The final distribution tail is now closed:

1. `packaging/installer.iss` now installs per-user under `{localappdata}\\Programs\\KartOverlay` instead of requiring a machine-wide elevated install path.
2. The installer now declares `PrivilegesRequired=lowest`, which keeps silent install and smoke verification aligned with a normal user environment.
3. The Windows packaging tests now cover that installer contract directly.
4. Real packaging verification has been rerun end to end: build script, portable executable smoke, silent installer smoke, and installed executable launch smoke all pass on the current Windows environment.

## Incremental Update: Phase 7 HUD Overlay Restyle Foundation

The HUD-only execution phase is now in place:

1. The default overlay layout now uses a safer baseline geometry, including explicit default widths and heights, so the stock HUD no longer overlaps on the default `1280x720` canvas.
2. Telemetry frame production now normalizes invalid heading values and carries an internal acceleration-source flag, which supports safe fallback behavior without adding extra HUD copy.
3. When source files do not provide acceleration channels, the interpolator now produces a conservative estimated G-force from motion instead of leaving the G-force widget empty by default.
4. `MiniTrackWidget` now supports a broadcast-style current-position marker with halo and heading arrow when heading data is available.
5. Shared HUD card metrics have been tightened, `MiniTrackWidget` has been reduced to a more compact default height, and `CoordinatesWidget` has been demoted to a smaller tertiary footprint.
6. Added focused regression coverage for HUD geometry, mini-track marker behavior, heading safety, G-force estimation, and preview/export hidden-state parity.

This phase still deliberately stops short of the remaining non-HUD requests:

1. no track-results-panel redesign
2. no sector timing model rewrite
3. no export GPU acceleration or ffmpeg window suppression work yet

## Current Scaffold Status

The repository is initialized on the `main` branch and now contains the first
Scheme C architecture foundation:

1. dependency manifest for the target conda environment
2. runnable Python package root
3. native Qt main window shell
4. project document and atomic persistence layer
5. telemetry store domain contracts
6. FFprobe and parser adapter stubs

The next implementation phase will fill in real GPX/VBO parsing, timing
analysis, sync flow, preview binding, and transparent MOV export.

## Incremental Update: Real Telemetry Import

The project now supports importing the real `test.gpx` and `test.vbo` sample
files through the application service layer.

Current import behavior:

1. `GPX` parsing reads coordinates, timestamps, elevation, Garmin speed, and course.
2. `GPX` speed is normalized to `km/h`.
3. `VBO` parsing reads real data rows, time-of-day, speed, heading, and height.
4. `VBO` latitude/longitude are normalized from the Racebobo-generated sample
   coordinate layout used by the provided file.
5. Both formats are projected into local `x/y` coordinates and returned as one
   unified `TelemetryStore`.

The next step is to build timing analysis and track editing on top of this
normalized import path.

## Incremental Update: Track Definition And Basemap Boundary

The project now includes the first pure-domain track and timing building blocks:

1. `TrackDefinition`, `TimingLine`, `SectorLine`, and `DisplayTransform`
2. `LineCrossingDetector` with direction-aware crossing validation
3. `Amap` basemap service abstraction for future background loading in the native Qt track editor
4. `LapDetector` and `SectorDetector` for start/finish and sector crossing analysis
5. `TrackEditor` can now render imported telemetry plus track-definition lines in the native Qt UI
6. `TrackEditor` now supports a local two-click line creation flow for start/finish and sector definitions

Current map-provider decision:

1. `Amap` is the default basemap provider wired into the domain display configuration.
2. The provider API is abstracted in code first; live background fetching is not yet enabled inside the track editor.
3. Local runtime configuration is loaded from `.env.local`, which is ignored by git.
4. If service parameters need to change later, the provider and config boundaries are already isolated from the domain model.

## Incremental Update: Track Editor Workflow

The native track editor now has the first usable editing workflow:

1. load real telemetry into the scene
2. switch edit mode to `start_finish` or `sector`
3. click two points to create a line
4. refresh lap and sector analysis immediately after the line is committed

This is still an architecture-first implementation, so the next steps are to
add visible editing affordances, drag-to-adjust line endpoints, and surface the
analysis results in dedicated UI panels.

## Incremental Update: Interaction Layer

The interaction layer is now substantially more complete for the track workflow:

1. `TrackWorkspace` combines toolbar actions, the track editor, and an inspector panel.
2. `TrackInspectorPanel` shows lap-crossing count, lap count, best lap time, and sector summaries.
3. `TrackEditor` supports:
   - two-click line creation
   - programmatic endpoint movement
   - immediate lap/sector analysis refresh
   - optional Amap static basemap preview loading
4. The main window now hosts `TrackWorkspace` instead of a bare editor widget.

This means the next major implementation focus can shift toward export and
overlay rendering without needing to come back and rebuild the basic track
interaction architecture.

## Incremental Update: Export Foundation

The export foundation is now in place for the next phase of transparent video output:

1. `TelemetryInterpolator` can sample intermediate telemetry frames by time.
2. Minimal overlay widgets currently include `SpeedWidget` and `TimerWidget`.
3. `FrameRenderer` produces transparent ARGB frames with widget rendering.
4. `FfmpegExporter` builds a `MOV ProRes 4444` command using `prores_ks` and `yuva444p10le`.
5. `ExportService` can render a frame sequence and return the final FFmpeg command for video assembly.
6. `ExportDialog` provides the first local export configuration UI with format, fps, and output path inputs.

The next step is to connect the track-analysis results and widget layout data to
the export pipeline, then execute the FFmpeg process and write export manifests.

## Incremental Update: Export Workspace

The desktop app now includes a first local export workspace:

1. `ExportWorkspace` is wired into the main window as an `Export` tab.
2. It can accept loaded telemetry, render a short frame sequence, write a manifest, and run the configured export service.
3. The current UI is intentionally minimal and stable: output directory, fps, and export trigger.
4. If `ffmpeg` is missing from the environment, the workspace now reports a clear failure message instead of crashing.

This means the remaining export work is now mostly about improving correctness
and completeness rather than inventing the structure:

1. connect real video metadata and sync offsets
2. include richer widget sets and layout configuration
3. execute real FFmpeg exports end-to-end with robust logging and failure handling

## Incremental Update: FFmpeg Runtime And Video Metadata Wiring

The export chain now has a more realistic local-runtime foundation:

1. `ExternalToolsConfig` resolves `ffmpeg` and `ffprobe` from explicit env vars, `PATH`, or a few common local locations.
2. `FfprobeService` can now execute a real probe command and derive oriented export canvas dimensions from rotation metadata.
3. `ExportService` performs an `ffmpeg` availability preflight before rendering the full frame sequence.
4. `ExportWorkspace` now includes:
   - video file input
   - ffmpeg/ffprobe runtime status
   - video metadata read action
   - editable canvas size and overlay start offset
5. After reading a video file, the workspace defaults export FPS and canvas size from the probed metadata instead of hardcoding `1280x720 @ 60`.
6. Local binary paths can be pinned with `KART_OVERLAY_FFMPEG_PATH` and `KART_OVERLAY_FFPROBE_PATH` in `.env.local`.

This moves the app closer to the required business path of:

1. inspect a real source video
2. preserve oriented canvas dimensions
3. export a transparent overlay video with explicit placement metadata

## Incremental Update: Sync Workspace Foundation

The desktop app now includes the first native sync workflow slice:

1. `SyncModel` now owns the core `video_time <-> data_time` offset conversion.
2. `SyncService` builds a sync model from one manual reference point and validates whether the mapped data time is inside the telemetry range.
3. `TrackEditor` now supports a `sync_pick` interaction mode that selects the nearest telemetry sample on the rendered path.
4. `SyncWorkspace` is wired into the main window as a `Sync` tab and provides:
   - video file metadata read
   - manual video time input
   - telemetry-point picking on the local track view
   - computed sync offset and mapping preview
5. The current sync workflow is intentionally focused on correctness first: it establishes the timebase boundary cleanly before low-resolution video frame preview is introduced.

## Incremental Update: Sync Preview Workflow

The sync page now covers more of the real business flow instead of only the offset math:

1. `VideoPreviewFrameService` uses local `ffmpeg` to capture a low-resolution preview frame at an arbitrary video timestamp.
2. `SyncWorkspace` now includes a timeline slider and a preview frame panel for local scrubbing.
3. After reading video metadata, the timeline range is initialized from the real video duration and the first preview frame can be loaded locally.
4. After a sync point is applied, dragging the video timeline recomputes `video -> data` mapping and highlights the nearest telemetry sample on the track view.
5. Sync-page tool status now exposes both `ffmpeg` and `ffprobe`, which makes preview failures and metadata failures easier to diagnose.

This means the current sync workflow is now:

1. read video metadata
2. scrub the timeline and inspect low-resolution frames
3. pick a telemetry point on the track
4. apply the sync point
5. drag the timeline again and visually confirm that the mapped telemetry position follows the expected place on track

## Incremental Update: Cross-Page Session State

The app now has the first shared business-state layer between pages:

1. `ProjectSession` carries shared telemetry, video path, video metadata, and confirmed sync model state.
2. `SyncWorkspace` now publishes confirmed sync results into the shared session instead of keeping them local-only.
3. `ExportWorkspace` now listens to the shared session and automatically adopts:
   - telemetry source
   - video file path
   - oriented canvas size
   - export FPS default
   - overlay start offset
4. The main window now creates one shared session instance and injects it into both `Sync` and `Export` tabs.

This means the current business flow is materially closer to the intended desktop workflow:

1. confirm sync in the `Sync` tab
2. switch to `Export`
3. continue with already-populated export defaults instead of re-entering the same information

## Incremental Update: End-To-End Workflow Shell

The desktop app now has a first complete project-level workflow shell:

1. `ProjectPanel` provides native import entry points for telemetry and video at the main-window level.
2. `TrackWorkspace` now listens to the shared session and automatically loads telemetry imported from the project panel.
3. `WorkflowStatusPanel` shows whether telemetry, video metadata, and sync offset have been established.
4. The main window now orchestrates:
   - `ProjectPanel` on the left
   - `Sync / Track Editor / Canvas Editor / Export` tabs in the center
   - `WorkflowStatusPanel` on the right

This means the current local workflow is now:

1. import telemetry in the left project panel
2. import video in the left project panel
3. define track lines in `Track Editor`
4. confirm time alignment in `Sync`
5. switch to `Export` with carried-over defaults and export the transparent overlay

## Incremental Update: Canvas Layout And Project Reuse

The app now closes the gap between functional workflow and reusable workflow:

1. `CanvasWorkspace` is now a real tab instead of a placeholder and can edit shared widget positions for `speed` and `timer`.
2. `ProjectSession` now carries widget-layout state and track-definition state in addition to telemetry, video, and sync data.
3. `ExportWorkspace` now builds export widgets from the shared canvas layout instead of using hardcoded positions.
4. `TrackWorkspace` now publishes edited track definitions back into the shared session.
5. `ProjectPanel` now supports project save/load for:
   - telemetry source path
   - video source path
   - sync offset
   - track definition
   - widget layout state

This means the current reusable desktop workflow is now:

1. import telemetry and video
2. edit track lines
3. confirm sync
4. adjust canvas widget positions
5. save the project file
6. reopen the project later and recover the working state before exporting

The next meaningful completeness steps are less about workflow connectivity and more about product depth: richer overlay modules, stronger canvas preview fidelity, project save/load coverage for more UI preferences, and exporting track-derived overlay components.

## Incremental Update: DJI-Style Canvas Preview And Expanded Widgets

The canvas workflow is now much closer to a creator-facing dashboard editor instead of a plain coordinate form:

1. `CanvasWorkspace` now contains a live preview surface instead of only a widget summary list.
2. The preview uses the real `FrameRenderer` plus telemetry interpolation, so the canvas tab shows actual overlay rendering at a chosen preview time.
3. Widget selection is visible in the preview, and widget positions can be updated from both the control panel and direct dragging on the preview surface.
4. Clicking a widget in the preview now synchronizes the left-side component panel, coordinate editor, and enabled state.
5. Each widget can now be enabled or disabled directly in the canvas editor without losing its saved layout.
6. The preview can also use the current video source as a low-resolution background reference when available.

The widget style has been moved toward a DJI-like dashboard language:

1. translucent dark HUD cards
2. cyan accent bars and fine borders
3. high-contrast white numeric emphasis
4. compact modular information panels

The currently supported widget set now includes:

1. `speed`
2. `timer`
3. `altitude`
4. `heading`
5. `g_force`
6. `lap_summary`
7. `best_lap`
8. `sector_state`
9. `coordinates`
10. `mini_track`

These widgets are backed by values already available from the current GPX/VBO import path where possible:

1. `speed` from normalized telemetry speed
2. `timer` from current mapped data time
3. `altitude` from GPS/VBO elevation
4. `heading` from course/heading channels
5. `g_force` from longitudinal/lateral acceleration channels when present
6. `lap_summary` from start/finish crossing analysis
7. `best_lap` from lap-duration analysis
8. `sector_state` from configured sector crossings
9. `coordinates` from latitude/longitude
10. `mini_track` from projected local track points plus current position

This means the dashboard layer now covers both raw telemetry cards and basic timing-analysis cards in the same visual system, while still staying compatible with transparent overlay export.

## Incremental Update: MOV-Only Export Workflow Closure

The export layer now behaves more like a reusable project workflow instead of a thin FFmpeg trigger:

1. `ExportWorkspace` now exports the full telemetry overlay range only.
2. Export preflight now validates:
   - telemetry is loaded
   - fps and canvas size are valid
   - at least one overlay widget is enabled
3. The export page now shows the resolved preflight window in terms of telemetry start and export duration.

The output policy has also been tightened around your preferred delivery format:

1. final delivery remains `MOV ProRes 4444` with alpha only
2. no PNG sequence is exposed as a user-facing export target
3. the current implementation now streams raw `RGBA` frames directly into `ffmpeg`, so there is no temporary PNG render pass in the active export path

Project reuse now also includes export-page state:

1. output directory
2. fps
3. canvas width and height
4. export range mode
5. export format marker (`mov_prores_4444`)

This means the current business export path is now closer to the intended production workflow:

1. import telemetry and optional source video metadata
2. keep export settings in the saved project
3. export the full telemetry-driven overlay layer
4. reopen the project later and continue exporting without rebuilding the same export setup

## Incremental Update: Background Export And Timing Recalculation

The export page now behaves more like a real production tool instead of a blocking form:

1. export execution now runs through a background task runner instead of directly blocking the page
2. the export page now exposes:
   - progress bar
   - running status text
   - cancel action
   - log preview panel
3. render progress and encode progress are now emitted through explicit progress events rather than being inferred from the final result only
4. cancellation is now supported during:
   - frame rendering
   - ffmpeg MOV encoding

Track timing analysis is also now more deeply wired into the shared business state:

1. `TrackWorkspace` now publishes a shared track-analysis summary into `ProjectSession`
2. editing the start/finish line or sector lines now clears stale timing analysis first and then republishes recalculated results
3. recalculated results now include:
   - lap result
   - last lap time
   - best lap time
   - last sector split times
   - best sector split times
4. the track inspector now surfaces last/best lap and sector timing summaries directly instead of only crossing counts

The overlay layer also now consumes this richer timing state:

1. `TimerWidget` now renders current lap elapsed time rather than only raw global elapsed time when track analysis is available
2. `SectorStateWidget` now renders current sector elapsed time and can reference best known split timing from the recalculated analysis summary
3. widget building can fall back to rebuilding timing analysis from telemetry plus track definition when a project is reopened before the user re-enters the track page

This means the workflow is now tighter in the places that matter most for real karting review:

1. edit start/finish or sector lines
2. immediately force a fresh lap/sector timing recalculation
3. see updated totals and split times in the track workflow
4. export with a cancellable MOV-alpha background job and inspect logs without freezing the page

## Incremental Update: Visual Timing-Line Editing Feedback

The track editor now has a much more usable local interaction loop for karting users:

1. timing lines are now rendered as explicit editable scene items instead of passive dashed strokes
2. clicking an existing timing line now selects it directly, even while the page is still in line-edit mode
3. selected timing lines now expose endpoint handles and stronger visual emphasis
4. endpoint dragging previews the geometry change first and only triggers timing recalculation on release
5. `TrackWorkspace` now exposes a persistent status strip for mode, selection, and recalculation feedback
6. sector deletion and start/finish reset now clear stale shared timing state and republish fresh analysis results

This tightens the real business loop on the track page:

1. create or select a timing line
2. adjust or delete it with visible feedback
3. immediately see refreshed lap and sector timing state in the inspector and shared workflow

## Incremental Update: Windows One-Folder Packaging

The project now includes the first Windows packaging path:

1. a PyInstaller one-folder build entrypoint for the desktop app
2. packaged-runtime binary resolution that prefers bundled `ffmpeg.exe` and `ffprobe.exe`
3. a build script that stages the executable, copies the required video tools, and bundles key Conda runtime DLLs
4. a generated Windows zip package for easy transfer to another machine
5. packaged launch notes for Windows-only distribution

## Incremental Update: Chinese Product UI And Sticker HUD Restyle

The desktop product is now Chinese-first by default instead of staying in a mixed prototype state:

1. the main window now uses a custom frameless title bar with Chinese product title, drag support, minimize/maximize/close controls, and double-click maximize behavior
2. the core workflow pages now default to Chinese UI copy across:
   - main tabs
   - project import/save/load actions
   - sync-page status and mapping feedback
   - track-page mode and recalculation feedback
   - canvas editor controls
   - export dialog and export workspace status text
3. the app bootstrap metadata now also defaults to the Chinese product name `卡丁车数据叠层`

The overlay style has also moved away from heavy boxed cards toward a lighter telemetry-sticker direction:

1. HUD cards now render with transparent fill, cyan divider accents, italic white value emphasis, and reduced panel framing
2. default widget display names and rendered labels now use Chinese-facing wording such as:
   - `速度`
   - `当前圈`
   - `最佳圈`
   - `分段`
   - `赛道图`
3. canvas preview summaries now show Chinese widget names instead of internal widget keys
4. the export dialog now keeps the user-facing output policy aligned with the product requirement by exposing only `MOV ProRes 4444（透明）`

This keeps the current workflow chain intact while making the app materially closer to the intended customer-facing karting tool:

1. import telemetry and video
2. edit timing lines with visible Chinese feedback
3. preview and place Chinese telemetry widgets
4. export a transparent MOV overlay layer without exposing PNG-sequence delivery in the UI

## Incremental Update: Window And Sync Layout Stabilization

One practical UI usability pass has now been added on top of the Chinese-first shell work:

1. the desktop shell has been simplified back to the native Windows title bar, while keeping the Chinese window title
2. the main three-column application shell now reserves usable width for:
   - the project workflow panel
   - the center editing workspace
   - the right workflow status panel
3. the `视频同步` page splitter now assigns stable initial space to:
   - the left control and preview column
   - the center track-selection canvas
   - the right status summary column

This specifically fixes the class of layout failures where:

1. a large blank area appeared above the tabs
2. the custom title bar looked like an empty banner
3. the sync page track area was squeezed down to an unusable narrow strip

## Incremental Update: Resizable Main And Inner Splitters

The desktop layout now better supports practical resizing during editing:

1. the outer main application splitter once again keeps enough free width for dragging between:
   - project workflow panel
   - center workspace tabs
   - right workflow status panel
2. the `视频同步` page no longer lets long runtime-status paths force the whole page to an oversized minimum width
3. long tool-status and video-status labels in the sync and export pages now wrap instead of locking the layout width
4. splitter handles across the main shell and key editor pages are now wider, which makes them easier to grab with the mouse

This specifically addresses the class of problems where:

1. the left and right areas of the main window appeared fixed in place
2. inner editing columns felt impossible to drag
3. one long ffmpeg/ffprobe path could indirectly prevent the whole application from resizing normally

## Incremental Update: Canvas Workspace Resize Root Cause Fix

The remaining resize lock in the center workspace has now been fixed at its source inside the `画布编辑` page:

1. the canvas preview summary now wraps instead of forcing all widget positions into one extra-wide single line
2. the preview surface minimum size has been reduced to a still-usable 16:9 footprint, so it no longer blocks the outer shell from shrinking
3. the canvas editor control column and preview column now expose more realistic minimum widths to the splitter system
4. automated tests now verify both:
   - the canvas workspace keeps a bounded minimum width
   - the outer main splitter can actually move during a drag interaction

This specifically resolves the last class of issues where:

1. switching to `画布编辑` made the whole application feel non-resizable again
2. the main left/right panels looked visually draggable but did not move in practice
3. the canvas page's own inner divider also felt stuck because the page minimum width had already consumed the available space

## Incremental Update: Windows DJI Video Import Compatibility

The video metadata import path is now more robust against real-world action-camera files on Windows:

1. `ffprobe` output is now captured as raw bytes and decoded explicitly as UTF-8 instead of relying on the local Windows code page
2. empty `ffprobe` output now fails with a clear metadata error instead of cascading into a `json.loads(None)` crash
3. invalid JSON output and missing video-stream payloads now fail with explicit validation errors
4. rotation metadata can now be read from both classic `tags.rotate` values and `side_data_list` display-matrix entries

This specifically fixes the class of import failures where:

1. DJI or other camera metadata contained characters that broke `subprocess(text=True)` decoding on Chinese Windows systems
2. the UI surfaced a misleading `the JSON object must be str, bytes or bytearray, not NoneType` error even though the video file itself was valid
3. real videos existed on disk but still could not be imported because the parser assumed an ideal `ffprobe` response

## Incremental Update: Build Script Self-Bootstrap

The Windows packaging entrypoint is now easier to run from a local shell:

1. `scripts/build_windows_dist.py` now inserts the project root into `sys.path` before importing app modules
2. the packaging script can now be launched directly from the `scripts` directory without manually exporting `PYTHONPATH`
3. the behavior is covered by a regression test so the direct-run workflow stays stable

This specifically fixes the class of problems where:

1. running `python build_windows_dist.py` inside `scripts` failed with `ModuleNotFoundError: No module named 'kart_overlay'`
2. the build only worked when the caller already knew to set `PYTHONPATH` by hand

## Incremental Update: Auto Basemap Visibility In Track Editing

The track editing page now makes the map background materially more usable instead of hiding it behind fragile scene placement:

1. loading telemetry with latitude and longitude now auto-enables the basemap path in the track workspace
2. fetched Amap static imagery is now scaled to cover the local track bounds instead of being dropped into the scene at raw `640x480` pixel size
3. the editor scene rect now expands to include the basemap footprint, which keeps the map visible during normal view navigation

This specifically fixes the class of issues where:

1. the user imported real telemetry but saw no practical background map in the track editor
2. the static map request succeeded yet the result still felt unusable because it was not fitted to the track extent
3. track editing lacked the expected geographic context for placing start/finish and sector lines

## Incremental Update: Lighter Sticker HUD And Compact G-Force Module

The overlay widget layer has also been pushed closer to the supplied racing-sticker reference:

1. the shared HUD metric primitive now uses a lighter sticker-style label, cyan accent slash, and tighter typography instead of a dashboard-card composition
2. the `GForceWidget` is now a compact single-ball module rather than a full card with extra longitudinal/lateral subtitle text
3. the G-force ball now renders as a centered standalone instrument with only the magnitude and marker retained

This specifically fixes the class of issues where:

1. telemetry widgets still looked too much like generic boxed cards instead of lightweight motorsport overlays
2. the G-force component carried more panel chrome and text than needed for fast karting review
3. the overlay language did not feel close enough to the reference edge-sticker layout

## Incremental Update: Sync Removal And Full-Telemetry Export Simplification

The workflow has now been simplified around the actual production need: build the overlay layer first, then align it later inside the video editor instead of inside this desktop tool.

1. the old `视频同步` tab has been removed from the main shell, so the center workspace now focuses on:
   - `赛道编辑`
   - `画布编辑`
   - `导出视频`
2. the old sync-only video preview chain has been removed entirely, including:
   - sync-page preview frames
   - timeline scrubbing for manual sync
   - export-side sync offset controls
   - synced-video overlap range selection
3. the canvas page no longer exposes a video-reference background toggle, so it now previews the overlay layer itself instead of trying to preview source-video alignment
4. export behavior is now normalized to `full_telemetry` everywhere:
   - default session state
   - export workspace state
   - project reload normalization for saved export settings
5. the export page still supports reading source-video metadata for canvas sizing and FPS defaults, but no longer treats source video as a timing master
6. the track editor now records a concrete basemap status message, which lets the UI surface load failures such as a non-image map response instead of silently showing a blank background
7. the outer main-window splitter has also been rebalanced so the working center region gets more initial width and the right-side status area no longer steals so much space

This specifically fixes the class of issues where:

1. the app spent too much time on in-app video alignment even though the user planned to align the exported layer in Premiere, Resolve, or similar tools
2. loading video previews made the sync workflow feel slower and heavier than the actual overlay-editing job required
3. the export page still exposed sync-era controls even when the intended delivery was always the full GPX-driven overlay layer
4. the map could fail to appear with too little feedback about whether it was disabled, unavailable, or returning invalid content

## Incremental Update: Local Background Images And Windows Installer Paths

The track editor has now been fully decoupled from Amap and any remote map key requirement:

1. the old Amap/background-map workflow has been removed from the track-editing path
2. the track page now uses a local background-image layer instead, so users can import either:
   - satellite/map screenshots
   - schematic track diagrams
3. the imported background image can be:
   - moved with left drag
   - scaled with `Ctrl + mouse wheel`
   - rotated with right drag
   - nudged with `Up / Down / Left / Right`
4. background alignment remains persisted through `DisplayTransform`
5. project files now persist `background_image_path` alongside timing lines and transform state
6. clearing the background image no longer affects start/finish or sector definitions
7. the start/finish and sector line interaction cleanup remains in place:
   - thinner vector rendering
   - checker-pattern start/finish line
   - stronger selected-state feedback
   - crosshair cursor during line drawing

The canvas editor remains aligned with the overlay-first workflow:

1. video import is still retained for reading the real output canvas size
2. the preview surface continues to paint widgets directly with Qt vector drawing
3. selected widgets keep direct resize handles and layout-state writeback

The Windows packaging/runtime path has also been moved closer to a real installed desktop product:

1. the build pipeline now includes an installer-script stage aimed at producing `KartOverlay-Setup.exe`
2. mutable user/runtime data is now designed around `%LOCALAPPDATA%\KartOverlay`
3. the default project directory is now `%USERPROFILE%\Documents\KartOverlay Projects`
4. `.env.local` is no longer used for Amap keys, because the distributed product no longer depends on them

Verification coverage for this pass now includes:

1. background-image track-editor and track-workspace regression tests
2. project save/load tests for persisted background paths
3. packaging/runtime path tests for installer and default Windows user directories
4. full unit-test pass across the repository (`119 passed`)

## Incremental Update: Results-First Track Workspace And Overlay-Layer Alignment

The track-editing page has now been restructured around the approved results-first workflow:

1. the outer main window no longer keeps a standalone right-side status column, so the shell now focuses initial width on:
   - the far-left import/project column
   - the tabbed working area
2. inside the track tab, the working area is now a nested splitter layout:
   - top-left results panel
   - top-right track editor
   - bottom operation strip
3. all of those boundaries can be dragged to resize for the current session
4. splitter proportions are intentionally not persisted, so each fresh launch returns to the default layout

The track/background alignment model has also been inverted to match the editing mental model:

1. the background image now stays visually fixed as the reference layer
2. `DisplayTransform` now moves the telemetry/timing overlay layer instead of the background layer
3. empty-space left drag moves the overlay track layer
4. right drag rotates the overlay track layer
5. `Ctrl + mouse wheel` scales the overlay track layer
6. the bottom operation strip now adds precise `Zoom +` / `Zoom -` controls next to the directional nudge buttons

The canvas widget system has been tightened up at the same time:

1. widget text, spacing, and custom indicator geometry now scale with widget size
2. a minimum font floor keeps small widgets readable instead of letting labels collapse
3. the vector-rendered preview/export path remains intact

Verification coverage for this pass now includes:

1. main-window and track-workspace layout regression tests
2. fixed-background / moving-overlay transform tests
3. precise zoom-button transform tests
4. widget typography scaling tests
5. full unit-test pass across the repository (`123 passed`)

## Incremental Update: Sector Timing Fixes, HUD Track Linkage, and Faster MOV Export

This pass tightened the current track-analysis and export workflow without changing the overall overlay-first architecture:

1. lap sector timing now follows the intended race order:
   - `S1`: start/finish to sector line 1
   - `S2`: sector line 1 to sector line 2
   - `S3`: sector line 2 back to start/finish
2. sector split generation now produces `N + 1` timed segments for `N` sector lines, including the final return segment
3. current-sector reporting now returns the active segment name instead of the last completed segment
4. the track results panel now appends per-lap split text directly into each lap row
5. the lap list now allows horizontal scrolling so dense split content remains readable

The HUD track widget was also corrected so the live marker and direction arrow stay pinned to the rendered trajectory:

1. the moving dot now uses the same normalization basis as the full track polyline
2. the heading arrow remains anchored to that corrected live point
3. regression coverage now checks the marker is positioned on the same normalized track coordinates used by the preview path

The MOV export subprocess path received a stability/performance pass:

1. `ffmpeg` no longer keeps long-running `stderr` output in an in-memory pipe, which reduces the risk of export hangs on larger runs
2. `ffmpeg` and `ffprobe` now start with hidden-window subprocess flags on Windows, preventing terminal popups during metadata read/export
3. the exporter now keeps transparent MOV output on the CPU `prores_ks` path; an earlier Vulkan-preference experiment was superseded because `prores_ks_vulkan` can stall on current Windows builds

Verification coverage for this pass now includes:

1. targeted sector-analysis and track-results regressions
2. HUD mini-track marker/arrow anchoring regressions
3. Windows subprocess flag and non-piped `ffmpeg` logging regressions
4. export, workspace, frame-renderer, canvas, and track-workspace regression runs
5. full unit-test pass across the repository (`153 passed`)

## Incremental Update: Export Encoder Visibility, Reload-Safe Geometry, and HUD Copy Cleanup

This pass closes the three follow-up tail items from the previous handoff:

1. export now surfaces the encoder path selected at runtime
   - the export preparation/result flow now carries an `encoder_label`
   - the active encoder label is now `ProRes 4444 (CPU)` for transparent MOV output
2. widget geometry now survives project save/load and remains aligned for later export
   - project save was already writing full widget layout payloads
   - project load now restores `width`, `height`, and `enabled` instead of only `x`, `y`, and `enabled`
   - this closes the earlier drift where manually resized widgets quietly snapped back to default sizes after reload
3. the HUD copy layer has been tightened without changing layout structure
   - `lap_summary` display naming now matches the current compact behavior as `圈数`
   - HUD card titles for lap count, best lap, sector status, mini track, heading, and G value are now explicit and consistent
   - heading directions now use Chinese compass labels (`北 / 东北 / 东 ...`) instead of English abbreviations

One important clarification from this pass:

1. the earlier “mojibake” suspicion was mostly a terminal-display issue during inspection, not a widespread UTF-8 source-file corruption problem
2. this cleanup therefore stayed focused on real HUD copy inconsistencies instead of rewriting the entire text layer

Verification coverage for this pass now includes:

1. project roundtrip tests for persisted widget width/height/enabled
2. export workspace tests for encoder-label visibility and shared-session widget dimensions
3. export execution tests updated for capability-aware command preparation
4. HUD copy tests for exact display names, card titles, and Chinese compass labels
5. full unit-test pass across the repository (`157 passed`)

## Incremental Update: Overlay Export Scaling and Lap Distance HUD

This pass fixes overlay export parity when the export canvas is smaller than the source video canvas:

1. `ExportWorkspace` now builds export-only widget copies and scales their `x`, `y`, `width`, and `height` from `video_metadata.canvas_size` to the selected export canvas.
2. the UI preview/session widget layout is not mutated during export, so preview geometry remains the source of truth.
3. export manifests now record the widget original canvas, target canvas, and `scale_x` / `scale_y` used for the export.
4. the resolution selector remains limited to original video size, 1080p, and 720p.

This pass also adds the compact `LapDistanceWidget`:

1. the widget displays `圈已行驶距离`, an integer meter value, unit `m`, and a bottom lap-progress bar.
2. lap distance and lap length come from `TrackAnalysisSummary.lap_distance_profiles`; missing data stays `--` and does not turn into `0`.
3. progress is clamped to `0..1`, while the displayed distance remains the real distance returned by the profile.
4. `hud_theme.py` now exposes shared dark-card, border, text, accent, positive, negative, warning, radius, and padding constants for HUD widgets.

Verification coverage for this pass now includes:

1. export widget scaling and manifest regression tests
2. lap-distance summary and widget missing-data tests
3. widget factory/default-layout coverage for `LapDistanceWidget`
4. HUD theme and label-order regressions
5. full unit-test pass across the repository (`175 passed`)

## Incremental Update: RaceChrono-Style HUD Card Group

This pass restructures the overlay widgets around the reference RaceChrono-style card system while keeping the canvas/background behavior unchanged:

1. widget cards now share the same dark card fill, border, 6 px radius, 8/12 px padding, title style, primary value style, unit style, and helper color rules.
2. the default widget layout now follows a dashboard-like grid with 12 px spacing; the mini track card spans a wider slot.
3. metric widgets now include visual areas such as progress gauges, center G bars, trend bars, mini line charts, heading ticks, and mini-track drawing instead of plain text-only blocks.
4. added dashboard cards for relative height and longitudinal G value so the default card group matches the reference set more closely.
5. the export/preview canvas background remains as before: transparent export frames and the existing editor preview background are not replaced by a full-page dashboard fill. Only the widget cards themselves draw their own dark backgrounds.

Verification coverage for this pass:

1. HUD/card/theme/widget/canvas focused regression group: `41 passed`
2. non-UI/data/widget-factory group: `34 passed`
3. UI/project/HUD group: `52 passed`
4. export/build/ffmpeg group: `46 passed`
5. track editor/results/workspace group: `43 passed`
6. compile check for changed widget/render/canvas modules: passed

## Incremental Update: Transparent Small Export Formats and G-Force Ball

This pass adds transparent low-size export choices without changing the existing transparent overlay rendering model:

1. export format settings are now centralized in `kart_overlay.application.export_formats`
   - `MOV ProRes 4444`: transparent, editing-friendly, largest file size
   - `MOV Animation`: transparent, smaller for flat HUD graphics, can grow with complex visuals
   - `WebM VP9 Alpha`: transparent, smallest file size, weaker editor compatibility
2. the export page and legacy export dialog now show every format with a short explanation and an estimated output size.
3. estimates scale from a 720p/50fps reference bitrate by canvas pixels, fps, and export duration, so a 720p 50fps 25-minute ProRes export is shown at roughly the same 16 GB order of magnitude seen in practice.
4. selected formats now flow through the export request, service, FFmpeg command builder, output extension normalization, and manifest fields.
5. the HUD set now includes a `GForceBallWidget` card that preserves the current RaceChrono card style while plotting lateral/longitudinal G as a two-axis ball.
6. the editor checkerboard preview background has been restored; the full overlay canvas is not replaced by a dark dashboard background.

Verification coverage for this pass:

1. export format/spec/size-estimate tests: passed
2. FFmpeg command builder tests for ProRes, QTRLE, and VP9 alpha: passed
3. export workspace and manifest regression tests: passed
4. HUD G-force ball, layout, factory, frame renderer, and canvas regressions: passed

## Incremental Update: FPS Presets, Export Snapshot Isolation, and Alpha-Safe Formats

This pass tightens export behavior after real editor testing showed WebM output appearing as a black-background clip:

1. the export FPS control is now a preset selector instead of free text
   - source-video FPS is listed after video metadata is loaded
   - common options include 24, 25, 30, 50, and 60 fps
2. export now freezes a deep-copied widget snapshot before the background task starts
   - changing the canvas while export is running no longer changes the in-flight export's widget geometry
3. WebM VP9 alpha has been removed from the transparent export options
   - a local FFmpeg encode/decode alpha smoke test showed VP9/WebM decoding back as fully opaque
   - this prevents exporting a file that appears transparent in intent but black in editors
4. the transparent video options now stay limited to alpha-verified MOV outputs
   - MOV ProRes 4444 for best editing compatibility
   - MOV Animation/QTRLE for smaller transparent HUD overlays
5. FFmpeg alpha preservation tests now encode and decode minimal transparent frames for supported formats and verify that alpha survives.

Verification coverage for this pass:

1. export format and FFmpeg command regressions: passed
2. export workspace FPS preset and snapshot isolation regressions: passed
3. real FFmpeg alpha preservation smoke test for ProRes/QTRLE: passed
