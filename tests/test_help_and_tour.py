"""系統手冊（❓ 怎麼操作）與每頁網頁導覽。規格：引導卡片規格 1.5、Canva 第 21 頁、會議室 20261010-224756 #11 清單第 1 項。"""
import re
from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import AuditLog, StudentProfile, User
from app.services.journey_service import academic_year_of


@pytest.fixture()
def client():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        db.create_all()
        user = User(username="stu", display_name="stu", role="student")
        user.set_password("pw")
        db.session.add(user)
        db.session.flush()
        db.session.add(StudentProfile(user_id=user.id, student_no="s1", admission_year=academic_year_of(date.today()) - 2))
        db.session.add(AuditLog(user_id=user.id, action="student.welcome_done"))
        db.session.commit()
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})
    return client


def test_help_page_answers_common_questions_briefly(client):
    page = client.get("/help").get_data(as_text=True)
    questions = re.findall(r"<summary[^>]*>(.*?)</summary>", page, re.S)
    assert len(questions) >= 8
    assert any("證照" in q for q in questions)
    assert any("誰看得到" in q for q in questions)
    # 每個答案都短：一兩句話
    for answer in re.findall(r'<p class="help__answer">(.*?)</p>', page, re.S):
        assert len(re.sub(r"<[^>]+>", "", answer).strip()) <= 70, answer


def test_help_requires_login():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        db.create_all()
    assert app.test_client().get("/help").status_code in (302, 401)


def test_masthead_links_to_help_and_tour(client):
    page = client.get("/student/dashboard").get_data(as_text=True)
    assert 'href="/help"' in page
    assert "data-tour-start" in page


@pytest.mark.parametrize("url, minimum", [
    ("/student/dashboard", 4),
    ("/student/learning-profile", 2),
    ("/student/portfolio", 2),
    ("/student/targets", 1),
])
def test_pages_have_short_tour_steps(client, url, minimum):
    page = client.get(url).get_data(as_text=True)
    steps = re.findall(r'data-tour="([^"]+)"', page)
    assert len(steps) >= minimum, url
    for text in steps:
        assert len(text) <= 30, text
