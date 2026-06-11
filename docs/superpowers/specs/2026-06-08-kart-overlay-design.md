# Kart Overlay Desktop Design

## 1. Overview

This project will build a local Windows desktop application for generating transparent telemetry overlay videos for karting and track-day footage. The application will import a source video and GPX/VBO telemetry, let the user define timing lines and overlay layout in a native Qt interface, preview the result locally, and export a transparent `MOV ProRes 4444` overlay video for use in professional editing software.

The selected implementation direction is **Scheme C: layered architecture with one end-to-end usable vertical slice**. That means we will build the long-term architecture from the beginning, but only fully implement the first production chain in phase one:

`video probe -> GPX/VBO import -> normalized telemetry -> track/timing analysis -> local Qt preview -> transparent MOV export`

PNG sequence export is retained only as a fallback path when Alpha MOV export fails.

## 2. Goals

Phase-one goals:

1. Launch a native Qt desktop application from the local Python environment at `D:\Anaconda_env\karting`.
2. Import common video files and read width, height, fps, duration, and rotation metadata.
3. Import both `GPX` and `VBO` telemetry sources and normalize them into one internal data model.
4. Display track data in a local editor and allow manual start/finish line and sector line definition.
5. Compute laps, sectors, best lap, and delta-to-reference using the normalized telemetry model.
6. Preview telemetry widgets locally inside the Qt application.
7. Export a transparent `MOV ProRes 4444` overlay video with matching canvas size and fps.
8. Save and reopen project files with stable references to video, telemetry, track configuration, layout, sync, and export settings.

Non-goals for phase one:

1. Browser UI, embedded web map, or web-first architecture.
2. Automatic video editing, AI commentary, or automatic track recognition.
3. Multi-car comparison and advanced CAN/OBD analytics.
4. Commercial online satellite map integration as a required dependency.
5. Final production-quality theming for every widget beyond a usable professional baseline.

## 3. Architecture Decision

We will use a hybrid of layered architecture and vertical-slice delivery:

1. **Strict architectural boundaries** for long-term maintainability.
2. **One fully implemented slice** for early usability and technical validation.

Why this approach:

1. A pure scaffold-first approach risks producing a large empty shell with no usable output.
2. A pure feature-first approach would entangle parsing, timing, UI, and export logic too early.
3. The hybrid approach keeps domain logic testable while still producing a working desktop tool in the first stage.

## 4. High-Level Layers

The application will be organized into the following layers:

### 4.1 `ui`

Responsibilities:

1. Qt Widgets main window and panels.
2. Video preview container.
3. Track editor scene.
4. Overlay canvas editor scene.
5. Property panels and export dialogs.

Must not:

1. Parse GPX/VBO directly.
2. Compute laps, sectors, deltas, or interpolation directly.
3. Build FFmpeg commands directly.

### 4.2 `application`

Responsibilities:

1. Coordinate import, analysis, sync, and export use cases.
2. Hold application-facing project state.
3. Connect UI commands to domain services and infrastructure adapters.

Must not:

1. Own parsing details.
2. Own geometric/timing algorithms.
3. Render widgets directly.

### 4.3 `domain`

Responsibilities:

1. Define telemetry, timing, track, sync, and overlay domain models.
2. Perform line crossing, lap detection, sector detection, distance alignment, delta calculation, and frame interpolation.
3. Remain fully testable without Qt or FFmpeg.

Must not depend on:

1. Qt
2. FFmpeg
3. file dialogs
4. local filesystem layout

### 4.4 `infrastructure`

Responsibilities:

1. Parse GPX and VBO.
2. Probe video files with FFprobe.
3. Export Alpha MOV and fallback PNG with FFmpeg.
4. Save project files and logs.
5. Provide cache or local-basemap support later.

Must not:

1. Decide lap validity rules.
2. Decide widget layout behavior.
3. Reach back into UI widgets.

### 4.5 `widgets`

Responsibilities:

1. Implement reusable overlay modules such as speed, timer, delta, sectors, and mini track map.
2. Render from a read-only telemetry frame and render context.

Must not:

1. Re-read telemetry files.
2. Recompute laps or deltas.
3. Mutate project state during rendering.

## 5. Phase-One Product Slice

The first complete slice will include:

1. Video import and metadata probing.
2. GPX import.
3. VBO import with configurable channel mapping.
4. Telemetry normalization.
5. Track visualization in a local Qt scene.
6. Start/finish line editing.
7. Sector line editing.
8. Lap and sector analysis.
9. Reference-lap delta calculation.
10. Local preview with a minimum widget set.
11. Transparent MOV export.
12. Project save/load.

The first widget set will be:

1. `TrackMapWidget`
2. `SpeedWidget`
3. `TimerWidget`
4. `DeltaWidget`
5. `SectorWidget`
6. `LapTableWidget`
7. `GBallWidget` if source data or estimate is available

