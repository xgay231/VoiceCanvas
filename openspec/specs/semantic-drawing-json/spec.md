# semantic-drawing-json Specification

## Purpose
TBD - created by archiving change semantic-drawing-json. Update Purpose after archive.
## Requirements
### Requirement: Structured Drawing Interpretation

The backend SHALL convert recognized or submitted natural-language drawing instructions into a structured JSON object that represents the drawing semantic result and can be consumed by the frontend drawing executor.

#### Scenario: Interpret text through a standalone endpoint for frontend execution

- **GIVEN** the frontend has a recognized transcript such as `画一个蓝色圆形在画布中央`
- **WHEN** the frontend submits that transcript to the standalone drawing interpretation endpoint
- **THEN** the endpoint SHALL return a `drawing` object with `version`, `type`, `actions`, `requires_clarification`, and `message`
- **AND** `drawing.type` SHALL be `draw` when executable create actions are available
- **AND** the response SHALL preserve enough structured action data for the frontend to create supported Fabric.js objects without parsing natural-language text
- **AND** the endpoint SHALL not require an audio upload

### Requirement: Stable JSON Model Output Contract

The backend SHALL prompt `mimo-v2.5-pro` to return only a JSON object matching the supported drawing interpretation schema.

#### Scenario: Model returns valid structured JSON

- **GIVEN** the semantic model returns a valid JSON object matching the supported schema
- **WHEN** the backend parses the model response
- **THEN** the backend SHALL return the parsed object in the `drawing` field
- **AND** SHALL NOT return raw explanatory model text as the executable drawing result

#### Scenario: Model raw message is available for debugging

- **GIVEN** the backend receives a response from `mimo-v2.5-pro`
- **WHEN** handling the semantic interpretation result
- **THEN** the backend SHALL output the raw model message to the backend console log for debugging

### Requirement: Safe Handling of Ambiguous or Unsupported Input

The semantic drawing result SHALL explicitly represent ambiguous, irrelevant, unsupported, or parser-error input with a user-facing message instead of inventing executable drawing actions.

#### Scenario: Non-draw result includes displayable message

- **GIVEN** the semantic drawing result has type `clarification`, `no_op`, `unsupported`, `parse_error`, or `semantic_error`
- **WHEN** the backend returns the drawing envelope to the frontend
- **THEN** the drawing envelope SHALL include a human-readable `message` suitable for display in the voice UI
- **AND** the drawing envelope SHALL NOT require the frontend to infer a message from raw model text

### Requirement: Server-side Parse and Validation Failure Path

The backend SHALL validate model output before exposing it as structured drawing data.

#### Scenario: Model returns non-JSON content

- **GIVEN** `mimo-v2.5-pro` returns text that cannot be parsed as a JSON object
- **WHEN** the backend handles the semantic model response
- **THEN** the backend SHALL return a `drawing` object with `type` equal to `parse_error`
- **AND** the response SHALL include a diagnostic error message
- **AND** the backend SHALL NOT pass unvalidated model text as executable drawing JSON

#### Scenario: Model returns JSON with missing required fields

- **GIVEN** `mimo-v2.5-pro` returns a JSON object missing required schema fields
- **WHEN** the backend validates the parsed JSON
- **THEN** the backend SHALL return a `drawing` object with `type` equal to `parse_error`
- **AND** the diagnostic message SHALL identify validation failure at a useful level

#### Scenario: Semantic model call fails after ASR succeeds

- **GIVEN** ASR successfully returns transcript text
- **AND** the `mimo-v2.5-pro` semantic interpretation request fails, times out, or raises an API error
- **WHEN** `/api/asr` builds its response
- **THEN** the response SHALL keep `success` equal to `true`
- **AND** the response SHALL preserve the transcript in the `text` field
- **AND** the response SHALL include a `drawing` object with `type` equal to `semantic_error`
- **AND** the response SHALL NOT represent the failure as `no_op`

