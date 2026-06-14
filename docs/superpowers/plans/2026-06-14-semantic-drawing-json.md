---
change: semantic-drawing-json
design-doc: docs/superpowers/specs/2026-06-14-semantic-drawing-json-design.md
base-ref: cf841d6510ce172a6a76704ff66fa1d9dd12e926
---

# Semantic Drawing JSON Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 为 VoiceCanvas 后端新增语义绘图 JSON 解释层，让 `/api/asr` 在保留原始转写文本的同时返回稳定、已校验的 `drawing` 结构，并提供独立的 `/api/interpret-drawing` 文本调试入口。

**Architecture:** `backend/main.py` 继续负责 FastAPI 路由、CORS、ASR 调用和响应编排；新增 `backend/drawing_interpreter.py` 负责 Prompt、`mimo-v2.5-pro` 调用、原始消息日志、JSON 解析、schema 校验和错误 envelope 构建。测试先覆盖纯函数，再覆盖独立文本端点，最后覆盖 `/api/asr` 与语义解释串联，确保 ASR 成功后语义失败不会丢失 `text`。

**Tech Stack:** Python 3、FastAPI、OpenAI-compatible MIMO client、pytest、FastAPI TestClient、OpenSpec Markdown specs。

---

## Scope Check

该 change 涉及一个后端语义解释子系统及其 API 串联，不包含前端执行器、不改 Fabric canvas 执行逻辑、不新增多轮对象记忆。任务拆分后每个任务都能独立测试并提交，符合单一计划范围。

## File Structure

- Modify: `openspec/changes/semantic-drawing-json/specs/semantic-drawing-json/spec.md`
  - 责任：确认 OpenSpec delta 覆盖结构化绘图解释、独立端点、ASR 响应扩展、错误与安全场景。
- Create: `backend/drawing_interpreter.py`
  - 责任：集中保存 `DRAWING_INTERPRETER_PROMPT`、模型调用、raw message 日志、JSON 解析、手写 schema 校验和标准错误 envelope。
- Modify: `backend/main.py`
  - 责任：新增 `/api/interpret-drawing`；将 `/api/asr` 编排为 ASR 转写成功后调用 `interpret_drawing_text`；ASR 失败保持 `success=false`。
- Create: `backend/tests/test_drawing_interpreter.py`
  - 责任：纯函数测试 `parse_model_json`、`validate_drawing_payload`、`interpret_drawing_text` 的成功、解析失败、校验失败和模型异常路径。
- Modify: `backend/tests/test_asr.py`
  - 责任：更新现有 `/api/asr` 测试，验证返回包含 `drawing` 字段，并覆盖语义成功、parse_error、semantic_error 和 ASR 失败。
- Create: `backend/tests/test_interpret_drawing_endpoint.py`
  - 责任：覆盖独立 `/api/interpret-drawing` 文本入口的 draw、clarification、no_op、unsupported、parse_error、semantic_error。

## Contract Summary

统一 `drawing` envelope：

```json
{
  "version": "1.0",
  "type": "draw",
  "actions": [],
  "requires_clarification": false,
  "message": null
}
```

允许的顶层 `type`：`draw`、`clarification`、`no_op`、`unsupported`、`parse_error`、`semantic_error`。

第一版允许的动作：

- `create`：仅支持 `rectangle`、`circle`、`text`、`line`。
- `update`：仅支持有足够目标上下文时的基础颜色、尺寸、位置变更。
- `delete`、`clear`、`group`、`layer`、stacking：必须返回 `unsupported`，不得返回可执行 actions。

---

### Task 1: OpenSpec Contract Patch

**Files:**
- Modify: `openspec/changes/semantic-drawing-json/specs/semantic-drawing-json/spec.md`

- [x] **Step 1: Inspect current delta spec**

Run:

```bash
cat openspec/changes/semantic-drawing-json/specs/semantic-drawing-json/spec.md
```

Expected: 文件包含 `Structured Drawing Interpretation`、`Stable JSON Model Output Contract`、`Safe Handling of Ambiguous or Unsupported Input`、`Server-side Parse and Validation Failure Path` 四组需求。

- [x] **Step 2: Patch missing contract details if absent**

