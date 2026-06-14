---
comet_change: execute-drawing-instructions
role: technical-design
canonical_spec: openspec
---

# Execute Drawing Instructions Technical Design

## Context

VoiceCanvas currently captures speech, sends WAV audio to the backend ASR endpoint, and displays the recognized transcript. This change completes the loop from transcript to structured drawing execution: after ASR returns recognized text, the frontend calls the standalone drawing interpretation endpoint, receives a validated drawing envelope, and executes only supported basic create actions on the Fabric.js canvas.

OpenSpec remains the canonical requirements source. This document records the implementation design for the `execute-drawing-instructions` change.

## Goals

- Submit recognized transcript text to `/api/interpret-drawing` for drawing interpretation.
- Keep `/api/asr` as the audio transcription source only for the frontend execution path, even if it currently returns a `drawing` field.
- Execute `drawing.type === "draw"` envelopes containing supported `create` actions for `rectangle`, `circle`, `text`, and `line`.
- Display backend messages for `clarification`, `no_op`, `unsupported`, `parse_error`, and `semantic_error` without modifying the canvas.
- Keep Fabric.js object construction inside the canvas boundary, not inside voice UI code.

## Non-Goals

- Editing existing objects, deleting objects, undo/redo, or clearing the canvas.
- Complex layout, multi-step natural-language clarification UI, or canvas state persistence.
- Replacing Fabric.js or changing VAD/WAV encoding behavior.
- Using `/api/asr.drawing` as the frontend drawing execution data source.

## Architecture

Use `App.vue` as a lightweight coordination layer. `VoiceControl` remains responsible for voice capture, transcript display, and calling the standalone interpretation API. `DrawingCanvas` owns Fabric.js execution and exposes a controlled drawing entrypoint to parent components.

```text
MicVAD speech segment
  -> /api/asr
  -> transcript text
  -> /api/interpret-drawing
  -> drawing envelope
  -> App.vue coordination
     -> draw envelope: DrawingCanvas execution entrypoint
     -> non-draw envelope: VoiceControl-visible message
```

This keeps component boundaries narrow:

- `VoiceControl` handles voice state, ASR history, interpretation request state, and user-facing drawing messages.
- `App.vue` wires emitted drawing envelopes/messages to the canvas and voice UI.
- `DrawingCanvas` maps whitelisted structured actions to Fabric.js objects.
- Backend `/api/interpret-drawing` preserves the drawing envelope contract and remains reusable for future non-voice text inputs.

## Frontend API Flow

After `useVoiceCapture` records a successful transcript, the frontend should submit the transcript to `/api/interpret-drawing` with a JSON body containing `text`. Canvas context is not required for this first implementation path.

The response contract used by the frontend is:

```ts
{
  success: boolean
  drawing: {
    version: string
    type: string
    actions: unknown[]
    requires_clarification: boolean
    message: string | null
  }
}
```

The frontend should treat the response as data, not executable instructions. It should not parse natural-language transcript text into drawing instructions, and it should not read drawing execution data from `/api/asr`.

## Canvas Execution

`DrawingCanvas` should expose a controlled entrypoint such as `executeDrawing(drawing)` or `executeActions(actions)`. The public entrypoint accepts structured data, validates the minimum fields needed by the frontend executor, and returns a small execution result that the caller can use for user-facing feedback.

Supported actions:

- `action: "create"`, `shape: "rectangle"`
- `action: "create"`, `shape: "circle"`
- `action: "create"`, `shape: "text"`
- `action: "create"`, `shape: "line"`

Unsupported action types or shapes are skipped. They must not throw through the UI, and the user should receive one aggregate message indicating that part of the instruction could not be executed.

The executor should use a whitelist of geometry and style fields. Missing optional fields and semantic presets should resolve to visible defaults within the 800x600 canvas, such as centered placement, reasonable dimensions, readable text size, and safe default fill/stroke colors.

## Backend Contract

The backend already provides `/api/interpret-drawing` and the drawing interpreter envelope. Build work should verify the endpoint response still provides:

- `success: true` for successful endpoint handling, including semantic error envelopes.
- `drawing.version`
- `drawing.type`
- `drawing.actions`
- `drawing.requires_clarification`
- `drawing.message`

Unexpected interpreter failures should continue returning a `semantic_error` drawing envelope with a displayable message rather than requiring the frontend to infer an error from raw model output.

## Error and Boundary Handling

- Non-draw envelopes display `drawing.message` and do not call the canvas execution entrypoint.
- Draw envelopes with no executable supported actions do not modify the canvas and produce user-visible feedback.
- Unknown action types, unknown shapes, malformed individual actions, or non-create actions are skipped defensively.
- Backend validation remains the primary contract guard, but frontend execution remains defensive because the UI boundary consumes external API data.
- ASR transcript history remains visible regardless of drawing interpretation result.

## Testing Strategy

Backend focused coverage:

- Verify `/api/interpret-drawing` accepts text and returns a `drawing` object with the expected envelope fields.
- Verify non-draw/error interpreter results include a displayable `message`.
- Preserve existing drawing interpreter validation tests.

Frontend focused coverage:

- Verify the interpretation request helper or voice flow submits recognized transcript text to `/api/interpret-drawing`.
- Verify supported `create` actions map to Fabric rectangle, circle, text, and line objects.
- Verify non-draw envelopes display backend messages and leave the canvas unchanged.
- Verify unsupported action or unsupported shape data does not crash the UI and produces feedback.

Manual verification:

- Start backend and frontend dev servers.
- In the browser, verify speech transcript appears in recognition history.
- Verify a supported instruction such as drawing a blue circle in the center calls `/api/interpret-drawing` and adds a visible Fabric object.
- Verify unsupported/no-op input displays a message and does not change the canvas.

## Implementation Notes

- Keep implementation minimal and aligned with existing Vue 3 `<script setup>` patterns.
- Prefer a small frontend helper only if it reduces coupling between `VoiceControl` and fetch handling.
- Do not introduce global state for this first execution path; a store/composable coordination layer is unnecessary until multiple command sources exist.
- Do not broaden the drawing schema beyond the OpenSpec delta while implementing this change.

## Spec Patch

No spec patch is required from the confirmed design. The current OpenSpec delta already covers the standalone endpoint contract, supported create actions, non-draw message display, and unsupported action safety behavior.
