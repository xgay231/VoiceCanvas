---
comet_change: semantic-drawing-json
role: technical-design
canonical_spec: openspec
---

# Semantic Drawing JSON Technical Design

## Context

VoiceCanvas currently accepts browser-recorded WAV audio through `/api/asr`, sends it to `mimo-v2.5-asr`, and returns recognized text. The frontend already has a Fabric canvas foundation, but free-form transcript text is not a stable contract for drawing execution.

This change adds a backend semantic interpretation layer. The layer converts recognized or typed drawing instructions into a validated `drawing` JSON envelope that future frontend code can consume.

## Goals

- Convert ASR transcript text into stable structured drawing JSON using `mimo-v2.5-pro`.
- Preserve the original transcript in API responses.
- Keep `/api/asr` as the voice entry point while adding a standalone text interpretation endpoint for testing, debugging, and future manual input.
- Log the raw `mimo-v2.5-pro` message to the backend console for Prompt debugging.
- Validate model output before exposing it as drawing data.

## Non-Goals

- Do not implement the frontend drawing executor in this change.
- Do not replace the existing `mimo-v2.5-asr` transcription flow.
- Do not add multi-turn canvas object memory.
- Do not support destructive or canvas-wide operations such as delete, clear, group, layer, or stacking in the first version.

## Architecture

Use a lightweight service split:

```text
backend/main.py
  - FastAPI app and CORS
  - /api/asr audio endpoint
  - /api/interpret-drawing text endpoint
  - ASR and semantic interpretation orchestration

backend/drawing_interpreter.py
  - DRAWING_INTERPRETER_PROMPT
  - interpret_drawing_text(text, client, canvas_context=None)
  - call mimo-v2.5-pro
  - log raw model message
  - parse_model_json(raw_message)
  - validate_drawing_payload(payload)
  - build parse_error / semantic_error envelopes
```

`backend/main.py` remains the route layer. The new interpreter module owns the Prompt, model call, parsing, validation, and standard drawing envelope construction. This keeps the current small backend understandable while avoiding a large mixed-responsibility `main.py`.

## Data Flow

### Voice entry point

```text
Browser WAV
  │
  ▼
POST /api/asr
  │
  ├─ mimo-v2.5-asr ──► transcript text
  │
  └─ interpret_drawing_text(text)
       │
       ├─ mimo-v2.5-pro
       │    │
       │    ▼
       │ raw model message ──► console log
       │    │
       │    ▼
       │ parse JSON + validate
       │
       ▼
{ success, text, drawing }
```

### Text entry point

```text
POST /api/interpret-drawing
{ "text": "画一个蓝色圆形在画布中央" }
  │
  ▼
interpret_drawing_text(text)
  │
  ▼
{ success, text, drawing }
```

The standalone endpoint uses the same interpreter function and `drawing` contract as `/api/asr`. It does not require audio upload.

## Drawing JSON Contract

All semantic results use a common envelope:

```json
{
  "version": "1.0",
  "type": "draw",
  "actions": [],
  "requires_clarification": false,
  "message": null
}
```

Top-level fields:

- `version`: fixed string, `"1.0"`.
- `type`: one of `draw`, `clarification`, `no_op`, `unsupported`, `parse_error`, `semantic_error`.
- `actions`: array. It may be non-empty only when `type` is `draw`.
- `requires_clarification`: true only when the result needs user clarification.
- `message`: human-readable diagnostic or clarification text. Required for clarification, no-op, unsupported, parse error, and semantic error results.

First-version action scope:

- `create`: supported for `rectangle`, `circle`, `text`, and `line`.
- `update`: supported only for basic color, size, and position changes when sufficient target context exists.
- `delete`, `clear`, `group`, `layer`, and stacking operations: unsupported in this version.

Use semantic presets instead of concrete Fabric coordinates when the user does not provide exact values. Example:

```json
{
  "action": "create",
  "shape": "circle",
  "text": null,
  "style": {
    "fill": "blue",
    "stroke": null,
    "strokeWidth": null
  },
  "position": {
    "preset": "center",
    "x": null,
    "y": null
  },
  "size": {
    "preset": "medium",
    "width": null,
    "height": null,
    "radius": null
  }
}
```