If any listed requirement is missing, add the exact requirement block below to `openspec/changes/semantic-drawing-json/specs/semantic-drawing-json/spec.md` under `## ADDED Requirements`:

```markdown
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
```

- [x] **Step 3: Validate OpenSpec delta formatting**

Run:

```bash
openspec validate semantic-drawing-json --strict
```

Expected: command exits `0` and reports the change is valid. If `openspec` is unavailable in PATH, run the repository's documented OpenSpec validation command if present and record the exact command output in the task handoff.

- [x] **Step 4: Commit spec contract**

```bash
git add openspec/changes/semantic-drawing-json/specs/semantic-drawing-json/spec.md
git commit -m "spec: define semantic drawing json contract"
```

---

### Task 2: Interpreter Parse Tests

**Files:**
- Create: `backend/tests/test_drawing_interpreter.py`
- Later Modify: `backend/drawing_interpreter.py`

- [x] **Step 1: Write failing parse tests**

Create `backend/tests/test_drawing_interpreter.py` with this initial content:

```python
import pytest

from drawing_interpreter import parse_model_json


def test_parse_model_json_accepts_valid_object():
    raw = '{"version":"1.0","type":"draw","actions":[],"requires_clarification":false,"message":null}'

    result = parse_model_json(raw)

    assert result == {
        "version": "1.0",
        "type": "draw",
        "actions": [],
        "requires_clarification": False,
        "message": None,
    }


def test_parse_model_json_strips_markdown_code_fence():
    raw = '''```json
{"version":"1.0","type":"no_op","actions":[],"requires_clarification":false,"message":"不是绘图指令"}
```'''

    result = parse_model_json(raw)

    assert result["type"] == "no_op"
    assert result["message"] == "不是绘图指令"


def test_parse_model_json_rejects_non_json_text():
    with pytest.raises(ValueError, match="Model output is not valid JSON"):
        parse_model_json("我会帮你画一个圆")


def test_parse_model_json_rejects_json_array():
    with pytest.raises(ValueError, match="Model output must be a JSON object"):
        parse_model_json("[]")
```

- [x] **Step 2: Run tests to verify failure**

Run from `backend/`:

```bash
pytest tests/test_drawing_interpreter.py -v
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'drawing_interpreter'`.

- [x] **Step 3: Commit failing tests**

```bash
git add backend/tests/test_drawing_interpreter.py
git commit -m "test: cover drawing interpreter json parsing"
```

---

### Task 3: Interpreter Parse Implementation

**Files:**
- Create: `backend/drawing_interpreter.py`
- Test: `backend/tests/test_drawing_interpreter.py`

- [x] **Step 1: Add minimal parser implementation**

Create `backend/drawing_interpreter.py`:

```python
import json


DRAWING_INTERPRETER_PROMPT = """You are the VoiceCanvas drawing instruction parser.
Return one JSON object only. Do not include Markdown, code fences, or explanations.
"""


def parse_model_json(raw_message: str):
    text = raw_message.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Model output is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("Model output must be a JSON object")

    return payload
```

- [x] **Step 2: Run parser tests**

Run from `backend/`:

```bash
pytest tests/test_drawing_interpreter.py -v
```

Expected: all 4 tests PASS.

- [x] **Step 3: Commit parser implementation**

```bash
git add backend/drawing_interpreter.py backend/tests/test_drawing_interpreter.py
git commit -m "feat: parse drawing interpreter json output"
```

---

### Task 4: Interpreter Validation Tests

**Files:**
- Modify: `backend/tests/test_drawing_interpreter.py`
- Later Modify: `backend/drawing_interpreter.py`

- [x] **Step 1: Append failing validation tests**

Append to `backend/tests/test_drawing_interpreter.py`:

