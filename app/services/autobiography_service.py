"""AI 自傳小幫手：學生先回答幾題，AI 再用「回答＋已確認的六類資料＋目標校系加權」寫草稿。

防止 AI 亂寫的做法：
1. 把學生資料整理成有編號的事實（F1、F2…），AI 只能引用這些事實和學生的回答。
2. 每一段都要列出用到的事實編號，不存在的編號會被濾掉。
3. 草稿一定要學生自己看過、修改、儲存，才會放進備審 Word。

草稿存在 learning_profile_outputs（output_type="autobiography_ai"），不需要新資料表。
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models import CredentialRecord, LearningCourseRecord, LearningProfileOutput, Portfolio
from app.services.gap_service import ALL_LABELS
from app.services.gemini_client import AIUnavailable, ai_ready, generate_json
from app.services.journey_service import CATEGORY_LABELS

OUTPUT_TYPE = "autobiography_ai"

# 學生按過「確認」的經歷；submitted 是舊的專題送審流程，也代表學生確認過
CONFIRMED_PORTFOLIO_STATUSES = ("confirmed", "submitted")

# 問題（key, 題目, 提示）。要改題目只要改這裡。
QUESTIONS = [
    ("motivation", "為什麼想繼續讀資管，或特別想讀這個系？", "例如：哪一門課、哪一次經驗讓你確定方向"),
    ("proud", "五年中最有成就感的一件事是什麼？你負責做了什麼？", "寫你自己做的部分，越具體越好"),
    ("challenge", "遇過最大的困難是什麼？你怎麼解決？", "可以是課業、專題或團隊合作"),
    ("future", "進二技後想學什麼？之後想做什麼工作？", "和這個系的課程或特色連起來會更好"),
]

PARAGRAPH_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "paragraphs": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "text": {"type": "STRING"},
                    "sources": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["title", "text", "sources"],
            },
        },
    },
    "required": ["paragraphs"],
}


def build_facts(student, program):
    """把學生已確認的資料整理成編號事實，並附上目標校系的評分項目與加權。

    只收學生確認過的資料：成績與證照要 confirmation_status 是 confirmed，經歷要學生按過「確認」。
    """
    lines = []
    for course in (LearningCourseRecord.query.filter_by(student_id=student.id, confirmation_status="confirmed")
                   .order_by(LearningCourseRecord.id)):
        score = f"{course.score} 分" if course.score is not None else (course.status_mark or "")
        lines.append(f"成績：{course.course_name}（{course.school_year or '?'} 年級，{score}）")
    for credential in (CredentialRecord.query.filter_by(student_id=student.id, confirmation_status="confirmed")
                       .order_by(CredentialRecord.id)):
        lines.append(f"證照：{credential.credential_name}" + (f"（{credential.level}）" if credential.level else ""))
    for record in (Portfolio.query.filter_by(student_id=student.id)
                   .filter(Portfolio.status.in_(CONFIRMED_PORTFOLIO_STATUSES)).order_by(Portfolio.id)):
        label = CATEGORY_LABELS.get(record.category)
        if label:
            source = "" if record.source == "student" else f"（來源：{record.source_label}）"
            lines.append(f"{label}：{record.title}" + (f"—{record.description}" if record.description else "") + source)
    items = [{"id": f"F{index}", "text": text} for index, text in enumerate(lines, start=1)]
    weights = [{
        "name": item.source_item_name,
        "weight": item.weight_percent,
        "categories": "、".join(ALL_LABELS.get(key, key) for key in item.category_keys),
    } for item in sorted(program.items, key=lambda i: -i.weight_percent)]
    return {"items": items, "weights": weights}


def _prompt(student, program, facts, answers):
    fact_lines = "\n".join(f"{fact['id']}. {fact['text']}" for fact in facts["items"]) or "（沒有資料）"
    weight_lines = "\n".join(f"- {w['name']}：{w['weight']}%（{w['categories']}）" for w in facts["weights"])
    answer_lines = "\n".join(f"- {question}\n  回答：{answers.get(key) or '（未回答）'}" for key, question, _ in QUESTIONS)
    return f"""你是五專資管科學生的自傳寫作助手。請幫學生寫申請「{program.school_name} {program.department_name}」的自傳草稿。

規則：
1. 使用繁體中文、第一人稱，語氣真誠自然，像高職／五專學生寫的，不要浮誇或使用空泛形容詞。
2. 只能使用下面的「學生資料」和「學生回答」，不得編造任何獎項、分數、證照、職位或經歷。資料不足就少寫，不要補。
3. 學生沒回答的題目，那一段的 text 只寫「（請補上：題目內容）」，sources 給空陣列；不要從其他資料推想他的感受、心得或經過。
4. 依校系加權，把加權高的項目相關經驗寫得比較完整。
5. 分成 4 段：學習動機、學習歷程與具體經驗、困難與成長、未來規劃。總長約 600～900 字。
6. 每段的 sources 列出這段用到的學生資料編號（例如 F2）；只用到學生回答就給空陣列。

