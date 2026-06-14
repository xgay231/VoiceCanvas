---
comet_change: add-fabric-canvas
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-14-add-fabric-canvas
status: final
---

# Add Fabric Canvas Technical Design

## Overview

This change introduces a standalone Fabric.js canvas component for the Vue frontend. The first version is intentionally small: it mounts an 800x600 Fabric canvas, shows a visible drawing area, adds a default interactive shape, exposes the Fabric instance, provides a top-right download button, and cleans up the Fabric instance on unmount.

The component is a foundation for later canvas editing and voice-driven drawing behavior, but this design avoids drawing tools, persistence, zooming, history, or backend integration.

## Current Context

The frontend currently mounts `VoiceControl` directly from `App.vue`. There is no drawing surface yet. Existing source files are mostly JavaScript-based Vue SFCs, while this component is required to use Vue 3 Composition API with `<script setup lang="ts">`.

The implementation should not change the ASR backend, audio capture flow, VAD/ONNX runtime assets, or the audio format contract.

## Architecture

Use a standalone component:

```text
App.vue
  ├─ VoiceControl.vue        existing voice recognition UI
  └─ DrawingCanvas.vue       new Fabric canvas UI
        ├─ HTML wrapper      layout, border, download button
        ├─ <canvas>          Fabric rendering target
        └─ fabric.Canvas     lifecycle-owned instance
```

`DrawingCanvas.vue` owns all Fabric-specific concerns:

- DOM canvas reference
- Fabric canvas instance reference
- mount-time initialization
- unmount-time disposal
- default shape creation
- image download behavior
- exposed canvas instance

This keeps `App.vue` focused on composition and avoids mixing application layout with Fabric lifecycle logic.

## Component Design

`DrawingCanvas.vue` should use:

- `<script setup lang="ts">`
- `ref`, `onMounted`, and `onUnmounted` from Vue
- Fabric v5 import style:

```ts
import { fabric } from 'fabric'
```

The component keeps two refs:

- `canvasElement`: points to the native `<canvas>` DOM element
- `canvas`: stores `fabric.Canvas | null`

The Fabric instance is exposed with:

```ts
defineExpose({ canvas })
```

The exposed value is the current canvas ref, allowing future parent components to inspect or manipulate the Fabric instance without moving lifecycle ownership out of `DrawingCanvas.vue`.

## Lifecycle Flow

```text
Vue mounts component
        │
        ▼
canvasElement exists
        │
        ▼
new fabric.Canvas(canvasElement, options)
        │
        ▼
set background / grid-like visual treatment
        │
        ▼
add centered default shape
        │
        ▼
renderAll()

Vue unmounts component
        │
        ▼
canvas.dispose()
        │
        ▼
canvas ref = null
```

Key lifecycle rules:

- Initialize Fabric only in `onMounted`, never during setup, because the canvas DOM node must exist first.
- Guard initialization if the element ref is missing.
- Dispose only when a Fabric instance exists.
- Clear the stored instance after disposal to avoid stale references.

## Canvas Layout

Use a relatively positioned wrapper around the canvas:

```text
┌──────────────────────────────────────────────┐
│ DrawingCanvas wrapper                        │
│                                      [下载]  │
│  ┌────────────────────────────────────────┐  │
│  │                                        │  │
│  │              Fabric Canvas             │  │
│  │          default centered shape         │  │
│  │                                        │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

Recommended layout properties:

- wrapper: `relative`, rounded corners, subtle background, padding, and overflow handling
- button: `absolute right-3 top-3 z-10`
- canvas: fixed `width="800" height="600"`, visible border, shadow or contrast treatment

The fixed 800x600 size is intentional for this first integration because it gives deterministic dimensions and makes center placement straightforward. Small screens should be handled by an outer overflow container rather than resizing Fabric in this change.

## Visual Treatment

The canvas area must be clearly visible. The implementation can use either:

- a light solid Fabric background color, or
- a simple grid-like CSS/Fabric background treatment.

The important requirement is that users can immediately distinguish the drawable area from the page background. Tailwind CSS classes should be used for the wrapper, border, spacing, and button styling.

## Default Fabric Content

After initialization, add one obvious centered shape. A blue rectangle or red circle is sufficient.

The shape should use center-based positioning:

```ts
originX: 'center'
originY: 'center'
left: CANVAS_WIDTH / 2
top: CANVAS_HEIGHT / 2
```

The shape should remain selectable and movable using Fabric's default object interaction. This proves that Fabric mounted correctly and that the canvas is interactive.

## Download Behavior

The top-right download button exports only the Fabric canvas content. It must not include the HTML button or wrapper UI.

Flow:

1. User clicks the download button.
2. If `canvas.value` is null, do nothing or keep the button disabled.
3. Call Fabric `toDataURL` with PNG format.
4. Create a temporary anchor element with `download="voicecanvas-drawing.png"`.
5. Trigger the anchor click.
6. Remove the temporary anchor.

The button should be disabled before Fabric initialization to avoid null-instance errors.

## App Integration

Update `App.vue` to import and render `DrawingCanvas` while preserving `VoiceControl`.

A simple layout is enough:

```text
VoiceCanvas page
  ├─ voice controls
  └─ drawing canvas section
```

This keeps the existing voice recognition UI available and makes the new canvas visible for manual verification.

## Dependencies and Configuration

Add Fabric.js as a frontend runtime dependency compatible with:

```ts
import { fabric } from 'fabric'
```

If TypeScript support is not already installed for the Vite/Vue project, add the minimal dependency/configuration required for a Vue SFC using `<script setup lang="ts">` to build.

If Tailwind CSS is not already configured, add minimal Tailwind setup for the frontend and use it only for new canvas-related layout/styling. Existing `VoiceControl` scoped CSS should not be rewritten as part of this change.

## Error Handling and Edge Cases

- Missing canvas DOM element on mount: skip initialization and leave the button disabled.
- Download before initialization: disabled button or safe no-op.
- Repeated unmount/dispose: check for a non-null Fabric instance before disposing.
- Fixed canvas on narrow screens: use wrapper overflow rather than responsive Fabric resizing in this change.
- Fabric import/type mismatch: adjust dependency version toward Fabric v5 compatibility first, preserving the requested import style.

## Testing Strategy

Automated verification:

- Run frontend build to verify Fabric import, TypeScript SFC support, Tailwind processing, and Vite bundling.
- Run existing frontend tests to confirm current behavior is not broken.

Manual verification:

- Page displays an 800x600 canvas with a visible border and light background/grid treatment.
- Default centered shape appears after mount.
- Default shape can be selected and dragged.
- Download button appears at the canvas UI's top-right corner.
- Downloaded PNG contains the canvas content and does not include the button.
- Navigating away or unmounting the component disposes the Fabric canvas instance.

## Out of Scope

- Drawing toolbar or freehand drawing controls
- Object palette or property editing
- Save/load persistence
- Undo/redo history
- Zoom/pan behavior
- Responsive Fabric resizing
- Backend API changes
- Voice-command integration with canvas actions
