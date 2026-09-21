from app import create_app
from app.extensions import db
from app.models import User


def ui_app():
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        student = User(username="ui-student", display_name="UI Student", role="student")
        student.set_password("test-password")
        db.session.add(student)
        db.session.commit()
    return app


def test_public_home_uses_the_shared_design_system_and_motion_shell():
    client = ui_app().test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b'data-page="public-home"' in response.data
    assert b"/static/css/design-system.css" in response.data
    assert b"/static/js/motion.js" in response.data
    assert b'data-motion="hero-cards"' in response.data


def test_student_dashboard_exposes_a_personal_journey_layout():
    client = ui_app().test_client()
    login_response = client.post(
        "/login",
        data={"username": "ui-student", "password": "test-password"},
    )

    assert login_response.status_code == 302
    response = client.get("/student/dashboard")

    assert response.status_code == 200
    assert b'data-page="student-dashboard"' in response.data
    assert b'data-journey-path' in response.data
    assert b'data-motion="reveal"' in response.data


def test_student_portfolio_page_stays_in_the_shared_student_experience():
    client = ui_app().test_client()
    client.post(
        "/login",
        data={"username": "ui-student", "password": "test-password"},
    )

    response = client.get("/student/portfolio")

    assert response.status_code == 200
    assert b'data-page="student-portfolio"' in response.data
    assert b"/static/css/design-system.css" in response.data
