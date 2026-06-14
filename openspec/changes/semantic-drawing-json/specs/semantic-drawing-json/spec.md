# semantic-drawing-json Specification

## ADDED Requirements

### Requirement: Structured Drawing Interpretation

The backend SHALL convert recognized natural-language drawing instructions into a structured JSON object that represents the drawing semantic result.

#### Scenario: Create a basic shape

- **GIVEN** the ASR transcript is `画一个蓝色圆形在画布中央`
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** the response SHALL include the original transcript text
- **AND** the response SHALL include a `drawing` object with `version`, `type`, and `actions`
- **AND** `drawing.type` SHALL be `draw`
- **AND** at least one action SHALL represent creating a circle with blue styling and center placement semantics
- **AND** placement and size SHALL be represented with semantic presets when exact canvas coordinates are not provided

#### Scenario: Interpret text through a standalone endpoint

- **GIVEN** a client submits recognized or typed text to the standalone drawing interpretation endpoint
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** the endpoint SHALL return the same `drawing` contract used by `/api/asr`
- **AND** the endpoint SHALL not require an audio upload

#### Scenario: Preserve original transcript

- **GIVEN** a voice request is successfully transcribed
- **WHEN** semantic drawing interpretation succeeds or fails
- **THEN** the response SHALL preserve the original transcript in the `text` field

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

The semantic drawing result SHALL explicitly represent ambiguous, irrelevant, or unsupported user input instead of inventing executable drawing actions.

#### Scenario: Ambiguous edit without target context

- **GIVEN** the ASR transcript is `把它改成红色并放大一点`
- **AND** no target object context is available to the semantic parser
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** `drawing.type` SHALL be `clarification`
- **AND** the result SHALL include a human-readable `message` describing what information is needed
- **AND** the result SHALL NOT include a fabricated target object id

#### Scenario: Non-drawing input

- **GIVEN** the ASR transcript is unrelated to drawing or canvas operations
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** `drawing.type` SHALL be `no_op`
- **AND** the response SHALL NOT include executable drawing actions

#### Scenario: Drawing request outside supported schema

- **GIVEN** the ASR transcript requests a drawing operation outside the supported schema
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** `drawing.type` SHALL be `unsupported`
- **AND** the result SHALL include a message describing the limitation

#### Scenario: Unsupported destructive or canvas-wide operation

- **GIVEN** the ASR transcript requests delete, clear, group, layer, or stacking operations
- **WHEN** the backend performs semantic drawing interpretation in the first version
- **THEN** `drawing.type` SHALL be `unsupported`
- **AND** the response SHALL NOT include executable drawing actions

#### Scenario: Supported first-version action scope

- **GIVEN** the ASR transcript describes creating a rectangle, circle, text, or line
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** `drawing.type` MAY be `draw`
- **AND** the action SHALL use `create`

- **GIVEN** the ASR transcript describes a basic update such as color, size, or position change
- **AND** sufficient target context is available
- **WHEN** the backend performs semantic drawing interpretation
- **THEN** `drawing.type` MAY be `draw`
- **AND** the action SHALL use `update`

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
