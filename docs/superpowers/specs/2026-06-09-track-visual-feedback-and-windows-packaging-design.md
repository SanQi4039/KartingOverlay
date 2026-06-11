# Track Visual Feedback And Windows Packaging Design

## Goal

Build an easy-to-use karting-focused track editing experience with strong visual editing feedback, then package the entire desktop application as a Windows-distributable executable bundle that runs on machines without Python or preinstalled tooling.

## Why This Work Now

The application already has a usable business chain:

1. telemetry import
2. video metadata and sync
3. track definition
4. canvas editing
5. transparent MOV export

The next highest-value gap is not new telemetry math. It is usability and delivery:

1. editing start/finish and sector lines still feels too low-feedback for repeated karting use
2. export and timing are now deep enough that the app needs real Windows distribution for other machines

This design keeps the product intentionally creator-friendly rather than turning it into a professional CAD editor.

## User Outcome

After this work:

1. a karting user can clearly see which timing line is selected
2. a karting user can drag line endpoints directly with obvious handles and labels
3. changing start/finish or sector lines immediately recalculates lap and sector timing summaries
4. the same app can be copied to another Windows machine and launched without installing Python

## Incremental Update 2026-06-09

The implementation now also includes:

1. lap-aware telemetry sample feedback in the sync workflow
2. adjustable canvas widget width and height controls
3. preview-path caching to reduce repeated ffmpeg extraction and overlay rerender cost
4. cached Amap static basemap reuse inside the track editor
5. a more compact track workspace composition with explicit basemap availability/status text

This means the current gap is shifting away from core workflow plumbing and toward visual refinement plus broader page-level polish.

## Scope Split

This design is intentionally split into two sequential implementation phases.

### Phase 1: Visual Track Editing Feedback

Focus on usability in the track editor:

1. selected line highlighting
2. hover feedback
3. endpoint handles
4. line labels
5. selection state display
6. delete/reset actions
7. visible recalculation feedback

### Phase 2: Windows Packaging

Focus on distribution:

1. PyInstaller-based Windows build
2. bundled Python runtime
3. bundled Qt dependencies
4. bundled ffmpeg and ffprobe
5. launchable one-folder deliverable on machines without Python

## Chosen Approach

Use objectized editable scene items inside the existing Qt graphics editor instead of continuing to hand-draw line state inside one large widget.

Why this is the right tradeoff:

1. lighter than building a full CAD-like editor
2. much easier for ordinary karting users than hidden line-edit logic
3. strong enough foundation for future actions like delete, lock, reorder, or right-click menus
4. preserves the current architecture where business recalculation stays outside purely visual scene objects

## Architecture

### Existing Boundary To Preserve

The current structure already has the right business separation and should stay that way:

1. `TrackEditor` owns scene orchestration
2. `TrackWorkspace` bridges editor state into the shared session
3. timing recalculation flows into shared `ProjectSession`
4. export and widgets consume shared track analysis state

The new work must not move timing math into graphics items.

### New Editing Object Model

Add explicit editable scene objects:

1. `EditableTimingLineItem`
   - represents one start/finish line or one sector line
   - draws the main line, selection highlight, label, and handle visibility state
2. `LineHandleItem`
   - represents one draggable endpoint
   - handles hover, drag, and endpoint-specific visual feedback
3. optional lightweight label object or embedded label drawing
   - displays `Start/Finish`, `S1`, `S2`, and selection emphasis

`TrackEditor` stays responsible for:

1. creating and destroying editable line items from `TrackDefinition`
2. tracking current edit mode
3. tracking current selected line and selected endpoint
4. converting visual edits back into domain `TrackDefinition`
5. triggering recalculation after completed edits

### Shared Analysis Model

The recently added shared track analysis summary remains the authoritative recalculation result.

Any change to:

1. start/finish line
2. sector line geometry
3. sector line deletion
4. start/finish reset

must follow this sequence:

1. clear stale shared analysis state
2. rebuild `TrackDefinition`
3. recalculate lap and sector analysis
4. publish fresh shared track analysis into `ProjectSession`
5. refresh track inspector and any widgets that consume timing data

## Phase 1 Detailed Design

### Visual Feedback States

Each editable line supports four visual states.

#### Idle

1. start/finish line uses a yellow dashed line
2. sector lines use orange dashed lines
3. labels remain visible but lower emphasis

#### Hover

1. line width increases slightly
2. label contrast increases
3. endpoint handles fade in or become more visible

#### Selected

1. line gets thicker and brighter
2. handles become fully visible
3. selected label is rendered as a clearer pill or badge
4. selection metadata is shown in the page status area

#### Dragging

1. active handle changes to accent cyan
2. line geometry updates live during drag
3. status text warns that release will recalculate timing
4. recalculation happens on drag release, not on every mouse move

### Interaction Rules

#### Create

1. `Start/Finish` mode: click two points to create the start/finish line
2. `Add Sector` mode: click two points to create the next sector line
3. after the second click, the editor immediately recalculates timing

#### Select