```python
from drawing_interpreter import validate_drawing_payload


def valid_create_payload():
    return {
        "version": "1.0",
        "type": "draw",
        "actions": [
            {
                "action": "create",
                "shape": "circle",
                "text": None,
                "style": {"fill": "blue", "stroke": None, "strokeWidth": None},
                "position": {"preset": "center", "x": None, "y": None},
                "size": {"preset": "medium", "width": None, "height": None, "radius": None},
            }
        ],
        "requires_clarification": False,
        "message": None,
    }


def test_validate_drawing_payload_accepts_valid_create():
    payload = valid_create_payload()

    result = validate_drawing_payload(payload)

    assert result == payload


def test_validate_drawing_payload_accepts_clarification():
    payload = {
        "version": "1.0",
        "type": "clarification",
        "actions": [],
        "requires_clarification": True,
        "message": "请说明要修改哪个对象",
    }

    result = validate_drawing_payload(payload)

    assert result == payload


def test_validate_drawing_payload_rejects_missing_version():
    payload = valid_create_payload()
    del payload["version"]

    with pytest.raises(ValueError, match="Missing required field: version"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_unknown_type():
    payload = valid_create_payload()
    payload["type"] = "animate"

    with pytest.raises(ValueError, match="Unsupported drawing type: animate"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_unknown_action():
    payload = valid_create_payload()
    payload["actions"][0]["action"] = "delete"

    with pytest.raises(ValueError, match="Unsupported drawing action: delete"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_actions_for_non_draw_type():
    payload = valid_create_payload()
    payload["type"] = "no_op"
    payload["message"] = "不是绘图指令"

    with pytest.raises(ValueError, match="Only draw results may include actions"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_unknown_top_level_field():
    payload = valid_create_payload()
    payload["debug"] = "raw"

    with pytest.raises(ValueError, match="Unknown top-level field: debug"):
        validate_drawing_payload(payload)
```

- [x] **Step 2: Run validation tests to verify failure**

Run from `backend/`:

```bash
pytest tests/test_drawing_interpreter.py -v
```

Expected: FAIL with `ImportError` or `AttributeError` for missing `validate_drawing_payload`.

- [x] **Step 3: Commit failing validation tests**

```bash
git add backend/tests/test_drawing_interpreter.py
git commit -m "test: cover drawing payload validation"
```

---

### Task 5: Interpreter Validation Implementation

**Files:**
- Modify: `backend/drawing_interpreter.py`
- Test: `backend/tests/test_drawing_interpreter.py`

- [x] **Step 1: Add validation constants and function**

Append to `backend/drawing_interpreter.py`:

```python
SUPPORTED_TYPES = {
    "draw",
    "clarification",
    "no_op",
    "unsupported",
    "parse_error",
    "semantic_error",
}
SUPPORTED_ACTIONS = {"create", "update"}
SUPPORTED_CREATE_SHAPES = {"rectangle", "circle", "text", "line"}
REQUIRED_TOP_LEVEL_FIELDS = {
    "version",
    "type",
    "actions",
    "requires_clarification",
    "message",
}


def validate_drawing_payload(payload):
    unknown_fields = set(payload) - REQUIRED_TOP_LEVEL_FIELDS
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise ValueError(f"Unknown top-level field: {field}")

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    if payload["version"] != "1.0":
        raise ValueError("Unsupported drawing version")

    drawing_type = payload["type"]
    if drawing_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported drawing type: {drawing_type}")

    actions = payload["actions"]
    if not isinstance(actions, list):
        raise ValueError("Field actions must be an array")

    if drawing_type != "draw" and actions:
        raise ValueError("Only draw results may include actions")

    if drawing_type == "draw":
        for action in actions:
            validate_drawing_action(action)

    if drawing_type in {"clarification", "no_op", "unsupported", "parse_error", "semantic_error"}:
        if not payload["message"]:
            raise ValueError(f"Message is required for {drawing_type}")

    return payload


def validate_drawing_action(action):
    if not isinstance(action, dict):
        raise ValueError("Drawing action must be an object")

    action_type = action.get("action")
    if action_type not in SUPPORTED_ACTIONS:
        raise ValueError(f"Unsupported drawing action: {action_type}")

    if action_type == "create":
        shape = action.get("shape")
        if shape not in SUPPORTED_CREATE_SHAPES:
            raise ValueError(f"Unsupported create shape: {shape}")

    if action_type == "update" and action.get("target_id"):
        raise ValueError("Update action must not fabricate target ids without context")
```

- [x] **Step 2: Run interpreter tests**

Run from `backend/`:

```bash
pytest tests/test_drawing_interpreter.py -v
```

Expected: all interpreter tests PASS.

