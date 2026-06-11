# Local Background Images And Windows Installer Design

## Goal

Replace the Amap-dependent track-background workflow with a local image workflow that is safe to distribute in a Windows desktop installer.

The user should be able to:

1. import either a satellite/map screenshot or a schematic track image as the track-editing background
2. move, scale, rotate, reset, replace, and clear that background image while keeping GPX track coordinates canonical
3. save and reload project files with the selected background image path and transform state
4. package the product as a real Windows `setup.exe` installer instead of only a portable folder build
5. keep program files, user configuration, and user project files in the correct Windows locations

The core architectural rule for this change is:

`the track path and timing lines remain canonical scene geometry; only the background-image layer moves.`

## Current Problems

1. the app still contains Amap-specific API, configuration, and UI concepts even though the product is intended to be distributed without exposing third-party keys
2. a distributed desktop `exe` cannot safely contain a reusable Amap Web Service key, so the current map-provider direction is not suitable for public distribution
3. the track editor's current background interaction logic is tied to the idea of a remote basemap instead of a user-supplied local image
4. the project file does not yet persist a local track-background image path
5. the existing Windows packaging path produces a PyInstaller directory/zip build, but not a user-facing `setup.exe` installer
6. the runtime still assumes `.env.local` in the working directory for map-related configuration, which is not a good fit for an installed desktop product

## Chosen Approach

The implementation will use four focused changes:

1. **Replace Amap with a local background-image layer**
   - Remove Amap service/config usage from the track-editing workflow.
   - Load a user-selected image file directly into the track editor as the background layer.
   - Continue using the existing transform model so the background layer can be translated, rotated, and scaled relative to the telemetry path.

2. **Simplify the track persistence model**
   - Keep `DisplayTransform`, but strip it down to transform-only fields.
   - Add `background_image_path` to the saved track-definition payload.
   - Do not preserve any backward-compatibility logic for old Amap-era projects because there are no existing user projects to migrate.

3. **Treat the background image as edit-only support material**
   - Keep the background image visible only in the track editor.
   - Do not include it in transparent overlay export rendering.
   - Let the export path remain focused on telemetry widgets and transparent video output.

4. **Add a real Windows installer and formal user-data layout**
   - Keep PyInstaller as the app-bundle stage.
   - Add an installer stage that produces `setup.exe`.
   - Store installed binaries in the user-selected install directory.
   - Store configuration/log/cache data under `AppData\Local\KartOverlay`.
   - Default project save/load dialogs to `Documents\KartOverlay Projects`.

## Components

### Track Background Image Layer

Files involved:

