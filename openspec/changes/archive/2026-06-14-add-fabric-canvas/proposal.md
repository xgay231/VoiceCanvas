## Why

VoiceCanvas needs a visible drawing surface that can become the foundation for future canvas-based editing and voice-driven drawing interactions. Introducing a basic Fabric.js canvas now validates that Fabric can be mounted safely in the Vue 3 frontend lifecycle and that users can see, interact with, and export the canvas area.

## What Changes

- Add a Vue 3 `<script setup lang="ts">` `DrawingCanvas.vue` component using Composition API.
- Import and initialize Fabric.js safely for Fabric v5 using `import { fabric } from 'fabric'`.
- Render a clearly visible canvas area with Tailwind CSS styling, a light background/grid treatment, and an obvious border.
- Initialize a `fabric.Canvas` instance in `onMounted` and dispose it in `onUnmounted` to avoid memory leaks during component switching.
- Add a default centered shape after initialization to prove Fabric is mounted and interactive.
- Expose the Fabric canvas instance via `defineExpose` for future parent-component control.
- Provide a download button in the canvas area's top-right corner that exports the current canvas as an image.
- Mount the new canvas component in the frontend so it can be viewed during development.

## Capabilities

### New Capabilities
- `drawing-canvas`: Covers rendering, lifecycle management, basic interaction proof, instance exposure, and image download for the Fabric.js drawing canvas.

### Modified Capabilities

None.

## Impact

- Affected frontend files likely include `frontend/src/components/DrawingCanvas.vue`, `frontend/src/App.vue`, and package/dependency configuration under `frontend/`.
- Adds a new runtime dependency on Fabric.js and may require TypeScript/Tailwind setup adjustments if they are not already configured.
- No backend API, ASR flow, VAD/ONNX asset, or audio format contract changes are intended.
