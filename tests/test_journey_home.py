from datetime import date, datetime, timedelta, timezone

import pytest

from app import create_app
from app.extensions import db
from app.models import AuditLog, LearningCourseRecord, Portfolio, StudentProfile, User
from app.services.journey_home import RETURN_DAYS, journey_home
from app.services.journey_service import academic_year_of


@pytest.fixture()
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        db.create_all()
        user = User(username="stu", display_name="stu", role="student")
        user.set_password("pw")
        db.session.add(user)
        db.session.flush()
        db.session.add(StudentProfile(user_id=user.id, student_no="s1",
                                      admission_year=academic_year_of(date.today()) - 2))  # 專三
        db.session.add(AuditLog(user_id=user.id, action="student.welcome_done"))
        db.session.commit()
        yield app


def student():
    return User.query.filter_by(username="stu").one()


def test_five_stops_and_current_year(app):
    with app.test_request_context():
        view = journey_home(student())
    assert [stop["state"] for stop in view["stops"]] == ["past", "past", "now", "future", "future"]
    assert view["stops"][2]["label"] == "專三"


def test_this_year_puzzle_has_six_pieces_and_blanks(app):
    with app.test_request_context():
        user = student()
        db.session.add(LearningCourseRecord(student_id=user.id, school_year=3, course_name="系統分析",
                                            normalized_course_name="系統分析", score=80))
        db.session.add(Portfolio(student_id=user.id, title="資訊週", category="service", school_year=3))
        db.session.commit()
        view = journey_home(user)
    pieces = view["pieces"]
    assert len(pieces) == 6
    assert [p["key"] for p in pieces if p["filled"]] == ["grades", "service"]
    assert view["blanks"] == 4
    assert all(p["href"] for p in pieces if not p["filled"])


def test_past_year_counts(app):
    with app.test_request_context():
        user = student()
        db.session.add(Portfolio(student_id=user.id, title="迎新", category="activity", school_year=1))
        db.session.commit()
        view = journey_home(user)
    assert view["stops"][0]["count"] == 1


def test_return_scene_only_after_long_absence(app):
    now = datetime.now(timezone.utc)
    with app.test_request_context():
        user = student()
        assert journey_home(user, now=now)["away_days"] is None  # 沒有登入紀錄
        earlier = AuditLog(user_id=user.id, action="student.login", created_at=now - timedelta(days=10))
        db.session.add(earlier)
        db.session.add(AuditLog(user_id=user.id, action="student.login", created_at=now))
        db.session.commit()
        assert journey_home(user, now=now)["away_days"] is None  # 10 天前才來過
        earlier.created_at = now - timedelta(days=327)
        db.session.commit()
        view = journey_home(user, now=now)
    assert view["away_days"] == 327 >= RETURN_DAYS


def test_login_is_recorded_and_home_renders(app):
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})
    with app.app_context():
        assert AuditLog.query.filter_by(action="student.login").count() == 1

    page = client.get("/student/dashboard").get_data(as_text=True)
    assert page.count("data-stop=") == 5
    assert 'aria-current="step"' in page
    assert page.count("data-piece=") == 6
    assert "你在這裡" in page
    assert "data-return" not in page


def test_return_scene_shows_once_per_login(app):
    client = app.test_client()
    with app.app_context():
        user = student()
        db.session.add(AuditLog(user_id=user.id, action="student.login",
                                created_at=datetime.now(timezone.utc) - timedelta(days=200)))
        db.session.commit()
    client.post("/login", data={"username": "stu", "password": "pw"})

    assert "data-return" in client.get("/student/dashboard").get_data(as_text=True)
    assert "data-return" not in client.get("/student/dashboard").get_data(as_text=True)


def test_home_has_walker_and_four_places(app):
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})
    page = client.get("/student/dashboard").get_data(as_text=True)

    assert "data-walker" in page
    assert page.count("data-place=") == 4
    for href in ("/student/learning-profile", "/student/portfolio", "/student/targets"):
        assert f'href="{href}"' in page


def test_blank_pieces_are_draggable(app):
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})
    page = client.get("/student/dashboard").get_data(as_text=True)

    assert page.count("data-drag-piece") == 6  # 專三沒有資料：六塊都是空白，各有一片可以拖
    assert page.count("data-slot") == 6
    assert "data-board" in page