## 6. Native UI Design

The UI will be a native Qt Widgets application. No browser, no QWebEngine dependency for the primary workflow, and no web frontend layer.

Main layout:

1. Left sidebar: project tree, imported assets, widget list.
2. Center workspace: tabbed or stacked `Video Preview`, `Track Editor`, and `Canvas Editor`.
3. Right sidebar: property editor and style/config panel.
4. Bottom strip: timeline and current video/data position status.

Key UI modules:

1. `MainWindow`
2. `ProjectPanel`
3. `TrackEditor`
4. `CanvasEditor`
5. `SyncPanel`
6. `ExportDialog`
7. `PropertyPanel`

UI implementation choices:

1. `QGraphicsView/QGraphicsScene` for track and canvas interaction.
2. Background worker threads for import, analysis, and export.
3. Signal-based updates from workers to the main thread.
4. A consistent dark professional desktop theme, but without blocking the core technical slice.

## 7. Core Domain Model

### 7.1 Telemetry Store

All GPX/VBO input must be converted into one normalized store.

Required normalized fields:

1. `sample_index`
2. `timestamp_ms`
3. `elapsed_sec`
4. `lat`
5. `lon`
6. `x_m`
7. `y_m`
8. `speed_kmh`
9. `heading_deg`
10. `accel_long_g`
11. `accel_lat_g`
12. `lap_id`
13. `lap_time_sec`
14. `lap_distance_m`
15. `sector_id`
16. `sector_time_sec`
17. `valid`
18. `source_quality`

### 7.2 Track Definition

Track-related domain objects:

1. `TimingLine`
2. `SectorLine`
3. `TrackDefinition`
4. `DisplayTransform`

There must be a hard split between:

1. **calculation coordinates** used for timing and distance
2. **display coordinates** used for UI alignment and drawing

### 7.3 Sync Model

Video-to-data sync is defined by an offset:

`data_time = video_time - sync_offset`

The sync model must stay reusable across preview and export.

### 7.4 Telemetry Frame

Widgets and renderers receive a read-only frame view, not raw parser output.

The frame must expose:

1. interpolated position
2. speed
3. heading
4. G values
5. lap/sector progress
6. delta to reference lap
7. quality flags

## 8. Parsing and Normalization

### 8.1 GPX

Parsing requirements:

1. Read coordinates and timestamps.
2. Read elevation if present.
3. Use raw speed/heading if present in extensions.
4. Estimate speed when absent.
5. Estimate heading when absent.
6. Estimate G only as a marked low-confidence derived value.
7. Reject timing analysis when timestamps are missing.

### 8.2 VBO

Parsing requirements:

1. Support channel alias mapping.
2. Preserve unknown channels for inspection.
3. Prefer raw speed/heading/G from VBO over derived values.
4. Expose a user-correctable channel mapping step in the UI flow.

### 8.3 Cleaning Rules

1. Remove or invalidate empty coordinate samples.
2. Sort out-of-order timestamps.
3. Collapse duplicate timestamps safely.
4. Mark GPS spikes instead of deleting them blindly.
5. Carry quality metadata forward to later layers.

## 9. Timing and Delta Analysis

The timing engine is a pure algorithm module.

Required responsibilities:

1. Detect line crossings from adjacent trajectory segments.
2. Interpolate crossing time instead of snapping to sample boundaries.
3. Apply direction rules, cooldown time, cooldown distance, and minimum speed.
4. Build laps and sector tables.
5. Select a reference lap.
6. Compute delta against the reference lap by lap distance, not raw global time.

Key rule:

`delta = current_lap_time_at_distance(d) - reference_lap_time_at_distance(d)`

## 10. Preview and Export

### 10.1 Preview

Preview uses a lower-cost pipeline for responsiveness:

1. video frame reference
2. synchronized telemetry lookup
3. widget rendering onto a transparent Qt surface
4. composited local display

Preview must not be reused as final export output.

### 10.2 Export

Primary export target:

1. `MOV ProRes 4444` with Alpha channel

Fallback target:

1. `PNG sequence`

Export flow:

1. Probe and validate export settings.
2. Generate target frame times from output fps.
3. Convert each `video_time` to `data_time`.
4. Query a `TelemetryFrame`.
5. Render widgets on a transparent `RGBA` frame.
6. Pipe or stage frames for FFmpeg encoding.
7. Produce Alpha MOV plus export manifest and log.

Important transparency note:

1. Some general-purpose players may show black where Alpha exists.
2. Editing software should still read Alpha correctly if the export path is valid.
3. The app must verify encoder settings around Alpha support and not route the primary export through non-Alpha codecs such as standard H.264 MP4.

## 11. Project Persistence

Project save/load is required in phase one.

