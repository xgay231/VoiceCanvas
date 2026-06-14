# drawing-canvas Delta Specification

## MODIFIED Requirements

### Requirement: Canvas instance is exposed to parent components

The system SHALL expose a controlled drawing execution entrypoint from the drawing canvas component so parent components can request supported Fabric.js drawing operations without directly constructing Fabric objects.

#### Scenario: Parent executes a supported drawing instruction

- **GIVEN** the drawing canvas component has initialized its Fabric canvas instance
- **AND** a parent component has a validated drawing envelope with `type` equal to `draw`
- **WHEN** the parent passes supported `create` actions to the drawing canvas execution entrypoint
- **THEN** the canvas SHALL add the corresponding Fabric objects
- **AND** the newly created objects SHALL be visible on the canvas

### Requirement: Canvas executes basic JSON drawing create actions

The system SHALL map supported structured drawing `create` actions to Fabric.js objects for basic shapes.

#### Scenario: Create basic shapes from drawing actions

- **GIVEN** a drawing envelope contains supported `create` actions for rectangle, circle, text, or line
- **WHEN** the frontend executes the drawing envelope
- **THEN** the canvas SHALL create the matching Fabric.js objects using whitelisted geometry and style fields
- **AND** semantic placement or missing optional fields SHALL resolve to safe visible defaults

#### Scenario: Unknown drawing action does not crash the page

- **GIVEN** a drawing envelope contains an unknown action type or unsupported shape
- **WHEN** the frontend attempts to execute the drawing envelope
- **THEN** the unsupported action SHALL NOT be executed
- **AND** the page SHALL remain interactive
- **AND** the user SHALL receive a message indicating that part of the drawing instruction could not be executed

### Requirement: Voice UI displays drawing interpretation messages

The system SHALL display backend drawing interpretation messages for non-draw results without modifying the canvas.

#### Scenario: Non-draw envelope shows message and leaves canvas unchanged

- **GIVEN** the frontend receives a drawing envelope with type `clarification`, `no_op`, `unsupported`, `parse_error`, or `semantic_error`
- **WHEN** the voice UI handles the envelope
- **THEN** it SHALL display the envelope `message` to the user
- **AND** it SHALL NOT add, remove, or update Fabric canvas objects
- **AND** the original recognized transcript SHALL remain visible in the recognition history
