# Chinese UI And HUD Restyle Design

## Goal

Refit the desktop app for a Chinese karting customer base by making the entire product Chinese-first, fixing whole-window dragging through a custom Chinese title bar, and restyling the overlay HUD away from boxed dashboard cards toward lightweight racing telemetry stickers.

## Why This Work Now

The current workflow chain is already functional:

1. telemetry import
2. video metadata and sync
3. track editing
4. canvas editing
5. transparent MOV export
6. Windows packaging

The next product gap is usability and presentation for the actual target audience:

1. the program still exposes mostly English UI text
2. the packaged main window cannot be dragged like a normal desktop app
3. the current HUD language is too card-heavy and too close to generic dark panels instead of restrained motorsport telemetry stickers

## Approved Direction

Use a Chinese-first product pass with a light custom title bar and a sticker-style HUD redesign.

This direction intentionally does **not** rebuild the business workflow or rewrite the renderer from scratch. It keeps the data pipeline and export path stable while replacing the window chrome, UI copy, and HUD visual language.

## User Outcome

After this work:

1. the main desktop window is draggable again
2. the app surface is fully Chinese by default
3. exported overlays also use Chinese HUD labels by default
4. the HUD looks closer to racing telemetry stickers instead of boxed dashboard panels
5. the current sync, track, canvas, and export workflow remains intact

## Scope

### In Scope

1. custom Chinese title bar for the main window
2. whole-app default Chinese UI copy
3. default Chinese HUD labels in exported overlays and preview
4. HUD visual restyle toward the supplied reference direction
5. canvas preview interaction fixes related to left-right dragging and widget placement clarity
6. incremental documentation updates

### Out Of Scope

1. multi-language switching
2. a full workflow IA redesign
3. replacing Qt with another UI stack
4. rewriting the export pipeline
5. a full CAD-like overlay editor

## Design Principles

The implementation should follow these product rules:

1. Chinese is the only default language for both app UI and overlay labels
2. the product should feel easy for ordinary karting users, not like a broadcast graphics workstation
3. transparent export suitability matters more than fancy panel decoration
4. the middle of the overlay should stay visually empty whenever practical
5. window behavior must feel native and reliable on Windows even if the title bar is custom

## Architecture

### Keep Business Logic Stable

The current application and export chain should stay structurally intact:

1. `ProjectSession` remains the shared state source
2. the track, sync, canvas, and export pages keep their current responsibilities
3. widget data still flows through the existing widget factory and frame renderer

This work should mainly affect:

1. window shell composition
2. UI labels and copy
3. widget presentation and positioning defaults
4. canvas preview interaction polish

### New UI Text Boundary

Introduce a focused text/catalog layer for Chinese-facing labels instead of hardcoding all translated strings inside widgets and pages.

This layer should provide:

1. app window text
2. tab names
3. page button labels
4. field labels
5. HUD widget display titles
6. status text and workflow copy

The goal is to make later wording changes straightforward without searching through every page class.

### Window Shell Boundary

The main window should move to a custom title-bar shell while still using the existing page widgets.

The shell should own:

1. app title
2. drag area
3. minimize button
4. maximize/restore button
5. close button
6. double-click maximize handling

The inner workflow widgets should not be responsible for window movement.

### HUD Styling Boundary

The visual redesign should be concentrated in the HUD theme and widget drawing helpers, not scattered ad hoc across every widget.

The theme layer should define:

1. typography
2. accent colors
3. divider line style
4. bar style
5. gauge style
6. shadow and outline rules

Individual widgets should mostly consume those theme primitives.

## Window Behavior Design

### Title Bar Style

Use a light custom title bar rather than a fully exotic frameless shell.

Visually:

1. Chinese product title
2. restrained dark background
3. crisp white text
4. cyan accent details consistent with the new HUD language
5. simple Windows-like control buttons on the right

Behaviorally:

1. dragging any empty title-bar area moves the window
2. double-click toggles maximize/restore
3. minimize, maximize, restore, and close actions work normally
4. the implementation should prioritize stability over visual tricks

## Chinese UI Design

### App-Level Copy

Translate the whole workflow into Chinese-first labels, including:

