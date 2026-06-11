# HUD Overlay Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved HUD-only restyle so overlay widgets become more compact, mini-track gains a broadcast-style moving dot, and hidden-state behavior stays consistent between canvas preview and export.

**Architecture:** Keep the change bounded to the overlay rendering stack. Update shared HUD drawing primitives first, then apply role-based widget sizing and per-widget rendering changes, then close the loop with preview/export parity tests and G-force fallback data support.

**Tech Stack:** Python, PySide6, pytest, Qt painting (`QPainter`, `QImage`), existing session/widget/export pipeline.

---

## Scope Guard

This plan intentionally covers only these user requirements:

- `1` G-force widget has no usable displayed value
- `4` default widget sizes should start larger and feel proportional to canvas
- `5` hidden state must work in both canvas preview and export
- `6` oversized widgets should be reduced to key information only
- `7` all HUD widgets should be more compact with less empty space
- `8` mini-track should show a moving dot with direction in canvas preview/export

This plan intentionally does **not** implement these items:

- `2` sector result next to track results
- `3` sector timing model correction
- `9` export GPU/performance improvements
- `10` suppress ffmpeg terminal window

Those remain for later non-HUD phases and the Security/Reality Checker phase.

## File Map

### Likely Tests To Modify Or Extend

- `tests/unit/test_g_force_widget.py`
- `tests/unit/test_frame_renderer.py`
- `tests/unit/test_canvas_workspace.py`
- `tests/unit/test_export_widget_layout_bridge.py`
- `tests/unit/test_widget_factory_analysis.py`
- `tests/unit/test_telemetry_interpolator.py`
- `tests/unit/test_real_parsers.py`

### Likely Production Files To Modify

- `kart_overlay/widgets/hud_theme.py`
- `kart_overlay/widgets/base.py`
- `kart_overlay/widgets/g_force_widget.py`
- `kart_overlay/widgets/mini_track_widget.py`
- `kart_overlay/widgets/sector_state_widget.py`
- `kart_overlay/widgets/speed_widget.py`
- `kart_overlay/widgets/timer_widget.py`
- `kart_overlay/widgets/best_lap_widget.py`
- `kart_overlay/widgets/lap_summary_widget.py`
- `kart_overlay/widgets/heading_widget.py`
- `kart_overlay/widgets/altitude_widget.py`
- `kart_overlay/widgets/coordinates_widget.py`
- `kart_overlay/widgets/widget_factory.py`
- `kart_overlay/domain/telemetry/models.py`
- `kart_overlay/domain/telemetry/interpolator.py`
- `kart_overlay/infrastructure/parsers/vbo_parser.py`
- `kart_overlay/infrastructure/parsers/gpx_parser.py`

### Files To Inspect But Prefer Not To Change Unless Evidence Requires It

- `kart_overlay/ui/canvas_workspace.py`
- `kart_overlay/application/export_service.py`
- `kart_overlay/infrastructure/render/frame_renderer.py`
- `kart_overlay/infrastructure/render/ffmpeg_exporter.py`

---

### Task 1: Reproduce Hidden-State And Moving-Dot Gaps With Failing Tests

**Files:**
- Modify: `tests/unit/test_canvas_workspace.py`
- Modify: `tests/unit/test_export_widget_layout_bridge.py`
- Modify: `tests/unit/test_frame_renderer.py`

- [ ] **Step 1: Add a failing preview-side hidden-state test**

```python
def test_canvas_preview_widget_does_not_render_hidden_mini_track(monkeypatch):
    ...
    session.set_widget_layouts(
        {
            "mini_track": {"x": 100, "y": 60, "enabled": False},
        }
    )
    image = preview._render_overlay_image()
    assert image is None or _alpha_scan(image) == 0
```

- [ ] **Step 2: Add a failing export-side hidden-state regression test for a non-default widget family**

```python
def test_export_workspace_skips_hidden_g_force_widget_from_shared_session(tmp_path):
    ...
    session.set_widget_layouts(
        {
            "speed": {"x": 160, "y": 220, "enabled": True},
            "g_force": {"x": 520, "y": 240, "enabled": False},
        }
    )
    ...
    assert "GForceWidget" not in widget_names
```

- [ ] **Step 3: Add a failing mini-track marker visibility test**