1. clicking a line selects the whole line
2. selection reveals handles and stronger labels
3. only one line needs to be selected at a time in this phase

#### Drag

1. endpoint dragging must happen through handle items, not by dragging the whole line body
2. line body remains easy to select but not easy to accidentally distort
3. releasing a dragged handle commits the geometry change and triggers recalculation

#### Delete And Reset

1. add `Delete Selected` for sector lines
2. add `Reset Start/Finish` for the start/finish line
3. do not add right-click menus or multi-select in this phase

### Status Feedback

The track page should expose short, always-visible status feedback rather than modal dialogs.

Recommended examples:

1. `Mode: Start/Finish`
2. `Selected: S1`
3. `Selected: Start/Finish end point`
4. `Recalculated: Best 52.314 s | S1 18.204 s`

This should live in a lightweight status strip or compact inspector block, not a popup.

### Track Inspector Expansion

The track inspector should continue to show:

1. lap crossings
2. lap count
3. best lap

and also clearly expose:

1. last lap time
2. last sector times
3. best sector times

This directly supports the requirement that start/finish and sector edits must visibly recalculate total and split timing.

### Data Flow

Final interaction data flow:

1. user selects mode in `TrackWorkspace`
2. user creates or edits a line item in `TrackEditor`
3. editable item emits geometric edit back to `TrackEditor`
4. `TrackEditor` rebuilds `TrackDefinition`
5. `TrackEditor` recalculates track analysis summary
6. `TrackWorkspace` publishes track definition and analysis into `ProjectSession`
7. inspector and overlay widgets refresh from the new shared state

## Phase 2 Detailed Design

### Packaging Target

Use `PyInstaller` one-folder packaging as the primary distribution format.

Why one-folder first:

1. simpler to debug than one-file
2. easier for Qt plugins and DLL resolution
3. easier to bundle ffmpeg and ffprobe explicitly
4. more reliable for first external distribution

### Deliverable Shape

Produce a Windows distribution directory containing:

1. application executable
2. Qt runtime and plugins
3. Python runtime
4. app resources
5. `ffmpeg.exe`
6. `ffprobe.exe`
7. optional README for launch notes

The user experience should be:

1. unzip the folder
2. double-click the app
3. use the app without Python installation

### Runtime Tool Resolution

The current binary resolution already supports explicit paths and common local locations.

Packaging work should add a packaged-app resolution path so that:

1. bundled `ffmpeg.exe`
2. bundled `ffprobe.exe`

are preferred when running from the packaged build.

This keeps external-machine behavior stable.

### Packaging Build Assets

Expected additions:

1. PyInstaller spec file
2. build script for Windows packaging
3. copy step for ffmpeg and ffprobe
4. smoke-test instructions for packaged output

### Out Of Scope For This Phase

Do not expand packaging scope into:

1. installer authoring
2. auto-update system
3. code signing
4. one-file packaging
5. cross-platform builds

These can follow after one-folder distribution works reliably.

## Files Likely To Change

Phase 1 likely touches:

1. `kart_overlay/ui/track_editor.py`
2. `kart_overlay/ui/track_workspace.py`
3. `kart_overlay/ui/track_inspector_panel.py`
4. new scene-item helper files under `kart_overlay/ui/` or a focused subfolder
5. `kart_overlay/application/project_session.py`
6. `kart_overlay/widgets/widget_factory.py`
7. timing-related widgets that should reflect recalculated lap and sector data
8. unit tests covering track editing, inspector output, and widget consumption

Phase 2 likely touches:

1. packaging config or new `.spec` file
2. `kart_overlay/config.py`
3. build scripts under a `scripts/` or packaging folder
4. documentation for building and running packaged output

## Error Handling

### Editing

1. deleting a sector line with no selection should do nothing and show a clear status hint
2. resetting start/finish when none exists should show a status hint
3. partial edits must not leave the domain track definition corrupted

### Recalculation

1. recalculation failure should not crash the scene
2. stale timing data must not remain visible after line deletion or reset
3. status area should show recalculation failure in plain language

### Packaging

1. packaging should fail clearly if bundled ffmpeg or ffprobe paths are missing
2. packaged build smoke test should verify app startup and export tool availability
3. docs must state that target machines are Windows-only for this build

## Testing Strategy

### Phase 1

Add or expand tests for:

1. line selection feedback state
2. endpoint drag committing geometry changes
3. start/finish changes causing recalculated lap timing
4. sector changes causing recalculated sector timing
5. deleting sectors and resetting start/finish clearing stale shared analysis
6. inspector formatting of recalculated lap and sector summaries

### Phase 2

Add build verification and smoke coverage for:

1. packaged executable startup
2. packaged ffmpeg and ffprobe detection
3. export page tool status in packaged mode
4. one sample export path from packaged build on a clean Windows machine if possible

## Success Criteria

This design is successful when:

1. editing timing lines feels visually obvious and low-friction for a karting user
2. changing start/finish or sector lines immediately updates total and split timing summaries
3. track-related overlay widgets reflect the refreshed timing state
4. the app can be distributed as a Windows folder that runs on machines without Python installed
