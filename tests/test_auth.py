from app import create_app
from app.extensions import db
from app.models import User


def auth_app():
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        for username, role, display_name in (
            ("student001", "student", "測試學生"),
            ("teacher001", "teacher", "測試教師"),
            ("admin", "admin", "測試管理員"),
        ):
            user = User(username=username, role=role, display_name=display_name)
            user.set_password("test-password")
            db.session.add(user)
        db.session.commit()
    return app


def test_login_redirects_student_to_student_dashboard():
    client = auth_app().test_client()

    response = client.post(
        "/login",
        data={"username": "student001", "password": "test-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/student/dashboard")


def test_login_rejects_wrong_password_without_creating_session():
    client = auth_app().test_client()

    response = client.post(
        "/login",
        data={"username": "student001", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "帳號或密碼錯誤".encode("utf-8") in response.data


def test_student_cannot_open_admin_dashboard():
    client = auth_app().test_client()
    client.post(
        "/login",
        data={"username": "student001", "password": "test-password"},
    )

    response = client.get("/admin/dashboard")

    assert response.status_code == 403


def test_logout_clears_session():
    client = auth_app().test_client()
    client.post(
        "/login",
        data={"username": "student001", "password": "test-password"},
    )

    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert client.get("/student/dashboard").status_code == 401
