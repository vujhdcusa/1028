"""升學 Agent 共用引擎：AI 決定下一步、後端執行工具；AI 不能用時改走固定流程。

背景巡查：T1 檢查來源 → T2 擷取成候選校系。
使用者觸發：T6 排序校系 → T7 為已選的目標校系準備自傳草稿。
"""
import json

import pytest

from app import create_app
from app.extensions import db
from app.models import (AdmissionProgram, AgentTask, LearningProfileOutput, PublicSourceChange, StudentProfile,
                        StudentTarget, User)
from app.services import admission_agent_service, autobiography_service
from app.services.admission_service import import_seed_programs
from app.services.agent_advisor import advisor_decider, run_advisor
from app.services.agent_engine import AiDecider, Tool, run
from app.services.agent_patrol import run_patrol
from app.services.gemini_client import AIUnavailable

EXTRACTED = {"programs": [{"program_code": "208099", "admission_year": 116, "school_name": "測試科技大學",
                           "department_name": "資訊管理系", "admission_category": "管理類四",
                           "items": [{"name": "證照", "weight": 100, "categories": ["credential"]}]}]}
ANSWERS = {"motivation": "專二做網頁時喜歡上資管。", "proud": "黑客松負責後端。", "challenge": "", "future": "想學資料分析。"}


@pytest.fixture()
def app(tmp_path):
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True,
                      "UPLOAD_FOLDER": str(tmp_path), "AGENT_SOURCE_FOLDER": str(tmp_path / "agent")})
    with app.app_context():
        db.create_all()
        import_seed_programs()
        for username, role in (("admin", "admin"), ("stu", "student"), ("other", "student")):
            user = User(username=username, display_name=f"王{username}", role=role)
            user.set_password("pw")
            db.session.add(user)
        db.session.flush()
        for username, number in (("stu", "111534100"), ("other", "111534101")):
            student = User.query.filter_by(username=username).one()
            db.session.add(StudentProfile(user_id=student.id, student_no=number, class_name="資管科五甲",
                                          admission_year=111))
        db.session.commit()
        yield app


def user(name):
    return User.query.filter_by(username=name).one()


def program(code="208003"):
    return AdmissionProgram.query.filter_by(program_code=code).one()


def choose_target(student, code="208003"):
    db.session.add(StudentTarget(student_id=student.id, rule_version_id=program(code).id))
    db.session.commit()


def scripted(*decisions):
    """假的 AI：依序回傳決定。"""
    queue = list(decisions)
    return lambda goal, steps, tools: queue.pop(0)


def finish_plan(goal, steps, tools):
    return {"finish": "固定流程完成"}


# ---------- 引擎 ----------

def echo_tool(calls):
    def echo(text=""):
        calls.append(text)
        return {"summary": f"收到 {text}"}
    return Tool(name="echo", label="回聲", description="測試用", run=echo, params={"text": "內容"})


def test_engine_runs_ai_decisions_and_records_task(app):
    calls = []
    result = run(task_type="test_run", goal="測試", tools=[echo_tool(calls)], requester=user("admin"),
                 decide=scripted({"tool": "echo", "args": {"text": "甲"}}, {"finish": "完成了"}), fallback=finish_plan)

    assert calls == ["甲"]
    assert result["mode"] == "ai"
    assert result["summary"] == "完成了"
    task = db.session.get(AgentTask, result["task_id"])
    assert task.task_type == "test_run" and task.status == "succeeded"
    assert task.result_json["steps"] == [{"tool": "echo", "label": "回聲", "summary": "收到 甲"}]


def test_engine_reports_unknown_tool_and_keeps_going(app):
    result = run(task_type="test_run", goal="測試", tools=[], requester=user("admin"),
                 decide=scripted({"tool": "nope", "args": {}}, {"finish": "好"}), fallback=finish_plan)

    assert result["steps"][0]["summary"] == "沒有這個工具。"
    assert result["summary"] == "好"


def test_engine_falls_back_to_fixed_plan_when_ai_is_unavailable(app):
    def broken(goal, steps, tools):
        raise AIUnavailable("AI 額度暫時用完了")

    result = run(task_type="test_run", goal="測試", tools=[], requester=user("admin"), decide=broken,
                 fallback=finish_plan)

    assert result["mode"] == "rule"
    assert result["summary"] == "固定流程完成"
    assert "額度" in db.session.get(AgentTask, result["task_id"]).result_json["fallback_reason"]


def test_engine_stops_after_max_steps(app):
    calls = []
    forever = lambda goal, steps, tools: {"tool": "echo", "args": {"text": "再一次"}}

    result = run(task_type="test_run", goal="測試", tools=[echo_tool(calls)], requester=user("admin"),
                 decide=forever, fallback=finish_plan, max_steps=3)

    assert len(calls) == 3
    assert db.session.get(AgentTask, result["task_id"]).status == "stopped"