1. window title
2. tab titles
3. project workflow panel
4. sync page controls
5. track page controls
6. canvas editor controls
7. export page controls
8. status panel text

### Chinese HUD Labels

HUD labels should also default to Chinese. Examples:

1. `速度`
2. `当前圈`
3. `最佳圈`
4. `分段`
5. `圈数`
6. `油门`
7. `刹车`
8. `转速`
9. `方向`
10. `航向`
11. `时间差`
12. `赛道`

Numeric values remain numeric, but titles and small helper labels should read naturally for Chinese users.

## HUD Restyle Design

### Reference Direction

The approved reference is a restrained karting telemetry sticker style:

1. bold white italic numerals
2. small white labels
3. thin cyan underline/divider accents
4. subtle dark shadow or thin outline for readability
5. very limited use of color outside signal bars and warning ranges
6. no large dashboard panels
7. no sci-fi glass, holographic framing, or neon UI language

### Layout Language

The overlay should feel distributed around the edges, with the center staying mostly empty and transparent.

Default layout direction:

1. top row: session/time/track/lap meta
2. left stack: current lap, best lap, sector, G-force, lap count
3. right stack: RPM, throttle, brake, steering, delta
4. bottom right: main speed gauge
5. bottom band: simplified support widgets such as throttle/brake bars, heading, compact RPM, or mini track

### Visual Rules

The redesign should replace current card-heavy rendering with lighter sticker elements:

1. remove most filled rounded panels
2. keep short cyan line accents instead of large card borders
3. use white numerals as the primary visual anchor
4. keep green only for throttle
5. keep red only for brake and RPM warning emphasis
6. use cyan for structure, not for glowing decoration
7. keep shapes crisp and flat, not glossy

### Widget-Specific Intent

Expected changes by widget family:

1. speed becomes the main visual anchor with a cleaner semicircle gauge
2. lap and best-lap widgets lose heavy card fills and become stacked telemetry stickers
3. sector state uses lighter split markers and cleaner timing hierarchy
4. heading becomes a simpler compact compass treatment
5. mini track becomes a cleaner white path line with a small accent marker
6. throttle/brake bars become slim horizontal broadcast-style bars
7. RPM shifts toward segmented warning bars instead of a boxed numeric card

## Canvas Interaction Fixes

The user reported left-right dragging problems. For this pass, the canvas editor must be checked for:

1. widget dragging in both X and Y directions
2. correct hit testing
3. visible selection state
4. clear position feedback while dragging

This should be solved inside the existing canvas preview interaction model, not by replacing the canvas page.

## Data Flow

Updated display flow after this work:

1. `ProjectSession` keeps widget state and telemetry/timing state
2. widget factory creates Chinese-labeled widgets by default
3. HUD theme provides the sticker-style visual language
4. frame renderer renders the new transparent edge-layout widgets
5. canvas preview reflects the same Chinese HUD style used by export

## Error Handling

### Window Shell

1. if a custom title bar event is not on the drag zone, it should not move the window
2. maximize/restore state text or icon should stay synchronized
3. page interaction should not accidentally trigger window dragging

### Chinese Copy

1. missing labels should fall back to a safe Chinese default where possible
2. no mixed English/Chinese wording should remain in normal user flows unless it is a unit suffix or unavoidable technical term

### HUD Restyle

1. redesign must not reduce readability on transparent export
2. colored elements must remain readable over bright or dark source footage
3. if a widget lacks data, it should still show a stable Chinese label and placeholder state

## Testing Strategy

Add or expand tests for:

1. main window title-bar actions and drag-related shell behavior where feasible
2. Chinese text rendering in key UI surfaces
3. canvas preview drag movement in both axes
4. widget labels produced by the factory being Chinese by default
5. HUD theme helpers producing the new lightweight visual structure without breaking transparent rendering
6. export preview and full test suite regression after restyling

## Success Criteria

This work is successful when:

1. the packaged app window can be dragged normally again
2. the visible app UI is Chinese by default
3. the default overlay labels are Chinese by default
4. the HUD feels closer to professional karting telemetry stickers than boxed dashboard cards
5. no existing workflow page loses functional behavior
