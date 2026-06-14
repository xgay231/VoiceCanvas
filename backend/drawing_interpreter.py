"""Drawing Interpreter — semantic parsing via mimo-v2.5-pro.

Chains ASR text → structured drawing JSON using MIMO's OpenAI-compatible API.
"""

import json
import re
from typing import Optional

SUPPORTED_TYPES = {"draw", "clarification", "no_op", "unsupported", "parse_error", "semantic_error"}
SUPPORTED_ACTIONS = {"create", "update"}
SUPPORTED_CREATE_SHAPES = {"rectangle", "circle", "text", "line"}
REQUIRED_TOP_LEVEL_FIELDS = {"version", "type", "actions", "requires_clarification", "message"}

DRAWING_INTERPRETER_MODEL = "mimo-v2.5-pro"

DRAWING_INTERPRETER_PROMPT = """\
你是一个绘图指令解析器。用户通过语音输入描述想要在画布上绘制的内容，你负责将其解析为结构化的 JSON 绘图指令。

## 输出格式

你必须严格按照以下 JSON 格式输出，不包含任何其他文字：

{
  "version": "1.0",
  "type": "<类型>",
  "actions": [<动作列表>],
  "requires_clarification": <布尔值>,
  "message": <字符串或null>
}

## 类型枚举

- `draw`：用户想要绘图，且指令足够明确
- `clarification`：用户想绘图但信息不完整，需要追问
- `no_op`：用户输入与绘图无关（如"今天天气怎么样"）
- `unsupported`：用户想执行绘图相关操作但超出当前支持范围

## 支持的动作

仅支持以下动作类型和形状：

- `create` + `rectangle`：创建矩形
- `create` + `circle`：创建圆形
- `create` + `text`：创建文字
- `create` + `line`：创建线条

update 动作暂不支持具体参数，遇到更新需求时返回 `unsupported`。

## params 语义预设

params 中使用语义预设而非具体像素值：

- 位置：`position: { preset: "center" }`、`"top-left"`、`"bottom-right"` 等
- 尺寸：`size: { preset: "large" }`、`"medium"`、`"small"` 等
- 颜色：`fill: "red"`、`"blue"`、`"#ff0000"` 等
- 文字：`text: "你好"`
- 粗细/透明度等：`strokeWidth: 2`、`opacity: 0.5`

## 规则

1. 优先解析为 `draw`，仅当信息明显不完整时返回 `clarification`
2. `requires_clarification` 为 `true` 时，`message` 必须包含具体的追问内容
3. `no_op` 和 `unsupported` 时，`actions` 必须为空数组 `[]`
4. 未指定的语义预设不填入 params，由前端应用默认值
5. 颜色允许中英文（红→red, 蓝→blue 等），转为英文色名或 hex
"""


def _build_envelope(
    *,
    version: str = "1.0",
    envelope_type: str,
    actions: Optional[list] = None,
    requires_clarification: bool = False,
    message: Optional[str] = None,
) -> dict:
    return {
        "version": version,
        "type": envelope_type,
        "actions": actions or [],
        "requires_clarification": requires_clarification,
        "message": message,
    }


def parse_error_payload(detail: str) -> dict:
    """Build a parse_error envelope."""
    return _build_envelope(
        envelope_type="parse_error",
        message=f"模型输出解析失败: {detail}",
    )


def semantic_error_payload() -> dict:
    """Build a semantic_error envelope (model call failed)."""
    return _build_envelope(
        envelope_type="semantic_error",
        message="语义解析模型调用失败",
    )


def interpret_drawing_text(
    text: str,
    client,
    canvas_context: Optional[dict] = None,
) -> dict:
    """Parse user text into a structured drawing envelope via mimo-v2.5-pro.

    Args:
        text: The user's transcribed speech text.
        client: An initialized OpenAI-compatible client.
        canvas_context: Optional canvas state for context-aware parsing (reserved for v2).

    Returns:
        A drawing envelope dict (draw/clarification/no_op/unsupported/parse_error/semantic_error).
    """
    try:
        response = client.chat.completions.create(
            model=DRAWING_INTERPRETER_MODEL,
            messages=[
                {"role": "system", "content": DRAWING_INTERPRETER_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=512,
        )
        raw_message = response.choices[0].message.content
        print(f"[drawing_interpreter] raw model response: {raw_message}")
    except Exception as exc:
        print(f"[drawing_interpreter] model call failed: {exc}")
        return semantic_error_payload()

    try:
        payload = parse_model_json(raw_message)
    except ValueError as exc:
        return parse_error_payload(str(exc))

    try:
        validate_drawing_payload(payload)
    except ValueError as exc:
        return parse_error_payload(str(exc))

    return payload


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
