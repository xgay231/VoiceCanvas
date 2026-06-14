"""Drawing Interpreter — semantic parsing via mimo-v2.5-pro.

Chains ASR text → structured drawing JSON using MIMO's OpenAI-compatible API.
"""

import json
import re


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
