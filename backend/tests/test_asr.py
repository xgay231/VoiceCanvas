import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestAsrEndpoint:
    def test_asr_returns_text_on_success(self, client):
        """ASR 路由成功时返回识别文本"""
        mock_completion = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "你好世界"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]

        with patch("main.client") as mock_client:
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

    def test_asr_returns_error_on_failure(self, client):
        """ASR 路由失败时返回错误信息"""
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API key invalid")
            wav_bytes = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x00" * 16 + b"data" + b"\x00" * 4
            response = client.post(
                "/api/asr",
                files={"audio": ("test.wav", wav_bytes, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "API key invalid" in data["error"]

    def test_asr_missing_audio_returns_422(self, client):
        """缺少 audio 字段时返回 422"""
        response = client.post("/api/asr")
        assert response.status_code == 422
