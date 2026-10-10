"""公開首頁與小助手要「一兩句短話」：文字太長就失敗。"""
import re

from app import create_app
from app.content.five_year_plan import FIVE_YEAR_PLAN, NEXT_STOPS

MAX_LINE = 30


def test_five_year_plan_lines_are_short():
    for stop in FIVE_YEAR_PLAN:
        assert len(stop["summary"]) <= MAX_LINE, stop
        assert len(stop["keep"]) <= 3
    for stop in NEXT_STOPS:
        assert len(stop["text"]) <= MAX_LINE, stop


def test_landing_page_paragraphs_are_short():
    html = create_app({"TESTING": True}).test_client().get("/").get_data(as_text=True)
    for tag in ("cover__lead", "chapter__lead"):
        for text in re.findall(rf'class="{tag}">(.*?)</p>', html, re.S):
            assert len(text.strip()) <= MAX_LINE * 2, text
    body = re.sub(r"<(script|style)[\s\S]*?</\1>|<[^>]+>", "", html)
    assert len(re.sub(r"\s+", "", body)) < 1400
