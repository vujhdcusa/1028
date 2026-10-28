"""Gemini 暫時不可用時的 OpenAI 備援；全程使用假網路回應。"""
import io
import json
import urllib.error

from app import create_app
from app.services import gemini_client


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def app_with_fallback():
    return create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True,
                       "AI_ENABLED": True, "AI_PROVIDER": "gemini", "AI_API_KEY": "gemini-test",
                       "OPENAI_API_KEY": "openai-test", "OPENAI_ASSISTANT_MODEL": "gpt-test"})


def test_chat_uses_openai_when_gemini_rate_limited(monkeypatch):
    def broken(*_args, **_kwargs):
        raise gemini_client.AIUnavailable("AI 額度暫時用完了（每分鐘次數有限制），請過一分鐘再試。")

    seen = {}
    def openai(request, timeout):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        return FakeResponse(json.dumps({"choices": [{"message": {"content": "我已改用備援 AI 回答。"}}]}).encode())

    monkeypatch.setattr(gemini_client, "_post", broken)
    with app_with_fallback().app_context():
        result = gemini_client.chat([{"role": "user", "parts": [{"text": "畢業門檻？"}]}], [], "只回答科上問題", opener=openai)

    assert result["parts"][0]["text"] == "我已改用備援 AI 回答。"
    assert seen["url"].endswith("/chat/completions") and seen["auth"] == "Bearer openai-test"


def test_invalid_gemini_key_does_not_send_to_fallback(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise gemini_client.AIUnavailable("金鑰無效或沒有權限（HTTP 403），請確認金鑰是否正確。")

    monkeypatch.setattr(gemini_client, "_post", forbidden)
    with app_with_fallback().app_context():
        try:
            gemini_client.chat([{"role": "user", "parts": [{"text": "測試"}]}], [], "規則")
        except gemini_client.AIUnavailable as error:
            assert "HTTP 403" in str(error)
        else:
            raise AssertionError("無效金鑰不可自動改送備援服務")
