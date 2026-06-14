"""Drawing Interpreter — semantic parsing via mimo-v2.5-pro.

Chains ASR text → structured drawing JSON using MIMO's OpenAI-compatible API.
"""

import json
import re

SUPPORTED_TYPES = {"draw", "clarification", "no_op", "unsupported", "parse_error", "semantic_error"}
SUPPORTED_ACTIONS = {"create", "update"}
SUPPORTED_CREATE_SHAPES = {"rectangle", "circle", "text", "line"}
REQUIRED_TOP_LEVEL_FIELDS = {"version", "type", "actions", "requires_clarification", "message"}


def validate_drawing_payload(payload: dict) -> None:
    """Validate a parsed drawing envelope.

    Checks: required top-level fields, valid type enum, no unknown top-level
    fields, valid actions (create shapes, known action types).

    Args:
        payload: Parsed JSON dict from parse_model_json.

    Raises:
        ValueError: On any validation failure.
    """
    missing = REQUIRED_TOP_LEVEL_FIELDS - payload.keys()
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")

    unknown = payload.keys() - REQUIRED_TOP_LEVEL_FIELDS
    if unknown:
        raise ValueError(f"Unknown top-level fields: {', '.join(sorted(unknown))}")

    if payload["type"] not in SUPPORTED_TYPES:
        raise ValueError(f"Unknown type: {payload['type']}")

    for i, action in enumerate(payload["actions"]):
        action_type = action.get("action")
        if action_type not in SUPPORTED_ACTIONS:
            raise ValueError(f"Unknown action type at index {i}: {action_type}")
        if action_type == "create":
            shape = action.get("shape")
            if shape not in SUPPORTED_CREATE_SHAPES:
                raise ValueError(f"Unknown create shape at index {i}: {shape}")


def parse_model_json(raw_message: str) -> dict:
    """Parse model output to JSON dict.

    Handles markdown code fences (```json ... ```), plain JSON strings,
    and rejects non-JSON text or JSON arrays.

    Args:
        raw_message: Raw string from the model.

    Returns:
        Parsed JSON as a dict.

    Raises:
        ValueError: If input is not valid JSON or is not a JSON object.
    """
    cleaned = raw_message.strip()

    # Strip markdown code fences: ```json ... ``` or ``` ... ```
    fence_match = re.match(
        r"^```(?:json)?\s*\n?(.*?)\n?\s*```$",
        cleaned,
        re.DOTALL,
    )
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("Model output is not valid JSON")

    if not isinstance(parsed, dict):
        raise ValueError("Model output must be a JSON object")

    return parsed