- [x] **Step 3: Commit validation implementation**

```bash
git add backend/drawing_interpreter.py backend/tests/test_drawing_interpreter.py
git commit -m "feat: validate drawing interpreter payloads"
```

---

### Task 6: Interpreter Model Call Tests

**Files:**
- Modify: `backend/tests/test_drawing_interpreter.py`
- Later Modify: `backend/drawing_interpreter.py`

- [x] **Step 1: Append failing model-call tests**

Append to `backend/tests/test_drawing_interpreter.py`:

```python
from unittest.mock import MagicMock

from drawing_interpreter import interpret_drawing_text


def completion_with_message(content):
    completion = MagicMock()
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    completion.choices = [choice]
    return completion


def test_interpret_drawing_text_calls_mimo_pro_and_returns_valid_payload(capsys):
    mock_client = MagicMock()
    raw = '{"version":"1.0","type":"draw","actions":[{"action":"create","shape":"circle"}],"requires_clarification":false,"message":null}'
    mock_client.chat.completions.create.return_value = completion_with_message(raw)

    result = interpret_drawing_text("画一个蓝色圆形在画布中央", mock_client)

    assert result["type"] == "draw"
    assert result["actions"][0]["shape"] == "circle"
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "mimo-v2.5-pro"
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][1]["role"] == "user"
    assert "画一个蓝色圆形在画布中央" in call_kwargs["messages"][1]["content"]
    assert "[drawing_interpreter] raw model message:" in capsys.readouterr().out


def test_interpret_drawing_text_returns_parse_error_for_invalid_json():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = completion_with_message("不是 JSON")

    result = interpret_drawing_text("画一个圆", mock_client)

    assert result == {
        "version": "1.0",
        "type": "parse_error",
        "actions": [],
        "requires_clarification": False,
        "message": "Model output is not valid JSON",
    }


def test_interpret_drawing_text_returns_semantic_error_for_model_failure():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("timeout")

    result = interpret_drawing_text("画一个圆", mock_client)

    assert result == {
        "version": "1.0",
        "type": "semantic_error",
        "actions": [],
        "requires_clarification": False,
        "message": "Semantic interpreter unavailable",
    }
```

- [x] **Step 2: Run tests to verify failure**

Run from `backend/`:

```bash
pytest tests/test_drawing_interpreter.py -v
```

Expected: FAIL with missing `interpret_drawing_text`.

- [x] **Step 3: Commit failing model-call tests**

```bash
git add backend/tests/test_drawing_interpreter.py
git commit -m "test: cover drawing semantic model calls"
```

---

### Task 7: Interpreter Model Call Implementation

**Files:**
- Modify: `backend/drawing_interpreter.py`
- Test: `backend/tests/test_drawing_interpreter.py`

- [x] **Step 1: Replace prompt with constrained schema prompt**

In `backend/drawing_interpreter.py`, replace `DRAWING_INTERPRETER_PROMPT` with:

```python
DRAWING_INTERPRETER_PROMPT = """You are the VoiceCanvas drawing instruction parser.
Return one JSON object only. Do not include Markdown, code fences, or explanations.

Top-level schema:
{
  "version": "1.0",
  "type": "draw | clarification | no_op | unsupported",
  "actions": [],
  "requires_clarification": false,
  "message": null
}

Rules:
- Use type "draw" only for supported executable actions.
- Supported create shapes: rectangle, circle, text, line.
- Supported update actions: basic color, size, or position changes only when canvas_context identifies the target clearly.
- Do not invent target ids. If target context is missing for an update, return type "clarification" with requires_clarification true and an explanatory message.
- For unrelated non-drawing input, return type "no_op" with an explanatory message and no actions.
- For delete, clear, group, layer, stacking, or other unsupported operations, return type "unsupported" with an explanatory message and no actions.
- Prefer semantic presets for missing exact geometry: center, top, bottom, left, right, small, medium, large.
"""
```

- [x] **Step 2: Add envelope builders and model call function**

Append to `backend/drawing_interpreter.py`:

```python
def parse_error_payload(message):
    return {
        "version": "1.0",
        "type": "parse_error",
        "actions": [],
        "requires_clarification": False,
        "message": message,
    }


def semantic_error_payload():
    return {
        "version": "1.0",
        "type": "semantic_error",
        "actions": [],
        "requires_clarification": False,
        "message": "Semantic interpreter unavailable",
    }


def interpret_drawing_text(text, client, canvas_context=None):
    try:
        completion = client.chat.completions.create(
            model="mimo-v2.5-pro",
            messages=[
                {"role": "system", "content": DRAWING_INTERPRETER_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"text": text, "canvas_context": canvas_context},
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        raw_message = completion.choices[0].message.content
        print(f"[drawing_interpreter] raw model message: {raw_message}")
        payload = parse_model_json(raw_message)
        return validate_drawing_payload(payload)
    except ValueError as exc:
        return parse_error_payload(str(exc))
    except Exception:
        return semantic_error_payload()
```

- [x] **Step 3: Run interpreter tests**

Run from `backend/`:

```bash
pytest tests/test_drawing_interpreter.py -v
```

Expected: all interpreter tests PASS.

- [x] **Step 4: Commit model-call implementation**

```bash
git add backend/drawing_interpreter.py backend/tests/test_drawing_interpreter.py
git commit -m "feat: call mimo pro for drawing interpretation"
```

---

### Task 8: Standalone Endpoint Tests

**Files:**
- Create: `backend/tests/test_interpret_drawing_endpoint.py`
- Later Modify: `backend/main.py`

- [x] **Step 1: Write failing endpoint tests**

Create `backend/tests/test_interpret_drawing_endpoint.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def drawing_payload(drawing_type, message=None, actions=None, requires_clarification=False):
    return {
        "version": "1.0",
        "type": drawing_type,
        "actions": actions or [],
        "requires_clarification": requires_clarification,
        "message": message,
    }


def test_interpret_drawing_endpoint_returns_draw(client):
    drawing = drawing_payload(
        "draw",
        actions=[{"action": "create", "shape": "circle"}],
    )

    with patch("main.interpret_drawing_text", return_value=drawing) as mock_interpret:
        response = client.post("/api/interpret-drawing", json={"text": "画一个蓝色圆形"})

    assert response.status_code == 200
    data = response.json()
    assert data == {"success": True, "text": "画一个蓝色圆形", "drawing": drawing}
    mock_interpret.assert_called_once()


def test_interpret_drawing_endpoint_returns_clarification(client):
    drawing = drawing_payload("clarification", "请说明要修改哪个对象", requires_clarification=True)

    with patch("main.interpret_drawing_text", return_value=drawing):
        response = client.post("/api/interpret-drawing", json={"text": "把它改成红色"})

    assert response.status_code == 200
    assert response.json()["drawing"]["type"] == "clarification"
    assert response.json()["drawing"]["requires_clarification"] is True


def test_interpret_drawing_endpoint_returns_no_op(client):
    drawing = drawing_payload("no_op", "不是绘图指令")

    with patch("main.interpret_drawing_text", return_value=drawing):
        response = client.post("/api/interpret-drawing", json={"text": "今天天气怎么样"})

    assert response.status_code == 200
    assert response.json()["drawing"]["type"] == "no_op"


def test_interpret_drawing_endpoint_returns_unsupported(client):
    drawing = drawing_payload("unsupported", "暂不支持清空画布")

    with patch("main.interpret_drawing_text", return_value=drawing):
        response = client.post("/api/interpret-drawing", json={"text": "清空画布"})

    assert response.status_code == 200
    assert response.json()["drawing"]["type"] == "unsupported"


def test_interpret_drawing_endpoint_returns_parse_error(client):
    drawing = drawing_payload("parse_error", "Model output is not valid JSON")

    with patch("main.interpret_drawing_text", return_value=drawing):
        response = client.post("/api/interpret-drawing", json={"text": "画一个圆"})

    assert response.status_code == 200
    assert response.json()["drawing"]["type"] == "parse_error"


def test_interpret_drawing_endpoint_returns_semantic_error(client):
    drawing = drawing_payload("semantic_error", "Semantic interpreter unavailable")

    with patch("main.interpret_drawing_text", return_value=drawing):
        response = client.post("/api/interpret-drawing", json={"text": "画一个圆"})

    assert response.status_code == 200
    assert response.json()["drawing"]["type"] == "semantic_error"


def test_interpret_drawing_endpoint_requires_text(client):
    response = client.post("/api/interpret-drawing", json={})

    assert response.status_code == 422
```