```python
def test_frame_renderer_renders_mini_track_marker_when_position_exists():
    renderer = FrameRenderer(
        canvas_size=(640, 360),
        widgets=[MiniTrackWidget(x=320, y=40, track_points=[(0.0, 0.0), (10.0, 0.0)])],
    )
    image = renderer.render(
        TelemetryFrame(
            data_elapsed_sec=1.0,
            x_m=5.0,
            y_m=0.0,
            speed_kmh=50.0,
            heading_deg=45.0,
        )
    )
    assert _alpha_scan(image) > 0
```

- [ ] **Step 4: Run the focused tests and confirm at least one fails**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_canvas_workspace.py tests\unit\test_export_widget_layout_bridge.py tests\unit\test_frame_renderer.py -q
```

Expected:
- At least one failure tied to hidden-state parity or mini-track marker/direction expectations.

- [ ] **Step 5: Record the failure mode before implementation**

Verification note:
- Save the exact failing test names in the implementation log or working notes.

**Risk:**
- A hidden-state complaint may already be fixed for export but not for preview, or vice versa.

**Rollback:**
- Revert only the new failing tests if the reproduction assumptions are disproven and rewrite them from the observed behavior.

---

### Task 2: Introduce Canvas-Relative Default Sizing And Shared Compact HUD Metrics

**Files:**
- Modify: `tests/unit/test_g_force_widget.py`
- Modify: `tests/unit/test_widget_factory_analysis.py`
- Modify: `tests/unit/test_frame_renderer.py`
- Modify: `kart_overlay/widgets/base.py`
- Modify: `kart_overlay/widgets/hud_theme.py`
- Modify: `kart_overlay/widgets/widget_factory.py`

- [ ] **Step 1: Add a failing size-policy test**

```python
def test_widget_factory_expands_default_hud_sizes_for_primary_and_secondary_widgets():
    session = ProjectSession()
    widgets = build_widgets_from_session(session)
    by_key = {widget.widget_key: widget for widget in widgets}
    assert by_key["speed"].width >= 280
    assert by_key["timer"].width >= 280
    assert by_key["g_force"].width >= 160
    assert by_key["mini_track"].width >= 300
```

- [ ] **Step 2: Add a failing compact-theme metrics test**

```python
def test_hud_card_metrics_support_more_compact_vertical_padding():
    metrics = hud_card_metrics(width=280.0, height=110.0)
    assert metrics.value_top <= 22.0
```

- [ ] **Step 3: Run the new focused tests and confirm failure**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_g_force_widget.py tests\unit\test_widget_factory_analysis.py tests\unit\test_frame_renderer.py -q
```

Expected:
- Failures on current default sizing and/or compact metrics assumptions.

- [ ] **Step 4: Implement the minimal shared sizing policy**

Implementation targets:
- Add role-aware default sizing helpers in `base.py` or `widget_factory.py`
- Keep per-widget overrides possible
- Avoid rewriting session-persisted explicit width/height values

- [ ] **Step 5: Tighten shared HUD metrics in `hud_theme.py`**

Implementation targets:
- Reduce top padding
- Reduce subtitle height
- Keep accent and typography hierarchy
- Preserve transparency-safe rendering

- [ ] **Step 6: Re-run the focused tests**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_g_force_widget.py tests\unit\test_widget_factory_analysis.py tests\unit\test_frame_renderer.py -q
```

Expected:
- All tests pass.

**Risk:**
- Shared metric changes can unintentionally make heading/timer unreadable.

**Rollback:**
- Revert `hud_theme.py` separately from size-policy changes if readability regresses.

---

### Task 3: Restyle G-Force And Metric HUD Widgets Into The Compact Sticker Family

**Files:**
- Modify: `tests/unit/test_g_force_widget.py`
- Add or modify: `tests/unit/test_hud_theme_restyle.py`
- Modify: `kart_overlay/widgets/g_force_widget.py`
- Modify: `kart_overlay/widgets/speed_widget.py`
- Modify: `kart_overlay/widgets/timer_widget.py`
- Modify: `kart_overlay/widgets/best_lap_widget.py`
- Modify: `kart_overlay/widgets/lap_summary_widget.py`
- Modify: `kart_overlay/widgets/heading_widget.py`
- Modify: `kart_overlay/widgets/altitude_widget.py`
- Modify: `kart_overlay/widgets/coordinates_widget.py`

- [ ] **Step 1: Add a failing G-force title/value compactness test**

```python
def test_g_force_widget_keeps_single_primary_value_and_no_source_badge():
    widget = GForceWidget(x=20, y=20)
    assert widget.default_width == widget.default_height
    # Render-path assertion can stay structural if text introspection is hard.
