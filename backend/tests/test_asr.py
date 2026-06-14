import json

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def _mock_asr_completion(content: str) -> MagicMock:
    mock_completion = MagicMock()
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    return mock_completion


def _mock_drawing_completion(content: str) -> MagicMock:
    return _mock_asr_completion(content)


WAV_BYTES = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x00" * 16 + b"data" + b"\x00" * 4


class TestAsrEndpoint:
    def test_asr_returns_text_on_success(self, client):
        """ASR 路由成功时返回识别文本"""
        draw_json = json.dumps({
            "version": "1.0", "type": "draw",
            "actions": [{"action": "create", "shape": "circle", "params": {"fill": "blue"}}],
            "requires_clarification": False, "message": None,
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = [
                _mock_asr_completion("画一个蓝色的圆"),
                _mock_drawing_completion(draw_json),
            ]
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", WAV_BYTES, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "画一个蓝色的圆"

    def test_asr_returns_drawing_field_on_success(self, client):
        """ASR 成功且语义解析成功时返回 drawing 字段"""
        draw_json = json.dumps({
            "version": "1.0", "type": "draw",
            "actions": [{"action": "create", "shape": "rectangle", "params": {"fill": "red"}}],
            "requires_clarification": False, "message": None,
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = [
                _mock_asr_completion("画一个红色矩形"),
                _mock_drawing_completion(draw_json),
            ]
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", WAV_BYTES, "audio/wav")},
            )

        data = response.json()
        assert data["drawing"]["type"] == "draw"
        assert data["drawing"]["actions"][0]["shape"] == "rectangle"

    def test_asr_returns_parse_error_when_drawing_parse_fails(self, client):
        """ASR 成功但语义模型返回非法 JSON 时 drawing.type = parse_error"""
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = [
                _mock_asr_completion("画一个圆"),
                _mock_drawing_completion("这不是JSON"),
            ]
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", WAV_BYTES, "audio/wav")},
            )

        data = response.json()
        assert data["success"] is True
        assert data["text"] == "画一个圆"
        assert data["drawing"]["type"] == "parse_error"

    def test_asr_returns_semantic_error_when_model_fails(self, client):
        """ASR 成功但语义模型调用失败时 drawing.type = semantic_error"""
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = [
                _mock_asr_completion("画一个圆"),
                Exception("Model unavailable"),
            ]
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", WAV_BYTES, "audio/wav")},
            )

        data = response.json()
        assert data["success"] is True
        assert data["text"] == "画一个圆"
        assert data["drawing"]["type"] == "semantic_error"

    def test_asr_returns_error_on_asr_failure(self, client):
        """ASR 路由失败时返回错误信息"""
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API key invalid")
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", WAV_BYTES, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "API key invalid" in data["error"]

    def test_asr_missing_audio_returns_422(self, client):
        """缺少 audio 字段时返回 422"""
        response = client.post("/api/asr")
        assert response.status_code == 422