Project file contents:

1. project metadata
2. video path and probed metadata
3. telemetry source path and import settings
4. sync offset
5. track line definitions
6. widget layout and style config
7. export settings
8. quality report summary

Persistence rules:

1. Save JSON-based project files.
2. Use temporary file write then atomic replace.
3. Detect missing assets on reopen and ask for relocation.

## 12. Proposed Directory Structure

```text
kart_overlay/
  app.py
  requirements.txt
  README.md

  ui/
    main_window.py
    project_panel.py
    track_editor.py
    canvas_editor.py
    sync_panel.py
    export_dialog.py
    property_panel.py
    viewmodels/
      project_viewmodel.py
      track_viewmodel.py
      canvas_viewmodel.py
      export_viewmodel.py

  application/
    services/
      project_service.py
      analysis_service.py
      export_service.py
    usecases/
      import_video.py
      import_telemetry.py
      recalculate_timing.py
      update_sync.py
      export_overlay.py
    tasks/
      task_runner.py

  domain/
    telemetry/
      models.py
      store.py
      interpolator.py
      frame_provider.py
      quality.py
    track/
      models.py
      projection.py
      transforms.py
    timing/
      line_crossing.py
      lap_detector.py
      sector_detector.py
      delta_calculator.py
      rules.py
    sync/
      models.py
    overlay/
      layout.py
      render_context.py
      widget_contract.py

  infrastructure/
    parsers/
      gpx_parser.py
      vbo_parser.py
      channel_mapper.py
      telemetry_cleaner.py
      telemetry_normalizer.py
      quality_report.py
    video/
      ffprobe_service.py
    render/
      frame_renderer.py
      ffmpeg_exporter.py
      png_fallback_exporter.py
      export_manifest.py
    persistence/
      project_repository.py
      atomic_writer.py
    logging/
      log_service.py

  widgets/
    track_map_widget.py
    speed_widget.py
    timer_widget.py
    delta_widget.py
    sector_widget.py
    lap_table_widget.py
    g_ball_widget.py

  tests/
    unit/
      test_gpx_parser.py
      test_vbo_parser.py
      test_line_crossing.py
      test_lap_detector.py
      test_sector_detector.py
      test_delta_calculator.py
      test_interpolator.py
    integration/
      test_import_pipeline.py
      test_export_manifest.py
      test_alpha_export_pipeline.py
```

## 13. Technical Stack

Preferred stack:

1. `PySide6` for local Qt Widgets UI
2. `numpy`
3. `pandas`
4. `gpxpy`
5. `pydantic` for config or schema validation where helpful
6. `ffmpeg` and `ffprobe` external binaries
7. `pytest`

Compatibility rule:

Any added package must remain compatible with the Python runtime available in `D:\Anaconda_env\karting`. If PySide6 compatibility is poor in that environment, the UI layer may fall back to `PyQt5`, but the architecture and application code should keep the switch localized.

## 14. Testing Strategy

Phase-one tests will focus on correctness of the core chain:

1. GPX parsing and normalization.
2. VBO parsing and channel mapping.
3. Line crossing interpolation.
4. Lap and sector construction.
5. Delta-by-distance calculation.
6. Telemetry frame interpolation.
7. Project persistence roundtrip.
8. Export manifest correctness.
9. Alpha export integration smoke test.

UI testing in phase one will be limited to launch-level and workflow smoke coverage. Core correctness must be protected at the domain and application layers.

## 15. Risks and Mitigations

1. `Alpha MOV compatibility`
Mitigation: lock phase-one export to a known FFmpeg + ProRes 4444 path and retain PNG fallback.

2. `VBO channel diversity`
Mitigation: explicit alias mapping plus user-correctable mapping UI.

3. `Low-quality GPX`
Mitigation: propagate quality markers and degrade UI widgets instead of failing hard.

4. `UI complexity`
Mitigation: implement only one solid slice first and avoid overbuilding editing tools before the render path is proven.

5. `Environment/package compatibility`
Mitigation: inspect the target conda environment before pinning dependencies and keep the UI binding choice adaptable.

## 16. Delivery Definition

Phase one is complete when all of the following are true:

1. The user can launch the local desktop app.
2. The user can import a video and GPX/VBO data.
3. The user can define start/finish and sector lines in the local UI.
4. The application computes laps, sectors, and deltas.
5. The user can preview overlay widgets locally.
6. The application exports a transparent `MOV ProRes 4444` overlay video.
7. The project can be saved and reopened without losing core configuration.

## 17. Implementation Note

The first coding phase should not try to finish every UI capability named in the PRD. It should instead build the architecture and immediately exercise it through the end-to-end usable slice above. Additional map features, styling depth, templates, and advanced telemetry widgets can then be layered onto a verified pipeline instead of being guessed in advance.
