# HUD Overlay Restyle Design

**Date:** 2026-06-11  
**Scope:** HUD overlay components only. This spec explicitly excludes main-window, track-page, export-page, and other non-HUD layout work.

## Goal

Restyle the overlay HUD components into a lighter racing-broadcast sticker system that is more compact, wastes less space, and better fits transparent export output.

## In Scope

- HUD component drawing and sizing only
- Default HUD size policy relative to canvas size
- Mini-track moving-dot and heading-arrow presentation
- HUD hidden-state behavior consistency between canvas preview and exported video
- G-force display strategy for datasets that usually do not contain true acceleration channels

## Out Of Scope

- Main UI panels, splitters, tabs, and workspace layout
- Track results panel redesign
- Export page redesign
- Sync workflow restoration
- Background map/source workflow redesign

## Confirmed Product Decisions

1. Use visual direction `A`: lightweight racing-broadcast sticker style.
2. This round modifies HUD components only, not the main application UI.
3. Mini track must show a racing-broadcast-style moving dot, synced in canvas preview and export.
4. Moving dot must include heading direction when heading is available.
5. Hidden HUD widgets must disappear in both canvas preview and exported video.
6. G-force should prioritize useful output for users who mostly do not have real acceleration channels.
7. UI does not need to distinguish `real` vs `estimated` G-force values.

## Visual System

### Shared HUD Language

- Deep transparent overlay background context
- White primary numerics
- Cyan accent for emphasis and active state
- Minimal gray secondary text
- No heavy card fills
- No large empty padding blocks
- One visual idea per widget

### Shared Layout Rules

- Structure every HUD as `small title + large primary value + one short secondary line + minimal graphic`
- Remove long explanatory copy
- Reduce internal padding across all widgets
- Prefer visual hierarchy through type scale and accent strokes, not thick borders

### Shared State Rules

- Empty data: show `--`
- Hidden: no rendering in preview, no rendering in export
- Selected in canvas editor: light cyan outline with resize handles
- Animated state: only subtle local motion such as current marker pulse or active sector highlight

## Widget Specifications

### GForceWidget

- Keep square form factor
- Keep g-ball graphic and combined G value as the dominant content
- Use a very small title `G`
- Do not add source labels such as `RAW` or `EST`
- If no reliable value is available, keep the ball skeleton and display `--`

**Default size**
- Preferred: `160x160`
- Minimum practical size: `120x120`
- Maximum default preset: `180x180`

### MiniTrackWidget

- Convert from card-like metric widget to graphic-first track widget
- Primary visual content is the track path
- Current position becomes a broadcast-style moving dot:
  - bright solid core
  - subtle outer halo
  - short heading arrow when heading is available
- Show start/finish marker clearly
- Show sector markers only as light track annotations
- Keep only one short bottom status line, for example `L2 / S3`
- Remove large `LIVE`-style center emphasis

**Default size**
- Preferred: `320x200`
- Acceptable neighboring preset: `300x200`

### SectorStateWidget

- Restyle into a narrow timing sticker
- Large primary value shows current sector elapsed time
- Secondary line shows compact current-sector context
- Add a bottom row of sector indicators such as `S1 / S2 / S3 ...`
- Current sector gets the active highlight

**Default size**
- Preferred: `300x110`

### Metric Widgets Family

Applies to:
- `speed`
- `timer`
- `best_lap`
- `lap_summary`
- `heading`
- `altitude`

Rules:
- Move all of them into the same compact sticker family
- One large primary value
- At most one short secondary line
- Keep any supporting graphic very small
- Reduce padding and eliminate oversized card feel

**Default size**
- Preferred family range: `280x110` to `300x120`

### CoordinatesWidget

- Treat as a tertiary HUD element
- If shown, render as a slim label-style component instead of a large card
- It must not compete with primary racing metrics

**Default size**
- Preferred: about `260x70`

## Size Policy

Default sizes must not rely only on hardcoded per-widget pixel constants.

Implementation should move toward a canvas-relative preset policy with role-based tiers:

- Primary HUD: `speed`, `timer`, `mini_track`
- Secondary HUD: `best_lap`, `sector_state`, `heading`, `g_force`
- Tertiary HUD: `altitude`, `coordinates`

The target behavior is not "everything larger," but "better starting size with proportional scaling across canvas sizes."

## Motion Specification

Allowed motion:
- mini-track current marker pulse
- mini-track heading arrow direction updates
- active sector indicator highlight

Disallowed motion:
- continuous full-widget glow
- heavy flashing
- long particle trails
- animation that risks export instability

## Hidden-State Contract

When a widget is hidden:

1. It remains in editable widget state.
2. It stays visible in the component list as a weakened row.
3. It must not render in canvas preview.
4. It must not render in exported video.

This is a functional product contract, not just a cosmetic preference.

## G-Force Data Contract

Because the target users commonly lack true acceleration channels:

- show a usable G-force value whenever the system can provide one
- do not surface "true vs estimated" source labels in HUD UI
- still preserve graceful empty-state behavior when no safe value can be produced

## Verification Targets For The Next Phase

- Canvas preview shows the same hidden-widget behavior as export
- Mini track marker moves with preview time
- Mini track marker direction changes with heading data
- Compact widgets still remain readable at common export resolutions
- Default HUD layout looks balanced on the current default canvas

## Risks

- Mini-track marker may overpower the track path if oversized
- Heading-arrow fallback must behave cleanly when heading is missing
- Hidden-state fixes span preview and export rendering paths, so one-sided verification is insufficient
- Compacting all widgets too aggressively may reduce readability for speed and timer

## Rollback Strategy

- Implement in small widget-focused batches
- Keep theme/layout changes separate from mini-track behavior changes
- Keep hidden-state fixes separate from style-only changes
- Revert per batch if readability or export parity regresses