學生：{student.display_name}

學生資料（只能引用這些）：
{fact_lines}

目標校系的評分項目與加權：
{weight_lines}

學生回答：
{answer_lines}
"""


def _demo_paragraphs(facts, answers):
    """沒有接上 AI 時的示範草稿：只把學生的回答和資料排好，明白標示不是 AI 寫的。"""
    experience = [f for f in facts["items"] if f["text"].split("：", 1)[0] in ("競賽", "活動", "幹部經歷")][:3]
    titles = "、".join(f["text"].split("：", 1)[1].split("—")[0] for f in experience)
    proud = answers.get("proud") or "（請補上你最有成就感的經驗）"
    return [
        {"title": "學習動機", "text": answers.get("motivation") or "（請補上你想讀這個系的原因）", "sources": []},
        {"title": "學習歷程與具體經驗", "text": proud + (f"另外，我也參與了{titles}。" if titles else ""),
         "sources": [f["id"] for f in experience]},
        {"title": "困難與成長", "text": answers.get("challenge") or "（請補上你遇過的困難與解決方式）", "sources": []},
        {"title": "未來規劃", "text": answers.get("future") or "（請補上進二技後的學習計畫）", "sources": []},
    ]


def generate_draft(student, program, answers, generate=None, api_key=None):
    """產生並儲存草稿。generate 是呼叫 AI 的函式（測試時可以換成假的）。

    api_key：學生自己的 Gemini 金鑰，只在這次呼叫用，**不會**寫進資料庫或任何紀錄。
    """
    facts = build_facts(student, program)
    known = {fact["id"] for fact in facts["items"]}
    answers = {key: (answers.get(key) or "").strip()[:1000] for key, _, _ in QUESTIONS}
    if generate is None and not api_key and not ai_ready():
        paragraphs, provider = _demo_paragraphs(facts, answers), "demo"
    else:
        prompt = _prompt(student, program, facts, answers)
        result = generate(prompt, PARAGRAPH_SCHEMA) if generate else generate_json(prompt, PARAGRAPH_SCHEMA, api_key=api_key)
        paragraphs = [{
            "title": str(p.get("title", "")).strip()[:30],
            "text": str(p.get("text", "")).strip(),
            "sources": [s for s in p.get("sources", []) if s in known],
        } for p in result.get("paragraphs", []) if str(p.get("text", "")).strip()]
        if not paragraphs:
            raise AIUnavailable("AI 沒有產生內容，請再試一次。")
        provider = "gemini"
    output = LearningProfileOutput(
        student_id=student.id,
        output_type=OUTPUT_TYPE,
        content_json={
            "program_id": program.id,
            "answers": answers,
            "paragraphs": paragraphs,
            "facts": facts["items"],
            "provider": provider,
            "edited": False,
        },
        source_snapshot_json={"program_id": program.id, "fact_count": len(facts["items"]),
                              "generated_at": datetime.now(timezone.utc).isoformat()},
    )
    db.session.add(output)
    db.session.commit()
    return output


def versions(student, program):
    """同一位學生、同一個校系的所有自傳版本（舊到新）。"""
    outputs = (LearningProfileOutput.query.filter_by(student_id=student.id, output_type=OUTPUT_TYPE)
               .order_by(LearningProfileOutput.id).all())
    return [o for o in outputs if o.content_json.get("program_id") == program.id]


def version_of(output):
    """這一版是第幾版。新資料存在 content_json["version"]；舊資料依建立順序推算。"""
    if output.content_json.get("version"):
        return output.content_json["version"]
    earlier = (LearningProfileOutput.query.filter(
        LearningProfileOutput.student_id == output.student_id,
        LearningProfileOutput.output_type == OUTPUT_TYPE,
        LearningProfileOutput.id <= output.id,
    ).all())
    return sum(1 for o in earlier if o.content_json.get("program_id") == output.content_json.get("program_id"))


def latest_draft(student, program):
    outputs = (LearningProfileOutput.query.filter_by(student_id=student.id, output_type=OUTPUT_TYPE)
               .order_by(LearningProfileOutput.id.desc()).all())
    return next((o for o in outputs if o.content_json.get("program_id") == program.id), None)


def save_edits(output, texts):
    """學生逐段修改後儲存。texts 是每一段的新文字（順序和原本一樣）。"""
    content = dict(output.content_json)
    paragraphs = [dict(p) for p in content["paragraphs"]]
    for paragraph, text in zip(paragraphs, texts):
        paragraph["text"] = text.strip()
    content["paragraphs"] = paragraphs
    content["edited"] = True
    output.content_json = content
    db.session.commit()