- [x] **Step 2: Run endpoint tests to verify failure**

Run from `backend/`:

```bash
pytest tests/test_interpret_drawing_endpoint.py -v
```

Expected: FAIL with `404 Not Found` or patch failure because `/api/interpret-drawing` and `main.interpret_drawing_text` do not exist yet.

- [x] **Step 3: Commit failing endpoint tests**

```bash
git add backend/tests/test_interpret_drawing_endpoint.py
git commit -m "test: cover drawing interpretation endpoint"
```

---

### Task 9: Standalone Endpoint Implementation

**Files:**
- Modify: `backend/main.py`
- Test: `backend/tests/test_interpret_drawing_endpoint.py`

- [x] **Step 1: Import Pydantic and interpreter**

In `backend/main.py`, change imports to include:

```python
from pydantic import BaseModel

from drawing_interpreter import interpret_drawing_text
```

- [x] **Step 2: Add request model**

Add below the `client = OpenAI(...)` block in `backend/main.py`:

```python
class InterpretDrawingRequest(BaseModel):
    text: str
```

- [x] **Step 3: Add standalone endpoint**

Add below `health_check` and above `/api/asr`:

```python
@app.post("/api/interpret-drawing")
async def interpret_drawing(request: InterpretDrawingRequest):
    drawing = interpret_drawing_text(request.text, client)
    return {"text": request.text, "success": True, "drawing": drawing}
```

- [x] **Step 4: Run standalone endpoint tests**

Run from `backend/`:

```bash
pytest tests/test_interpret_drawing_endpoint.py -v
```

Expected: all standalone endpoint tests PASS.

- [x] **Step 5: Commit standalone endpoint**

```bash
git add backend/main.py backend/tests/test_interpret_drawing_endpoint.py
git commit -m "feat: add drawing interpretation endpoint"
```

---

### Task 10: ASR Integration Tests

**Files:**
- Modify: `backend/tests/test_asr.py`
- Later Modify: `backend/main.py`

- [x] **Step 1: Update `/api/asr` success test for drawing field**

Replace `test_asr_returns_text_on_success` in `backend/tests/test_asr.py` with:

```python
    def test_asr_returns_text_and_drawing_on_success(self, client):
        """ASR 路由成功时返回识别文本和结构化绘图 JSON"""
        mock_completion = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "你好世界"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        drawing = {
            "version": "1.0",
            "type": "no_op",
            "actions": [],
            "requires_clarification": False,
            "message": "不是绘图指令",
        }

        with patch("main.client") as mock_client, patch("main.interpret_drawing_text", return_value=drawing) as mock_interpret:
            mock_client.chat.completions.create.return_value = mock_completion
            wav_bytes = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x00" * 16 + b"data" + b"\x00" * 4
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", wav_bytes, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "你好世界"
        assert data["drawing"] == drawing
        mock_interpret.assert_called_once_with("你好世界", mock_client)
```

- [x] **Step 2: Append ASR parse_error and semantic_error tests**

Append inside `TestAsrEndpoint` in `backend/tests/test_asr.py`:

```python
    def test_asr_preserves_text_when_interpreter_returns_parse_error(self, client):
        """ASR 成功后语义解析失败时保留原始文本"""
        mock_completion = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "画一个圆"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        drawing = {
            "version": "1.0",
            "type": "parse_error",
            "actions": [],
            "requires_clarification": False,
            "message": "Model output is not valid JSON",
        }

        with patch("main.client") as mock_client, patch("main.interpret_drawing_text", return_value=drawing):
            mock_client.chat.completions.create.return_value = mock_completion
            wav_bytes = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x00" * 16 + b"data" + b"\x00" * 4
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", wav_bytes, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "画一个圆"
        assert data["drawing"]["type"] == "parse_error"

    def test_asr_preserves_text_when_interpreter_returns_semantic_error(self, client):
        """ASR 成功后语义模型不可用时保留原始文本"""
        mock_completion = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "画一个圆"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        drawing = {
            "version": "1.0",
            "type": "semantic_error",
            "actions": [],
            "requires_clarification": False,
            "message": "Semantic interpreter unavailable",
        }

        with patch("main.client") as mock_client, patch("main.interpret_drawing_text", return_value=drawing):
            mock_client.chat.completions.create.return_value = mock_completion
            wav_bytes = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x00" * 16 + b"data" + b"\x00" * 4
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", wav_bytes, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "画一个圆"
        assert data["drawing"]["type"] == "semantic_error"
```