For update requests, the model must not invent target object ids. If the user says “把它改成红色” and no object context is provided, the result must be `clarification`, not `draw`.

## Prompt Strategy

The Prompt should make the model a constrained parser, not a conversational assistant:

- Role: VoiceCanvas drawing instruction parser.
- Output: a JSON object only; no Markdown, code fences, or explanations.
- Schema: include the allowed top-level fields, result types, actions, shapes, and field meanings.
- Uncertainty: return `clarification` when target context is missing.
- Unsupported scope: return `unsupported` for delete, clear, group, layer, and stacking.
- Non-drawing input: return `no_op`.
- Presets: prefer position and size presets such as `center`, `top`, `left`, `right`, `bottom`, `small`, `medium`, and `large` when exact coordinates or dimensions are absent.

The user message sent to `mimo-v2.5-pro` should be structured so future context can be added without changing the whole API:

```json
{
  "text": "画一个蓝色圆形在画布中央",
  "canvas_context": null
}
```

## Error Handling

### ASR failure

If ASR fails, `/api/asr` returns `success=false`, empty `text`, and an `error` message. No drawing action should be exposed because there is no trustworthy transcript.

### Semantic model call failure

If ASR succeeds but `mimo-v2.5-pro` fails, times out, or raises an API error, `/api/asr` returns `success=true` and preserves `text`. The drawing envelope is:

```json
{
  "version": "1.0",
  "type": "semantic_error",
  "actions": [],
  "requires_clarification": false,
  "message": "Semantic interpreter unavailable"
}
```

This must not be represented as `no_op`, because that would hide a system failure.

### Model output parse or validation failure

If `mimo-v2.5-pro` returns content that cannot be parsed or does not satisfy the supported schema, return `parse_error` with a useful diagnostic message. Do not pass unvalidated model content as executable drawing JSON.

The interpreter must print the raw model message before parsing:

```python
print(f"[drawing_interpreter] raw model message: {raw_message}")
```

## Validation Strategy

First version uses hand-written validation instead of a full Pydantic model layer. This keeps iteration cheap while the schema is still stabilizing.

Validation rules:

- Parsed value must be a JSON object.
- `version` must equal `"1.0"`.
- `type` must be one of the supported result types.
- `actions` must be an array.
- Non-`draw` types must have an empty `actions` array.
- `draw` actions must use `create` or `update`.
- `create.shape` must be one of `rectangle`, `circle`, `text`, or `line`.
- `update` must not include a fabricated target id when no context was provided.
- Top-level unknown fields should be rejected. Action-level unknown fields may be ignored in the first version to allow Prompt iteration.

`parse_model_json` may support stripping Markdown code fences as a robustness measure, but any non-object or invalid JSON must result in `parse_error`.

## Tests

### Pure function tests

Add tests for parsing and validation:

- Valid `create` JSON.
- Valid `clarification` JSON.
- Markdown code fence wrapped JSON.
- Non-JSON text.
- Missing `version`, `type`, or `actions`.
- Unknown top-level `type`.
- Unknown action.
- Non-`draw` type carrying actions.

### Standalone endpoint tests

Mock the MIMO client and verify `/api/interpret-drawing` returns:

- `draw` for a valid create instruction.
- `clarification` for an update without target context.
- `no_op` for unrelated text.
- `unsupported` for first-version unsupported operations.
- `parse_error` for invalid model output.
- `semantic_error` for model call failures.

### `/api/asr` integration tests

Mock ASR and semantic interpretation responses and verify:

- ASR success plus semantic success returns `success=true`, `text`, and `drawing`.
- ASR success plus parse error preserves `text` and returns `drawing.type="parse_error"`.
- ASR success plus semantic call failure preserves `text` and returns `drawing.type="semantic_error"`.
- ASR failure returns `success=false`.

## Spec Patch Applied

The OpenSpec delta spec was updated with the confirmed design constraints:

- Mixed preset schema for positions and sizes.
- Standalone text interpretation endpoint using the same drawing contract as `/api/asr`.
- First-version action scope: `create` plus basic `update`; no delete, clear, group, layer, or stacking.
- ASR success plus semantic model failure preserves `text` and returns `semantic_error`.
