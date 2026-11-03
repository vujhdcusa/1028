"""資管科小助手（AI Agent）：會呼叫工具查資料、守權限、不保存對話內容。"""
import json
from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import AdmissionProgram, AgentTask, ClassAdvisor, CredentialRecord, StudentProfile, StudentTarget, User
from app.services import assistant_service
from app.services.admission_service import import_seed_programs
from app.services.knowledge_service import search


@pytest.fixture()
def app(tmp_path):
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True, "UPLOAD_FOLDER": str(tmp_path)})
    with app.app_context():
        db.create_all()
        import_seed_programs()
        for username, role in (("stu", "student"), ("other", "student"), ("teacher", "teacher"), ("admin", "admin")):
            user = User(username=username, display_name=username, role=role)
            user.set_password("pw")
            db.session.add(user)
        db.session.flush()
        stu = User.query.filter_by(username="stu").one()
        other = User.query.filter_by(username="other").one()
        db.session.add(StudentProfile(user_id=stu.id, student_no="111534100", class_name="資管科三甲", admission_year=113))
        db.session.add(StudentProfile(user_id=other.id, student_no="111534200", class_name="資管科三乙", admission_year=113))
        db.session.add(CredentialRecord(student_id=stu.id, credential_name="網頁設計丙級", level="丙級"))
        teacher = User.query.filter_by(username="teacher").one()
        db.session.add(ClassAdvisor(teacher_id=teacher.id, class_name="資管科三甲", school_year=115))
        db.session.commit()
    yield app


def user(app, username):
    return User.query.filter_by(username=username).one()


def scripted(*turns):
    """假的 Gemini：依序回傳設定好的回合（工具呼叫或文字），並記錄收到的內容。"""
    seen = []

    def chat(contents, tools, instruction):
        seen.append({"contents": json.loads(json.dumps(contents, ensure_ascii=False)), "tools": tools,
                     "instruction": instruction})
        return turns[len(seen) - 1]

    chat.seen = seen
    return chat


def call(name, **args):
    return {"role": "model", "parts": [{"functionCall": {"name": name, "args": args}}]}


def text(value):
    return {"role": "model", "parts": [{"text": value}]}


def test_knowledge_search_finds_graduation_rule():
    results = search("畢業門檻要幾張證照")

    assert results and "畢業門檻" in results[0]["title"]
    assert "三張" in results[0]["text"] or any("三張" in r["text"] for r in results)


def test_student_agent_calls_tools_then_answers(app):
    chat = scripted(call("search_department_rules", query="畢業門檻 證照"), call("get_my_overview"),
                    text("畢業門檻要三張證照，你目前有 1 張（網頁設計丙級），還差 2 張。"))
    with app.app_context():
        result = assistant_service.ask(user(app, "stu"), "我還差幾張證照才能畢業？", chat=chat)

    assert "還差 2 張" in result["answer"]
    assert result["steps"] == ["查你的資料", "查科上規定"]
    assert any("畢業門檻" in s["title"] for s in result["sources"])
    tool_reply = chat.seen[2]["contents"][-1]["parts"][0]["functionResponse"]
    assert tool_reply["name"] == "get_my_overview"
    assert "網頁設計丙級" in json.dumps(tool_reply, ensure_ascii=False)


def test_agent_can_cite_published_admission_source_with_year_and_checked_date(app):
    with app.app_context():
        program = AdmissionProgram.query.first()
        program.source_url = "https://official.example.edu.tw/116-brochure.pdf"
        program.checked_at = date(2026, 11, 4)
        db.session.commit()
        chat = scripted(call("get_latest_admission_sources"), text("請以官方簡章為準。"))
        result = assistant_service.ask(user(app, "stu"), "最新二技簡章和報名日期在哪裡？", chat=chat)

    assert result["steps"] == ["查官方招生來源"]
    assert any(source["url"] == "https://official.example.edu.tw/116-brochure.pdf" for source in result["sources"])
    assert any("資料年度：" in source["detail"] and "最後查核：2026-11-04" in source["detail"]
               for source in result["sources"])


def test_student_tools_do_not_include_teacher_tools(app):
    chat = scripted(text("好"))
    with app.app_context():
        assistant_service.ask(user(app, "stu"), "嗨", chat=chat)

    names = {tool["name"] for tool in chat.seen[0]["tools"]}
    assert "list_my_class_students" not in names and "get_student_overview" not in names
    assert "get_my_overview" in names


def test_teacher_cannot_query_student_from_other_class(app):
    chat = scripted(call("get_student_overview", student_no="111534200"), text("無法查詢"))
    with app.app_context():
        assistant_service.ask(user(app, "teacher"), "查 111534200", chat=chat)

    reply = chat.seen[1]["contents"][-1]["parts"][0]["functionResponse"]["response"]["result"]
    assert "不是你負責班級" in reply["error"]
    assert "other" not in json.dumps(reply, ensure_ascii=False)


def test_teacher_lists_only_own_class(app):
    chat = scripted(call("list_my_class_students"), text("本班 1 人"))
    with app.app_context():
        assistant_service.ask(user(app, "teacher"), "本班有誰？", chat=chat)

    students = chat.seen[1]["contents"][-1]["parts"][0]["functionResponse"]["response"]["result"]["students"]
    assert [s["student_no"] for s in students] == ["111534100"]