```

- [ ] **Step 2: Add or extend a shared HUD family regression test**

```python
def test_metric_widgets_use_compact_sticker_sizing_family():
    assert SpeedWidget.default_height <= 120
    assert TimerWidget.default_height <= 120
    assert BestLapWidget.default_height <= 120
```

- [ ] **Step 3: Run focused HUD widget tests**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_g_force_widget.py tests\unit\test_hud_theme_restyle.py tests\unit\test_frame_renderer.py -q
```

Expected:
- Failures before production changes.

- [ ] **Step 4: Update widget renderers incrementally**

Order:
1. `g_force_widget.py`
2. `speed_widget.py`
3. `timer_widget.py`
4. `best_lap_widget.py`
5. `lap_summary_widget.py`
6. `heading_widget.py`
7. `altitude_widget.py`
8. `coordinates_widget.py`

Rules:
- One widget at a time
- Preserve existing data dependencies
- Remove copy-heavy subtitle usage

- [ ] **Step 5: Re-run focused HUD widget tests**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_g_force_widget.py tests\unit\test_hud_theme_restyle.py tests\unit\test_frame_renderer.py -q
```

Expected:
- Pass.

**Risk:**
- Visual compactness can reduce legibility if the same value font is reused blindly.

**Rollback:**
- Revert individual widget files one by one while keeping shared theme primitives.

---

### Task 4: Add Mini-Track Broadcast Marker And Direction Arrow

**Files:**
- Modify: `tests/unit/test_frame_renderer.py`
- Add or modify: `tests/unit/test_mini_track_widget.py`
- Modify: `kart_overlay/widgets/mini_track_widget.py`
- Possibly modify: `kart_overlay/widgets/hud_theme.py`

- [ ] **Step 1: Add a failing heading-arrow test**

```python
def test_mini_track_widget_draws_direction_arrow_when_heading_is_available():
    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 10.0)],
    )
    image = _render_widget(
        widget,
        TelemetryFrame(
            data_elapsed_sec=1.0,
            x_m=5.0,
            y_m=5.0,
            speed_kmh=40.0,
            heading_deg=90.0,
        ),
    )
    assert _alpha_scan(image) > 0
```

- [ ] **Step 2: Add a failing fallback test for missing heading**

```python
def test_mini_track_widget_still_draws_position_marker_without_heading():
    ...
    heading_deg=None
    ...
```

- [ ] **Step 3: Run the focused mini-track tests and confirm failure**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_frame_renderer.py tests\unit\test_mini_track_widget.py -q
```

Expected:
- Failure before adding arrow/halo behavior.

- [ ] **Step 4: Implement marker, halo, and short heading arrow**

Implementation targets:
- Keep marker visually small relative to track path
- Keep arrow optional when heading is missing
- Avoid large text overlays like `LIVE`
- Keep one short status line only

- [ ] **Step 5: Re-run mini-track tests**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_frame_renderer.py tests\unit\test_mini_track_widget.py -q
```

Expected:
- Pass.

**Risk:**
- Marker can dominate the track if halo radius is oversized.

**Rollback:**
- Revert marker/arrow drawing in `mini_track_widget.py` while leaving shared compact theme intact.

---

### Task 5: Provide Usable G-Force Values When Source Data Lacks True Acceleration

**Files:**
- Modify: `tests/unit/test_telemetry_interpolator.py`
- Modify: `tests/unit/test_real_parsers.py`
- Possibly add: `tests/unit/test_g_force_estimation.py`
- Modify: `kart_overlay/domain/telemetry/models.py`
- Modify: `kart_overlay/domain/telemetry/interpolator.py`
- Modify: `kart_overlay/infrastructure/parsers/vbo_parser.py`
- Modify: `kart_overlay/infrastructure/parsers/gpx_parser.py`

- [ ] **Step 1: Add a failing parser-or-interpolator fallback test**

```python
def test_telemetry_interpolator_estimates_g_force_from_motion_when_samples_lack_acceleration():
    store = TelemetryStore(
        samples=[
            TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=0.0, heading_deg=0.0),
            TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=0.0, speed_kmh=36.0, heading_deg=0.0),
        ]
    )
    frame = TelemetryInterpolator(store).frame_at(1.0)
    assert frame.accel_long_g is not None or frame.accel_lat_g is not None