def test_ai_decider_turns_function_calls_into_decisions_and_replays_steps(app):
    seen = []

    def fake_chat(contents, declarations, instruction):
        seen.append(contents)
        if len(seen) == 1:
            return {"role": "model", "parts": [{"functionCall": {"name": "echo", "args": {"text": "乙"}}}]}
        return {"role": "model", "parts": [{"text": "總結"}]}

    calls = []
    result = run(task_type="test_run", goal="目標文字", tools=[echo_tool(calls)], requester=user("admin"),
                 decide=AiDecider("說明", chat=fake_chat), fallback=finish_plan)

    assert calls == ["乙"] and result["summary"] == "總結"
    second = seen[1]
    assert second[0]["parts"][0]["text"] == "目標文字"
    assert second[1]["parts"][0]["functionCall"]["name"] == "echo"
    assert second[2]["parts"][0]["functionResponse"]["response"]["result"]["summary"] == "收到 乙"


# ---------- 背景巡查（T1、T2）----------

def add_source():
    return admission_agent_service.add_source("技專校院招生委員會", url="https://example.edu.tw/brochure.pdf")


def test_patrol_fixed_plan_checks_sources_and_extracts_candidates(app):
    add_source()

    result = run_patrol(user("admin"), fetch=lambda url: (b"%PDF new", "application/pdf"),
                        generate=lambda prompt, schema, files: EXTRACTED, decide=None)

    created = AdmissionProgram.query.filter_by(program_code="208099").one()
    assert created.status == "candidate" and created.data_origin == "agent"
    assert [step["tool"] for step in result["steps"]] == ["check_sources", "list_pending_changes", "extract_change"]
    assert "候選" in result["summary"]
    assert PublicSourceChange.query.one().status == "extracted"


def test_patrol_without_ai_only_checks_and_leaves_changes_for_admin(app):
    add_source()

    result = run_patrol(user("admin"), fetch=lambda url: (b"%PDF new", "application/pdf"), decide=None)

    assert [step["tool"] for step in result["steps"]] == ["check_sources", "list_pending_changes"]
    assert "需要 AI" in result["summary"]
    assert PublicSourceChange.query.one().status == "candidate"


def test_patrol_ai_mode_follows_ai_decisions_and_rejects_bad_change_ids(app):
    add_source()
    decide = scripted({"tool": "check_sources", "args": {}},
                      {"tool": "extract_change", "args": {"change_id": "999"}},
                      {"tool": "list_pending_changes", "args": {}},
                      {"tool": "extract_change", "args": {"change_id": "1"}},
                      {"finish": "巡查完成，建立 1 個候選校系，等管理員核准。"})

    result = run_patrol(user("admin"), fetch=lambda url: (b"%PDF new", "application/pdf"),
                        generate=lambda prompt, schema, files: EXTRACTED, decide=decide)

    assert result["mode"] == "ai"
    assert "找不到" in result["steps"][1]["summary"]
    assert AdmissionProgram.query.filter_by(program_code="208099").count() == 1
    assert result["summary"].startswith("巡查完成")


def test_patrol_cli_command_prints_summary(app):
    output = app.test_cli_runner().invoke(args=["agent-patrol"]).output

    assert "巡查" in output


def test_admin_can_run_patrol_from_agent_page(app):
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "pw"})

    response = client.post("/admin/agent/patrol")

    assert response.status_code == 302
    assert AgentTask.query.filter_by(task_type="agent_patrol").count() == 1
    assert "讓 Agent 巡查一次" in client.get("/admin/agent").get_data(as_text=True)


# ---------- 使用者觸發（T6、T7）----------

def test_advisor_fixed_plan_ranks_and_drafts_for_a_chosen_target(app):
    student = user("stu")
    choose_target(student)
    autobiography_service.generate_draft(student, program(), ANSWERS)  # 學生之前回答過自傳問題
    before = LearningProfileOutput.query.count()

    result = run_advisor(student, decide=None)

    assert [step["tool"] for step in result["steps"]] == ["rank_programs", "list_my_targets", "draft_autobiography"]
    assert LearningProfileOutput.query.count() == before + 1
    assert "國立臺北商業大學" in result["summary"]
    assert any(link["endpoint"] == "student.autobiography" for link in result["links"])


def test_advisor_never_picks_a_target_for_the_student(app):
    student = user("stu")

    result = run_advisor(student, decide=None)

    assert StudentTarget.query.count() == 0
    assert [step["tool"] for step in result["steps"]] == ["rank_programs", "list_my_targets"]
    assert "目標校系" in result["summary"]


