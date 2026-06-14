# drawing-canvas Specification

## Purpose
TBD - created by archiving change add-fabric-canvas. Update Purpose after archive.
## Requirements
### Requirement: Fabric canvas component renders a visible drawing area
The system SHALL provide a Vue 3 `DrawingCanvas` component that renders a Fabric.js-backed canvas with a visible border and light background or grid treatment.

#### Scenario: Canvas area is visible
- **WHEN** the frontend renders the drawing canvas component
- **THEN** the user sees a clearly bounded canvas area suitable for drawing interactions

### Requirement: Fabric canvas initializes during component mount
The system SHALL initialize a `fabric.Canvas` instance only after the Vue component has mounted and the canvas DOM element is available.

#### Scenario: Component mount initializes Fabric
- **WHEN** the drawing canvas component is mounted
- **THEN** a Fabric canvas instance is created for the rendered canvas element

### Requirement: Fabric canvas is disposed during component unmount
The system SHALL dispose the Fabric canvas instance when the drawing canvas component is unmounted.

#### Scenario: Component unmount releases Fabric resources
- **WHEN** the drawing canvas component is unmounted after initialization
- **THEN** the Fabric canvas instance is disposed to avoid memory leaks

### Requirement: Canvas demonstrates interactive Fabric content
The system SHALL add a default shape near the center of the canvas after initialization to demonstrate that Fabric is mounted and interactive.

#### Scenario: Default shape appears after initialization
- **WHEN** the Fabric canvas initialization completes
- **THEN** the canvas contains a visible default shape that can be selected or moved through Fabric interaction

### Requirement: Canvas instance is exposed to parent components

The system SHALL expose a controlled drawing execution entrypoint from the drawing canvas component so parent components can request supported Fabric.js drawing operations without directly constructing Fabric objects.

#### Scenario: Parent executes a supported drawing instruction

- **GIVEN** the drawing canvas component has initialized its Fabric canvas instance
- **AND** a parent component has a validated drawing envelope with `type` equal to `draw`
- **WHEN** the parent passes supported `create` actions to the drawing canvas execution entrypoint
- **THEN** the canvas SHALL add the corresponding Fabric objects
- **AND** the newly created objects SHALL be visible on the canvas

### Requirement: Canvas can be downloaded as an image
The system SHALL provide a download button in the top-right area of the canvas UI that exports the current Fabric canvas content as an image file.

#### Scenario: User downloads current canvas image
- **WHEN** the user clicks the canvas download button after initialization
- **THEN** the browser downloads an image representing the current canvas content

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

