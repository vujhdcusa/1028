"""所有測試共用的設定。"""
import pytest

from app.config import Config


@pytest.fixture(autouse=True)
def no_real_ai(monkeypatch):
    """測試一律不讀 .env 裡真的 AI 金鑰，避免連網路、花額度或洩漏金鑰。"""
    monkeypatch.setattr(Config, "AI_ENABLED", False)
    monkeypatch.setattr(Config, "AI_API_KEY", "")
