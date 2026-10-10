"""自傳草稿的規則式「證據—疑點—建議」。"""

from app.services.autobiography_review import review_paragraphs


def test_review_uses_short_evidence_title_and_keeps_full_text():
    reviews = review_paragraphs(
        [{"title": "學習歷程與具體經驗", "text": "我負責後端。", "sources": ["F1"]}],
        [{"id": "F1", "text": "競賽：校園黑客松—三人一組完成報名網站"}],
        {"proud": "黑客松時負責後端 API。"},
    )

    assert reviews[0]["evidence"] == [{
        "id": "F1",
        "title": "競賽：校園黑客松",
        "text": "競賽：校園黑客松—三人一組完成報名網站",
    }]
    assert reviews[0]["issue"] == "暫未發現資料疑點"
    assert reviews[0]["icon"] == "✓"


def test_review_flags_answered_paragraph_without_evidence():
    reviews = review_paragraphs(
        [{"title": "學習歷程與具體經驗", "text": "我負責後端。", "sources": []}],
        [],
        {"proud": "黑客松時負責後端 API。"},
    )

    assert reviews[0]["issue"] == "這段沒有資料佐證，請補上具體經驗"
    assert reviews[0]["suggestion"] == "補一段你負責的部分與學到什麼"
    assert reviews[0]["icon"] == "⚠"


def test_review_prioritizes_unanswered_question_over_missing_evidence():
    reviews = review_paragraphs(
        [{"title": "困難與成長", "text": "（請補上你遇過的困難）", "sources": []}],
        [],
        {"challenge": ""},
    )

    assert reviews[0]["issue"] == "這題還沒回答"
    assert reviews[0]["suggestion"] == "補上遇到的困難、你的做法與結果"
    assert reviews[0]["icon"] == "⚠"
