# semantic-drawing-json Delta Specification

## MODIFIED Requirements

### Requirement: Structured Drawing Interpretation

The backend SHALL convert recognized or submitted natural-language drawing instructions into a structured JSON object that represents the drawing semantic result and can be consumed by the frontend drawing executor.

#### Scenario: Interpret text through a standalone endpoint for frontend execution

- **GIVEN** the frontend has a recognized transcript such as `画一个蓝色圆形在画布中央`
- **WHEN** the frontend submits that transcript to the standalone drawing interpretation endpoint
- **THEN** the endpoint SHALL return a `drawing` object with `version`, `type`, `actions`, `requires_clarification`, and `message`
- **AND** `drawing.type` SHALL be `draw` when executable create actions are available
- **AND** the response SHALL preserve enough structured action data for the frontend to create supported Fabric.js objects without parsing natural-language text
- **AND** the endpoint SHALL not require an audio upload

### Requirement: Safe Handling of Ambiguous or Unsupported Input

The semantic drawing result SHALL explicitly represent ambiguous, irrelevant, unsupported, or parser-error input with a user-facing message instead of inventing executable drawing actions.

#### Scenario: Non-draw result includes displayable message

- **GIVEN** the semantic drawing result has type `clarification`, `no_op`, `unsupported`, `parse_error`, or `semantic_error`
- **WHEN** the backend returns the drawing envelope to the frontend
- **THEN** the drawing envelope SHALL include a human-readable `message` suitable for display in the voice UI
- **AND** the drawing envelope SHALL NOT require the frontend to infer a message from raw model text