def test_conversation_text_is_not_stored(app):
    chat = scripted(call("get_my_overview"), text("這是回答"))
    with app.app_context():
        assistant_service.ask(user(app, "stu"), "我的祕密問題", chat=chat)
        task = AgentTask.query.filter_by(task_type="assistant_chat").one()

        stored = json.dumps(task.result_json, ensure_ascii=False)
        assert task.status == "succeeded"
        assert "我的祕密問題" not in stored and "這是回答" not in stored
        assert "查你的資料" in stored


def test_loop_stops_after_max_steps(app):
    chat = scripted(*[call("get_my_overview")] * assistant_service.MAX_STEPS)
    with app.app_context():
        result = assistant_service.ask(user(app, "stu"), "一直查", chat=chat)

    assert "換個問法" in result["answer"]
    assert len(chat.seen) == assistant_service.MAX_STEPS


def test_without_api_key_route_gives_friendly_message(app):
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})

    response = client.post("/assistant/ask", data={"message": "畢業門檻？", "history": "[]"})

    assert response.status_code == 200
    assert "沒有開啟" in response.get_json()["answer"]


def test_admin_cannot_use_assistant_route(app):
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "pw"})

    assert client.post("/assistant/ask", data={"message": "x"}).status_code == 403


def test_widget_shows_on_student_and_teacher_pages_only(app):
    student = app.test_client()
    student.post("/login", data={"username": "stu", "password": "pw"})
    teacher = app.test_client()
    teacher.post("/login", data={"username": "teacher", "password": "pw"})

    assert "data-assistant" in student.get("/student/dashboard").get_data(as_text=True)
    assert "data-assistant" in teacher.get("/teacher/dashboard").get_data(as_text=True)
    assert "data-assistant" not in app.test_client().get("/login").get_data(as_text=True)


def test_agent_returns_safe_navigation_links_and_waits_for_student_consent(app):
    chat = scripted(text("我會先幫你整理。"))
    with app.app_context():
        result = assistant_service.ask(user(app, "stu"), "幫我規劃下一步，成績 OCR 要怎麼核對？", chat=chat)
        plan = result["plan"]
        assert any(link["url"] == "/student/learning-profile" for link in result["links"])
        assert plan["status"] == "pending"
        task = db.session.get(AgentTask, plan["id"])
        assert task.status == "pending"
        assert "幫我規劃" not in json.dumps(task.result_json, ensure_ascii=False)


def test_student_must_approve_agent_plan_before_it_runs(app):
    chat = scripted(text("我會先幫你整理。"))
    with app.app_context():
        plan = assistant_service.ask(user(app, "stu"), "幫我規劃下一步", chat=chat)["plan"]
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})
    response = client.post(f"/assistant/plans/{plan['id']}/approve")

    assert response.status_code == 200
    assert response.get_json()["status"] == "succeeded"
    with app.app_context():
        assert db.session.get(AgentTask, plan["id"]).status == "succeeded"


def test_approved_agent_plan_saves_todos_and_student_can_read_history(app):
    chat = scripted(text("我會先幫你整理。"))
    with app.app_context():
        plan = assistant_service.ask(user(app, "stu"), "幫我規劃下一步", chat=chat)["plan"]
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})

    approved = client.post(f"/assistant/plans/{plan['id']}/approve").get_json()
    history = client.get("/assistant/plans").get_json()["plans"]

    assert approved["status"] == "succeeded"
    assert approved["todos"]
    assert all(todo["url"].startswith("/student/") for todo in approved["todos"])
    assert history[0]["id"] == plan["id"]
    assert history[0]["todos"] == approved["todos"]


def test_agent_todos_are_ranked_by_selected_program_weight_and_can_be_completed(app):
    with app.app_context():
        student = user(app, "stu")
        program = AdmissionProgram.query.first()
        db.session.add(StudentTarget(student_id=student.id, rule_version_id=program.id))
        db.session.commit()
        plan = assistant_service.ask(student, "幫我規劃下一步", chat=scripted(text("好")))["plan"]
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})

    approved = client.post(f"/assistant/plans/{plan['id']}/approve").get_json()
    weighted = [todo["weight"] for todo in approved["todos"] if todo.get("kind") == "target_gap"]
    assert weighted == sorted(weighted, reverse=True)
    first_open = next(index for index, todo in enumerate(approved["todos"]) if todo["status"] == "open")
    marked = client.post(f"/assistant/plans/{plan['id']}/todos/{first_open}/completed").get_json()
    reopened = client.post(f"/assistant/plans/{plan['id']}/todos/{first_open}/open").get_json()
    history = client.get("/assistant/plans").get_json()["plans"]

    assert marked["status"] == "completed"
    assert reopened["status"] == "open"
    assert history[0]["todos"][first_open]["status"] == "open"


def test_agent_prefetches_private_progress_without_sending_identity(app):
    chat = scripted(text("目前資料已整理。"))
    with app.app_context():
        result = assistant_service.ask(user(app, "stu"), "我的進度如何？", chat=chat)

    prompt = json.dumps(chat.seen[0]["contents"], ensure_ascii=False)
    assert "查你的資料" in result["steps"]
    assert "111534100" not in prompt and "資管科三甲" not in prompt


def test_agent_plan_history_is_private_to_each_student(app):
    chat = scripted(text("我會先幫你整理。"))
    with app.app_context():
        plan = assistant_service.ask(user(app, "stu"), "幫我規劃下一步", chat=chat)["plan"]
    client = app.test_client()
    client.post("/login", data={"username": "other", "password": "pw"})

    assert client.get("/assistant/plans").get_json()["plans"] == []
