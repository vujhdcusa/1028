import io
import json

from app import create_app
from app.extensions import db
from app.models import User
from app.services import assistant_service
from app.services.gemini_client import chat


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_live_search_is_limited_to_admission_and_competition_queries(tmp_path):
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True,
                      "UPLOAD_FOLDER": str(tmp_path), "ASSISTANT_WEB_SEARCH_ENABLED": True})
    with app.app_context():
        assert assistant_service._needs_live_search("請搜尋最新資訊類比賽")
        assert assistant_service._needs_live_search("幫我查最新二技招生簡章")
        assert not assistant_service._needs_live_search("幫我查今天的天氣")
        assert not assistant_service._needs_live_search("我的證照還差幾張？")


def test_gemini_live_search_requests_grounding_and_returns_safe_sources(tmp_path):
    sent = {}

    def opener(request, timeout):
        sent["body"] = json.loads(request.data)
        reply = {"candidates": [{"content": {"role": "model", "parts": [{"text": "有一項比賽。"}]},
                                  "groundingMetadata": {"groundingChunks": [
                                      {"web": {"uri": "https://contest.example.edu.tw/info", "title": "主辦單位競賽公告"}},
                                      {"web": {"uri": "javascript:alert(1)", "title": "bad"}},
                                  ]}}]}
        return FakeResponse(json.dumps(reply).encode())

    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True,
                      "AI_ENABLED": True, "AI_PROVIDER": "gemini", "AI_API_KEY": "test-key",
                      "ASSISTANT_MODEL": "gemini-test"})
    with app.app_context():
        result = chat([{"role": "user", "parts": [{"text": "找比賽"}]}], [], "規則", opener=opener, web_search=True)

    assert {"google_search": {}} in sent["body"]["tools"]
    assert result["_web_sources"] == [{"title": "主辦單位競賽公告", "url": "https://contest.example.edu.tw/info", "detail": "Gemini 即時網路查詢"}]


def test_assistant_exposes_grounded_sources_to_student(tmp_path, monkeypatch):
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True,
                      "UPLOAD_FOLDER": str(tmp_path), "ASSISTANT_WEB_SEARCH_ENABLED": True})
    with app.app_context():
        db.create_all()
        user = User(username="stu", display_name="學生", role="student")
        user.set_password("pw")
        db.session.add(user)
        db.session.commit()

        monkeypatch.setattr(assistant_service.gemini_client, "chat", lambda *args, **kwargs: {
            "role": "model", "parts": [{"text": "請參考主辦方公告。"}], "_provider": "gemini",
            "_web_sources": [{"title": "資訊競賽公告", "url": "https://contest.example.edu.tw", "detail": "Gemini 即時網路查詢"}],
        })
        result = assistant_service.ask(user, "請查最新資訊類比賽")

    assert "即時網路查詢" in result["steps"]
    assert result["sources"][0]["url"] == "https://contest.example.edu.tw"