- `kart_overlay/ui/track_editor.py`
- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/domain/track/models.py`
- `kart_overlay/ui/project_panel.py`

Responsibilities:

1. import and render a local image beneath the telemetry path
2. support replacement, clearing, reset, and transform editing
3. persist image path plus transform state into the project file
4. surface missing-file and image-load errors without breaking track editing

The editor will load the background image from disk into a `QGraphicsPixmapItem` and apply the stored transform only to that item. The telemetry path, start/finish line, and sector lines remain the reference geometry and are never transformed by background alignment actions.

### Track Definition Persistence

Files involved:

- `kart_overlay/domain/track/models.py`
- `kart_overlay/ui/project_panel.py`
- `kart_overlay/domain/project.py`
- `tests/unit/test_track_definition.py`
- `tests/unit/test_project_panel.py`

Responsibilities:

1. store transform fields only in `DisplayTransform`
2. add `background_image_path` to track-definition serialization
3. save relative paths when practical, otherwise save absolute paths
4. load projects even if the background image file no longer exists

The saved `track` payload will contain:

1. `start_finish`
2. `sectors`
3. `display_transform`
4. `background_image_path`

`DisplayTransform` will retain only:

1. `translate_x`
2. `translate_y`
3. `rotation_deg`
4. `scale`

The old `basemap_provider` field will be removed entirely.

### Track Workspace UI

Files involved:

- `kart_overlay/ui/track_workspace.py`
- `kart_overlay/ui/texts.py`

Responsibilities:

1. rename basemap concepts to background-image concepts
2. provide explicit import/replace/clear/reset controls
3. keep the existing alignment gestures and micro-adjust buttons
4. expose current background status and selected filename clearly

The sidebar controls will be:

1. `导入背景图`
2. `替换背景图`
3. `清空背景图`
4. `重置背景变换`
5. `透明度`
6. `上下左右微调`

Supported image formats for the first version will be common local raster formats:

1. `png`
2. `jpg`
3. `jpeg`
4. `bmp`
5. `webp`

### Windows Installer And User Data Layout

Files involved:

- `scripts/build_windows_dist.py`
- `packaging/kart_overlay.spec`
- new installer script(s) under `packaging/`
- `kart_overlay/config.py`
- `kart_overlay/packaging.py`
- potentially a new app-path helper module

Responsibilities:

1. build the application bundle with PyInstaller
2. produce a `setup.exe` installer from that bundle
3. define the installed-program location separately from user-data locations
4. remove runtime dependence on `.env.local` for distributed installs

The Windows data layout will be:

1. **Install directory**
   - user-selected during setup
   - contains `KartOverlay.exe`, bundled FFmpeg/FFprobe, and runtime DLLs

2. **User configuration/runtime data**
   - `%LOCALAPPDATA%\KartOverlay`
   - contains settings, logs, caches, and future per-user runtime files

3. **Default project directory**
   - `%USERPROFILE%\Documents\KartOverlay Projects`
   - becomes the initial directory for save/load project dialogs

This separation keeps upgrades and uninstall safe while avoiding permission issues under `Program Files`.

## Interaction Model

### Track Editor

1. `view` mode:
   - left-drag on empty space moves the background image
   - `Ctrl + wheel` scales the background image
   - right-drag rotates the background image
2. `start_finish` and `sector` modes:
   - cursor remains crosshair
   - background image does not react to drag gestures
3. selected timing lines keep the current thinner-vector/highlighted behavior

### Background Image Controls

1. `导入背景图`
   - opens file picker
   - loads image and sets it as the current background layer
2. `替换背景图`
   - opens file picker and swaps the current image
3. `清空背景图`
   - removes the image path and hides the background layer
   - does not delete start/finish or sector lines
4. `重置背景变换`
   - resets `translate_x`, `translate_y`, `rotation_deg`, and `scale`
   - keeps the current image path
5. `透明度`
   - adjusts editor-only background visibility
   - does not affect saved export output
6. `上下左右微调`
   - keeps the current nudge model for fine alignment

### Project Save/Load Behavior

1. saving a project stores the current background image path and transform
2. if the image can be expressed relative to the project file path, save the relative path
3. otherwise save the absolute path
4. loading a project with a missing image:
   - restores track lines and transforms normally
   - leaves the editor usable
   - shows a clear status that the background image file is missing

## Packaging And Installation Behavior

1. the build pipeline remains two-stage:
   - PyInstaller builds the runnable app bundle
   - installer tooling packages that bundle as `setup.exe`
2. the installed app must be able to run without a workspace-local `.env.local`
3. the installer must not put mutable user files into the install directory
4. uninstall must remove app binaries but leave user projects and user data intact by default
5. future app settings should target `%LOCALAPPDATA%\KartOverlay`, not the current working directory

The intended user experience is:

1. run `setup.exe`
2. choose install path
3. launch the app from Start Menu or desktop shortcut
4. save projects by default into `Documents\KartOverlay Projects`
5. keep configuration and runtime support files under `AppData\Local\KartOverlay`

## Error Handling

1. if the user selects a non-image file, show a clear load failure and keep the previous background state unchanged
2. if the background image path in a project is missing, show a recoverable status instead of failing project load
3. if the installer build toolchain is missing, fail the packaging step with a direct actionable error
4. if the default user-data directories do not yet exist, create them lazily on first use

## Testing Strategy

1. replace Amap-specific unit tests with local-background-image tests where appropriate
2. add serialization tests for:
   - `background_image_path`
   - reduced `DisplayTransform`
3. add track-editor tests for:
   - import background image
   - replace background image
   - clear background image
   - reset transform
   - drag/scale/rotate updating stored transform
4. add project save/load tests for:
   - relative background paths
   - absolute background paths
   - missing image file recovery
5. add packaging/config tests for:
   - resolved user-data directories
   - default project directory selection
   - installer-script generation or packaging entrypoint behavior
6. keep export regression coverage to ensure the background image never leaks into transparent overlay output
7. run focused test suites first, then `tests/unit -q`

## Non-Goals

1. do not keep any live Amap integration path in the distributed product
2. do not include the background image in final overlay export output
3. do not support multiple simultaneous editable background layers in this pass
4. do not preserve compatibility with old Amap-era project files
5. do not redesign the export workflow beyond the installer/data-path implications
