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
