import json

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def _mock_completion(content: str) -> MagicMock:
    mock_completion = MagicMock()
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    return mock_completion


class TestInterpretDrawingEndpoint:
    def test_returns_draw_envelope(self, client):
        """绘图指令返回 draw 类型 envelope"""
        raw = json.dumps({
            "version": "1.0", "type": "draw",
            "actions": [{"action": "create", "shape": "circle", "params": {"fill": "blue"}}],
            "requires_clarification": False, "message": None,
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion(raw)
            response = client.post("/api/interpret-drawing", json={"text": "画一个蓝色的圆"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["drawing"]["type"] == "draw"
        assert data["drawing"]["actions"][0]["shape"] == "circle"

    def test_returns_complete_drawing_contract_for_frontend_execution(self, client):
        raw = json.dumps({
            "version": "1.0",
            "type": "draw",
            "actions": [
                {"action": "create", "shape": "rectangle", "params": {"fill": "#2563eb"}}
            ],
            "requires_clarification": False,
            "message": None,
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion(raw)
            response = client.post("/api/interpret-drawing", json={"text": "画一个蓝色矩形"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert set(data["drawing"].keys()) == {
            "version",
            "type",
            "actions",
            "requires_clarification",
            "message",
        }
        assert data["drawing"]["version"] == "1.0"
        assert data["drawing"]["type"] == "draw"
        assert data["drawing"]["actions"][0]["shape"] == "rectangle"
        assert data["drawing"]["requires_clarification"] is False
        assert data["drawing"]["message"] is None

    def test_returns_clarification(self, client):
        """信息不完整时返回 clarification"""
        raw = json.dumps({
            "version": "1.0", "type": "clarification",
            "actions": [], "requires_clarification": True,
            "message": "请问要画什么形状？",
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion(raw)
            response = client.post("/api/interpret-drawing", json={"text": "画一个"})

        data = response.json()
        assert data["success"] is True
        assert data["drawing"]["type"] == "clarification"
        assert data["drawing"]["requires_clarification"] is True
        assert data["drawing"]["message"]

    def test_returns_noop(self, client):
        """非绘图指令返回 no_op"""
        raw = json.dumps({
            "version": "1.0", "type": "no_op",
            "actions": [], "requires_clarification": False,
            "message": "不是绘图指令",
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion(raw)
            response = client.post("/api/interpret-drawing", json={"text": "今天天气怎么样"})

        data = response.json()
        assert data["success"] is True
        assert data["drawing"]["type"] == "no_op"
        assert data["drawing"]["message"]

    def test_returns_unsupported(self, client):
        """不支持的操作返回 unsupported"""
        raw = json.dumps({
            "version": "1.0", "type": "unsupported",
            "actions": [], "requires_clarification": False,
            "message": "暂不支持旋转操作",
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion(raw)
            response = client.post("/api/interpret-drawing", json={"text": "把圆形旋转45度"})

        data = response.json()
        assert data["success"] is True
        assert data["drawing"]["type"] == "unsupported"
        assert data["drawing"]["message"]

    def test_returns_parse_error_on_invalid_json(self, client):
        """模型返回非 JSON 时返回 parse_error"""
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion("这不是JSON")
            response = client.post("/api/interpret-drawing", json={"text": "随便说点什么"})

        data = response.json()
        assert data["success"] is True
        assert data["drawing"]["type"] == "parse_error"
        assert data["drawing"]["message"]

    def test_returns_semantic_error_on_api_failure(self, client):
        """模型调用失败时返回 semantic_error"""
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("Model unavailable")
            response = client.post("/api/interpret-drawing", json={"text": "画一个圆"})

        data = response.json()
        assert data["success"] is True
        assert data["drawing"]["type"] == "semantic_error"
        assert data["drawing"]["message"]

    def test_returns_422_on_missing_text(self, client):
        """缺少 text 字段时返回 422"""
        response = client.post("/api/interpret-drawing", json={})
        assert response.status_code == 422
