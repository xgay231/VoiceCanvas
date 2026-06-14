## 1. Dependency and Project Setup

- [x] 1.1 Add Fabric.js dependency compatible with the required `import { fabric } from 'fabric'` usage.
- [x] 1.2 Add or adjust TypeScript support needed for Vue `<script setup lang="ts">` components.
- [x] 1.3 Add or adjust Tailwind CSS setup if it is not already available to the frontend.

## 2. Drawing Canvas Component

- [x] 2.1 Create `frontend/src/components/DrawingCanvas.vue` with a visible 800x600 canvas area and Tailwind-styled border/background.
- [x] 2.2 Initialize `fabric.Canvas` in `onMounted` after the canvas element is available.
- [x] 2.3 Add a centered default shape after Fabric initialization to prove interaction works.
- [x] 2.4 Dispose the Fabric canvas in `onUnmounted` and clear the stored instance reference.
- [x] 2.5 Expose the Fabric canvas instance with `defineExpose` for parent-component access.
- [x] 2.6 Add a top-right download button that exports the current Fabric canvas content as an image.

## 3. App Integration and Verification

- [ ] 3.1 Mount `DrawingCanvas` in `frontend/src/App.vue` without breaking the existing voice control UI.
- [ ] 3.2 Run frontend tests/build to verify the component, dependency imports, TypeScript, and bundling.
