## Context

The frontend currently mounts the voice control UI in `App.vue` and does not yet provide a drawing surface. The requested canvas is a foundation for future canvas-based editing and voice-driven drawing interactions, but this change is limited to a basic Fabric.js integration that is visible, interactive, lifecycle-safe, and exportable.

The repository's current frontend is Vue 3 with Vite. Existing source files are JavaScript-oriented, while this component is explicitly required to use TypeScript and `<script setup lang="ts">`. Styling should use Tailwind CSS classes for the new canvas surface and controls.

## Goals / Non-Goals

**Goals:**
- Add a `DrawingCanvas.vue` component using Vue 3 Composition API and `<script setup lang="ts">`.
- Use Fabric.js v5 import style: `import { fabric } from 'fabric'`.
- Initialize Fabric only after the DOM canvas element exists in `onMounted`.
- Dispose the Fabric instance in `onUnmounted` to prevent leaks across component switches.
- Render an obvious canvas region with border and light background/grid styling.
- Add a centered default shape to prove Fabric interaction works.
- Expose the Fabric canvas instance through `defineExpose`.
- Provide a top-right download button that exports the current canvas as an image.
- Mount the component in the app for manual verification.

**Non-Goals:**
- Full drawing toolbars, freehand drawing, object palettes, save/load persistence, history/undo, zoom/pan, collaboration, or backend integration.
- Changes to ASR, audio capture, VAD/ONNX assets, or backend APIs.
- Complex application-wide state management.

## Decisions

1. **Use a standalone `DrawingCanvas.vue` component**
   - Rationale: Keeps Fabric lifecycle and export behavior localized and reusable.
   - Alternative considered: Initialize Fabric directly in `App.vue`; rejected because it would mix app layout with canvas lifecycle concerns.

2. **Use Fabric v5 named import style**
   - Rationale: The user explicitly called out Fabric v5 safety: `import { fabric } from 'fabric'`.
   - Alternative considered: Namespace or default imports used by other Fabric versions; rejected for this change unless dependency resolution proves v5 incompatible.

3. **Fixed initial canvas size of 800x600**
   - Rationale: Provides deterministic setup and easy verification for the first integration.
   - Alternative considered: Fully responsive parent-size canvas; deferred because resize behavior adds extra lifecycle and Fabric dimension synchronization complexity.

4. **Canvas wrapper owns download control positioning**
   - Rationale: A relatively positioned wrapper can place the download button in the top-right without altering Fabric's internal upper/lower canvas layering.
   - Alternative considered: Fabric-rendered button inside the canvas; rejected because export controls should remain UI chrome and not be part of the drawing itself.

5. **Use Fabric `toDataURL` for image export**
   - Rationale: It exports the current Fabric scene reliably and avoids manual DOM canvas handling.
   - Alternative considered: Raw HTMLCanvasElement export; rejected because Fabric maintains its own canvas stack and scene rendering state.

## Risks / Trade-offs

- **Fabric import/type mismatch** → Pin or install a Fabric version compatible with `import { fabric } from 'fabric'`; verify with frontend build.
- **Tailwind may not be configured yet** → Add minimal Tailwind setup if absent, or keep new component classes Tailwind-compatible while preserving existing styles.
- **Download may be triggered before initialization** → Disable or no-op the button until the Fabric instance is ready.
- **Fixed canvas size may not fit small screens** → Wrap in an overflow container; defer responsive resizing to a later change.
- **Object disposal could throw if repeated** → Keep a nullable instance ref and clear it after `dispose()`.

## Migration Plan

1. Add Fabric.js and any required TypeScript/Tailwind dependencies/configuration.
2. Create `DrawingCanvas.vue` with mounted initialization, unmounted disposal, default shape, exposed instance, and download button.
3. Update `App.vue` to render the new component alongside or near existing UI.
4. Run frontend build/tests to verify imports, TypeScript, and bundling.
5. Rollback by removing the component mount and dependency/config additions if needed.

## Open Questions

None for the initial implementation. Future changes can revisit responsive sizing, drawing tools, persistence, and voice-driven canvas operations.