def test_advisor_asks_for_answers_before_drafting(app):
    student = user("stu")
    choose_target(student)

    result = run_advisor(student, decide=None)

    assert LearningProfileOutput.query.count() == 0
    assert "回答" in result["summary"]


def test_draft_tool_refuses_programs_outside_the_students_targets(app):
    student = user("stu")
    choose_target(student)
    autobiography_service.generate_draft(student, program(), ANSWERS)
    other = program("208001")
    decide = scripted({"tool": "draft_autobiography", "args": {"program_id": str(other.id)}}, {"finish": "好"})

    result = run_advisor(student, decide=decide)

    assert "目標校系" in result["steps"][0]["summary"]
    assert LearningProfileOutput.query.filter(LearningProfileOutput.content_json.isnot(None)).count() == 1


def test_advisor_never_sends_name_or_student_number_to_ai(app):
    student = user("stu")
    choose_target(student)
    sent = []

    def fake_chat(contents, declarations, instruction):
        sent.append(json.dumps([contents, instruction], ensure_ascii=False))
        if len(sent) == 1:
            return {"role": "model", "parts": [{"functionCall": {"name": "rank_programs", "args": {}}}]}
        return {"role": "model", "parts": [{"text": "建議先補證照。"}]}

    result = run_advisor(student, decide=advisor_decider(chat=fake_chat))

    assert result["summary"] == "建議先補證照。"
    assert all("王stu" not in text and "111534100" not in text for text in sent)


def login(app, username):
    client = app.test_client()
    client.post("/login", data={"username": username, "password": "pw"})
    return client


def test_student_runs_agent_and_sees_steps_only_on_their_own_run(app):
    choose_target(user("stu"))
    client = login(app, "stu")

    response = client.post("/student/agent/advise")

    assert response.status_code == 302
    page = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "排序校系" in page and "契合度不是錄取機率" in page
    assert login(app, "other").get(response.headers["Location"]).status_code == 404


def test_matching_page_has_agent_button(app):
    html = login(app, "stu").get("/student/matching").get_data(as_text=True)

    assert "/student/agent/advise" in html


def test_run_page_shows_taiwan_time(app):
    from datetime import datetime
    choose_target(user("stu"))
    client = login(app, "stu")
    location = client.post("/student/agent/advise").headers["Location"]
    task = AgentTask.query.filter_by(task_type="agent_advisor").one()
    task.created_at = datetime(2026, 10, 22, 2, 30)  # 資料庫存 UTC
    db.session.commit()

    assert "2026-10-22 10:30" in client.get(location).get_data(as_text=True)


def test_advisor_links_to_autobiography_when_answers_are_missing(app):
    choose_target(user("stu"))

    result = run_advisor(user("stu"), decide=None)

    assert any(link["endpoint"] == "student.autobiography" for link in result["links"])


def test_fetch_keeps_certificate_checks_but_accepts_school_certificates_without_strict_x509(monkeypatch):
    import ssl
    import urllib.request

    seen = {}

    class FakeResponse:
        headers = type("H", (), {"get_content_type": staticmethod(lambda: "text/html")})()

        def read(self, size):
            return b"<html></html>"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout, context=None):
        seen["context"] = context
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    admission_agent_service.fetch_url("https://www.jctv.ntut.edu.tw/enter/")

    context = seen["context"]
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    assert not context.verify_flags & ssl.VERIFY_X509_STRICT


# ---------- 網頁比對：不被人次計數器騙、看得懂 Big5 ----------

PAGE = "<html><body><h1>二技技優甄審</h1><p>網路報名 {date}</p><div>網站人次：{count}</div></body></html>"


def _fetcher(*pages):
    queue = list(pages)
    return lambda url: (queue.pop(0), "text/html")


def test_visitor_counter_change_is_not_an_update(app):
    source = add_source()
    fetch = _fetcher(PAGE.format(date="4/20", count="1666538").encode("utf-8"),
                     PAGE.format(date="4/20", count="1666539").encode("utf-8"))

    admission_agent_service.check_source(source, user("admin"), fetch=fetch)
    second = admission_agent_service.check_source(source, user("admin"), fetch=fetch)

    assert second.result_json["changed"] is False


def test_date_change_on_a_page_is_an_update(app):
    source = add_source()
    fetch = _fetcher(PAGE.format(date="4/20", count="1").encode("utf-8"),
                     PAGE.format(date="4/27", count="1").encode("utf-8"))

    admission_agent_service.check_source(source, user("admin"), fetch=fetch)
    second = admission_agent_service.check_source(source, user("admin"), fetch=fetch)

    assert second.result_json["changed"] is True


def test_big5_pages_are_read_as_chinese_text():
    text = admission_agent_service._html_to_text(PAGE.format(date="4/20", count="1").encode("cp950"))

    assert "二技技優甄審" in text and "網路報名" in text