```

- [ ] **Step 2: Add a failing “prefer real channel when present” test**

```python
def test_telemetry_interpolator_preserves_real_g_force_when_available():
    ...
    assert frame.accel_long_g == pytest.approx(known_value)
```

- [ ] **Step 3: Run the focused telemetry tests and confirm failure**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_telemetry_interpolator.py tests\unit\test_real_parsers.py -q
```

Expected:
- Failure on estimated-G fallback behavior.

- [ ] **Step 4: Implement the smallest safe fallback**

Recommended boundary:
- Estimate in the interpolation/frame-production path, not in widget rendering
- Prefer real acceleration channels when present
- Keep estimation conservative and deterministic

- [ ] **Step 5: Re-run telemetry and HUD rendering tests**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_telemetry_interpolator.py tests\unit\test_real_parsers.py tests\unit\test_g_force_widget.py tests\unit\test_frame_renderer.py -q
```

Expected:
- Pass.

**Risk:**
- A noisy estimator can make the widget look “alive” but wrong.

**Rollback:**
- Revert estimator code independently while keeping the visual G-force widget restyle.

---

### Task 6: Close Preview/Export Parity And Full HUD Regression

**Files:**
- Modify: `tests/unit/test_canvas_workspace.py`
- Modify: `tests/unit/test_export_widget_layout_bridge.py`
- Modify: `tests/unit/test_frame_renderer.py`
- Possibly modify: `kart_overlay/ui/canvas_workspace.py`
- Possibly modify: `kart_overlay/widgets/widget_factory.py`

- [ ] **Step 1: Add an end-to-end parity test for hidden-state plus moving marker**

```python
def test_canvas_preview_and_export_use_same_enabled_widget_filter():
    session = ProjectSession()
    session.set_widget_layouts(
        {
            "speed": {"x": 40, "y": 40, "enabled": True},
            "mini_track": {"x": 300, "y": 40, "enabled": False},
        }
    )
    assert "MiniTrackWidget" not in _widget_names(build_widgets_from_session(session))
```

- [ ] **Step 2: Run the regression cluster**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_canvas_workspace.py tests\unit\test_export_widget_layout_bridge.py tests\unit\test_frame_renderer.py tests\unit\test_widget_factory_analysis.py -q
```

Expected:
- Any remaining parity failures are now visible.

- [ ] **Step 3: Apply only the minimum production fix if parity still fails**

Implementation targets:
- Prefer fixing shared widget construction/filtering instead of duplicating preview/export logic
- Change `canvas_workspace.py` only if preview-side state invalidation or widget selection logic truly causes stale rendering

- [ ] **Step 4: Run full test suite**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m pytest -q
```

Expected:
- Full suite passes.

- [ ] **Step 5: Run compile check**

Run:
```powershell
D:\Anaconda_env\karting\python.exe -m compileall kart_overlay tests
```

Expected:
- No compile errors.

**Risk:**
- Preview parity bugs may actually be stale-cache bugs rather than enabled-filter bugs.

**Rollback:**
- Revert parity fixes separately from styling and telemetry-estimation changes.

---

## Security/Reality Checker Follow-Up Items

Do not finalize these in the HUD implementation batch. Hand them to the later Security/Reality Checker phase:

- Whether G-force estimation could mislead users without an explicit source badge
- Whether heading-arrow drawing should clamp obviously invalid heading values
- Whether hidden widgets can still leak into export through any future alternate render path
- Whether HUD compacting increases overlap risk at smaller canvas sizes

## Phase Verification Commands

Use these as the standard command set during implementation:

```powershell
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_g_force_widget.py -q
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_frame_renderer.py -q
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_canvas_workspace.py tests\unit\test_export_widget_layout_bridge.py -q
D:\Anaconda_env\karting\python.exe -m pytest tests\unit\test_telemetry_interpolator.py tests\unit\test_real_parsers.py -q
D:\Anaconda_env\karting\python.exe -m pytest -q
D:\Anaconda_env\karting\python.exe -m compileall kart_overlay tests
```

## Commit Strategy

- Commit 1: shared HUD sizing and theme primitives
- Commit 2: compact widget family restyle
- Commit 3: mini-track moving dot and direction arrow
- Commit 4: G-force fallback data support
- Commit 5: hidden-state parity fixes and regression tests