- [x] **Step 3: Ensure ASR failure test asserts no drawing field**

In `test_asr_returns_error_on_failure`, after `assert "API key invalid" in data["error"]`, add:

```python
        assert "drawing" not in data
```

- [x] **Step 4: Run ASR tests to verify failure**

Run from `backend/`:

```bash
pytest tests/test_asr.py -v
```

Expected: FAIL because `/api/asr` does not yet include `drawing` on success.

- [x] **Step 5: Commit failing ASR integration tests**

```bash
git add backend/tests/test_asr.py
git commit -m "test: cover asr drawing response contract"
```

---

### Task 11: ASR Integration Implementation

**Files:**
- Modify: `backend/main.py`
- Test: `backend/tests/test_asr.py`

- [x] **Step 1: Update `/api/asr` success path**

In `backend/main.py`, replace:

```python
        return {"text": completion.choices[0].message.content, "success": True}
```

with:

```python
        text = completion.choices[0].message.content
        drawing = interpret_drawing_text(text, client)
        return {"text": text, "success": True, "drawing": drawing}
```

- [x] **Step 2: Preserve ASR failure behavior**

Keep the existing exception response in `backend/main.py` exactly as:

```python
    except Exception as e:
        return {"text": "", "success": False, "error": str(e)}
```

- [x] **Step 3: Run ASR tests**

Run from `backend/`:

```bash
pytest tests/test_asr.py -v
```

Expected: all ASR tests PASS.

- [x] **Step 4: Run endpoint tests**

Run from `backend/`:

```bash
pytest tests/test_interpret_drawing_endpoint.py -v
```

Expected: all standalone endpoint tests PASS.

- [x] **Step 5: Commit ASR integration**

```bash
git add backend/main.py backend/tests/test_asr.py backend/tests/test_interpret_drawing_endpoint.py
git commit -m "feat: include drawing interpretation in asr response"
```

---

### Task 12: Full Backend Verification

**Files:**
- Verify: `backend/drawing_interpreter.py`
- Verify: `backend/main.py`
- Verify: `backend/tests/test_drawing_interpreter.py`
- Verify: `backend/tests/test_interpret_drawing_endpoint.py`
- Verify: `backend/tests/test_asr.py`

- [x] **Step 1: Run all backend tests**

Run from `backend/`:

```bash
pytest tests/ -v
```

Expected: all backend tests PASS.

- [x] **Step 2: Run focused import smoke check**

Run from `backend/`:

```bash
python -c "from main import app; from drawing_interpreter import interpret_drawing_text; print(app.title, callable(interpret_drawing_text))"
```

Expected output includes:

```text
VoiceCanvas API True
```

- [x] **Step 3: Commit verification-only adjustments if any were required**

If Step 1 or Step 2 required code/test fixes, commit only those touched files:

```bash
git add backend/drawing_interpreter.py backend/main.py backend/tests/test_drawing_interpreter.py backend/tests/test_interpret_drawing_endpoint.py backend/tests/test_asr.py
git commit -m "fix: stabilize semantic drawing backend tests"
```

If no files changed, do not create an empty commit.

---

### Task 13: Frontend Compatibility Verification

**Files:**
- Verify: `frontend/package.json`
- Verify: `frontend/src` files indirectly through build

- [x] **Step 1: Run frontend build**

Run from `frontend/`:

```bash
npm run build
```

Expected: Vite build exits `0`. This confirms adding `drawing` to backend responses does not require immediate frontend changes and does not break existing frontend compilation.

- [x] **Step 2: Record frontend build failure if dependencies are missing**

If `npm run build` fails because dependencies are not installed, run:

```bash
npm install
npm run build
```

