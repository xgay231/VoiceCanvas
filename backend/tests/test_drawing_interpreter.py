import json

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
    raw = '```json\n{"version":"1.0","type":"no_op","actions":[],"requires_clarification":false,"message":"不是绘图指令"}\n```'

    result = parse_model_json(raw)

    assert result["type"] == "no_op"
    assert result["message"] == "不是绘图指令"


def test_parse_model_json_rejects_non_json_text():
    with pytest.raises(ValueError, match="Model output is not valid JSON"):
        parse_model_json("我会帮你画一个圆")


def test_parse_model_json_rejects_json_array():
    with pytest.raises(ValueError, match="Model output must be a JSON object"):
        parse_model_json("[]")


# --- validate_drawing_payload ---

from drawing_interpreter import validate_drawing_payload


def test_validate_drawing_payload_accepts_valid_noop():
    payload = {
        "version": "1.0",
        "type": "no_op",
        "actions": [],
        "requires_clarification": False,
        "message": None,
    }
    # Should not raise
    validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_missing_version():
    payload = {
        "type": "draw",
        "actions": [],
        "requires_clarification": False,
        "message": None,
    }
    with pytest.raises(ValueError, match="version"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_unknown_type():
    payload = {
        "version": "1.0",
        "type": "invalid_type",
        "actions": [],
        "requires_clarification": False,
        "message": None,
    }
    with pytest.raises(ValueError, match="type"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_unknown_top_level_field():
    payload = {
        "version": "1.0",
        "type": "draw",
        "actions": [],
        "requires_clarification": False,
        "message": None,
        "extra_junk": True,
    }
    with pytest.raises(ValueError, match="Unknown top-level fields"):
        validate_drawing_payload(payload)


def test_validate_drawing_payload_accepts_create_rectangle():
    payload = {
        "version": "1.0",
        "type": "draw",
        "actions": [
            {
                "action": "create",
                "shape": "rectangle",
                "params": {"fill": "red"},
            }
        ],
        "requires_clarification": False,
        "message": None,
    }
    validate_drawing_payload(payload)


def test_validate_drawing_payload_rejects_create_with_unknown_shape():
    payload = {
        "version": "1.0",
        "type": "draw",
        "actions": [
            {
                "action": "create",
                "shape": "pyramid",
                "params": {},
            }
        ],
        "requires_clarification": False,
        "message": None,
    }
    with pytest.raises(ValueError, match="pyramid"):
        validate_drawing_payload(payload)


# --- interpret_drawing_text ---

from unittest.mock import MagicMock
from drawing_interpreter import interpret_drawing_text, parse_error_payload, semantic_error_payload


def _mock_client(message_json: str) -> MagicMock:
    """Build a mock OpenAI client that returns the given message content."""
    client = MagicMock()
    response = MagicMock()
    choice = MagicMock()
    choice.message.content = message_json
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


def test_interpret_drawing_returns_parsed_draw_envelope():
    raw_json = json.dumps({
        "version": "1.0", "type": "draw",
        "actions": [{"action": "create", "shape": "circle", "params": {"fill": "blue"}}],
        "requires_clarification": False, "message": None,
    })
    client = _mock_client(raw_json)

    result = interpret_drawing_text("画一个蓝色的圆", client)

    assert result["type"] == "draw"
    assert len(result["actions"]) == 1
    assert result["actions"][0]["shape"] == "circle"


def test_interpret_drawing_returns_clarification_for_incomplete():
    raw_json = json.dumps({
        "version": "1.0", "type": "clarification",
        "actions": [], "requires_clarification": True,
        "message": "请问要画什么形状？",
    })
    client = _mock_client(raw_json)

    result = interpret_drawing_text("画一个", client)

    assert result["type"] == "clarification"
    assert result["requires_clarification"] is True


def test_interpret_drawing_returns_noop_for_non_drawing():
    raw_json = json.dumps({
        "version": "1.0", "type": "no_op",
        "actions": [], "requires_clarification": False,
        "message": "不是绘图指令",
    })
    client = _mock_client(raw_json)

    result = interpret_drawing_text("今天天气怎么样", client)

    assert result["type"] == "no_op"


def test_interpret_drawing_returns_parse_error_on_invalid_json():
    client = _mock_client("这不是JSON")

    result = interpret_drawing_text("随便说点什么", client)

    assert result["type"] == "parse_error"


def test_interpret_drawing_returns_parse_error_on_missing_fields():
    raw_json = json.dumps({"version": "1.0"})
    client = _mock_client(raw_json)

    result = interpret_drawing_text("画一个", client)

    assert result["type"] == "parse_error"


def test_parse_error_payload_has_correct_shape():
    result = parse_error_payload("解析失败")

    assert result["version"] == "1.0"
    assert result["type"] == "parse_error"
    assert result["actions"] == []
    assert result["requires_clarification"] is False
    assert "解析失败" in result["message"]


def test_semantic_error_payload_has_correct_shape():
    result = semantic_error_payload()

    assert result["version"] == "1.0"
    assert result["type"] == "semantic_error"
    assert result["actions"] == []
    assert result["requires_clarification"] is False