Expected: build exits `0` after dependency installation. If dependency installation is not allowed in the execution environment, record the exact failure and continue to backend verification evidence.

- [x] **Step 3: Commit lockfile only if dependency installation changed it**

If `npm install` changed `frontend/package-lock.json`, inspect the diff. Commit only if the dependency graph changed as a direct consequence of installing existing declared dependencies:

```bash
git add frontend/package-lock.json
git commit -m "chore: refresh frontend lockfile"
```

If no frontend files changed, do not create a commit.

---

### Task 14: OpenSpec and Change-State Verification

**Files:**
- Verify: `openspec/changes/semantic-drawing-json/tasks.md`
- Verify: `openspec/changes/semantic-drawing-json/specs/semantic-drawing-json/spec.md`

- [x] **Step 1: Run OpenSpec validation**

Run:

```bash
openspec validate semantic-drawing-json --strict
```

Expected: command exits `0`.

- [x] **Step 2: Mark OpenSpec tasks complete**

Update `openspec/changes/semantic-drawing-json/tasks.md` by changing every task checkbox from `- [x]` to `- [x]` after the corresponding implementation and verification evidence exists.

The completed file should retain the same sections:

```markdown
## 1. Spec and Contract

- [x] 1.1 定义 `semantic-drawing-json` capability spec，覆盖成功绘图、澄清、无操作、不支持、解析失败等场景。
- [x] 1.2 明确 `/api/asr` 扩展响应契约，保留 `text` 与 `success`，新增结构化 `drawing` 字段。

## 2. Backend Implementation

- [x] 2.1 在后端封装 `mimo-v2.5-pro` 语义解析调用，复用现有 MIMO OpenAI-compatible client 配置。
- [x] 2.2 设计并接入绘图语义解析 Prompt，要求模型稳定输出 JSON。
- [x] 2.3 将 mimo-v2.5-pro 原始消息输出到控制台日志，便于调试。
- [x] 2.4 实现 JSON 解析与基础 schema 校验，失败时返回 `parse_error` 结构。
- [x] 2.5 将 `/api/asr` 流程串联为 ASR 转写 → 语义解析 → 扩展响应。

## 3. Tests and Verification

- [x] 3.1 为 Prompt 输出解析/校验逻辑添加后端单元测试，覆盖合法 JSON、非 JSON、字段缺失、未知动作。
- [x] 3.2 为 `/api/asr` 添加或更新测试，验证返回包含原始文本和结构化 `drawing` 字段。
- [x] 3.3 运行后端测试，必要时运行前端构建确认响应字段扩展不破坏现有前端。
```

- [x] **Step 3: Commit task completion**

```bash
git add openspec/changes/semantic-drawing-json/tasks.md
git commit -m "chore: mark semantic drawing json tasks complete"
```

---

## Final Verification Checklist

Run these commands before handing off implementation as complete:

```bash
cd backend && pytest tests/ -v
cd frontend && npm run build
openspec validate semantic-drawing-json --strict
git status --short
```

Expected final state:

- Backend tests pass.
- Frontend build passes or dependency/environment failure is documented with exact output.
- OpenSpec validation passes.
- `git status --short` is clean after required commits.
- `/api/asr` success responses include `success=true`, original `text`, and validated `drawing`.
- `/api/asr` ASR failures include `success=false`, empty `text`, and `error`, with no `drawing`.
- `/api/interpret-drawing` accepts JSON body `{"text":"..."}` and returns the same `drawing` contract as `/api/asr`.

## Self-Review

- Spec coverage: covered OpenSpec contract in Task 1 and Task 14; `drawing_interpreter` module in Tasks 2-7; `/api/interpret-drawing` in Tasks 8-9; `/api/asr`串联 in Tasks 10-11; backend/frontend/OpenSpec verification in Tasks 12-14.
- Placeholder scan: no `TBD`, no generic “handle edge cases”, no undefined implementation-only references; every code-changing step includes exact code or exact replacement.
- Type consistency: all tasks use the same envelope fields `version`、`type`、`actions`、`requires_clarification`、`message`; helper names remain `parse_model_json`、`validate_drawing_payload`、`interpret_drawing_text`、`parse_error_payload`、`semantic_error_payload`.
