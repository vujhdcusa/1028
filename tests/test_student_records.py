import io
import json
from datetime import date

from app import create_app
from app.extensions import db
from app.models import CredentialRecord, Portfolio, SourceDocument, StudentProfile, User


def records_app(tmp_path):
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "UPLOAD_FOLDER": str(tmp_path),
    })
    with app.app_context():
        db.create_all()
        student = User(username="stu", display_name="測試學生", role="student")
        student.set_password("pw")
        db.session.add(student)
        db.session.flush()
        db.session.add(StudentProfile(user_id=student.id, student_no="111534100", admission_year=111))
        db.session.commit()
    return app


def login(client):
    client.post("/login", data={"username": "stu", "password": "pw"})


def test_record_requires_one_of_the_four_experience_categories(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)

    response = client.post("/student/portfolio", data={"title": "隨便", "category": "課程作品"})

    assert response.status_code == 400
    with app.app_context():
        assert Portfolio.query.count() == 0


def test_record_stores_category_year_and_semester(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)

    response = client.post("/student/portfolio", data={
        "title": "資訊週志工", "category": "service", "school_year": "2", "semester": "1",
        "description": "協助活動報到",
    })

    assert response.status_code == 302
    with app.app_context():
        record = Portfolio.query.one()
        assert (record.category, record.school_year, record.semester) == ("service", 2, 1)


def test_record_rejects_year_outside_five_grades_or_academic_years(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)

    response = client.post("/student/portfolio", data={"title": "x", "category": "activity", "school_year": "abc"})

    assert response.status_code == 400


def test_credential_confirmation_keeps_issue_date(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)
    client.post("/student/learning-profile/documents", data={
        "document_type": "credential", "file": (io.BytesIO(b"demo"), "cert.pdf"),
    }, content_type="multipart/form-data")
    with app.app_context():
        document_id = SourceDocument.query.one().id

    response = client.post(f"/student/learning-profile/documents/{document_id}/review/confirm", data={
        "courses_json": "[]",
        "credentials_json": json.dumps([{"credential_name": "網頁設計丙級", "issue_date": "2024-03-02"}]),
    })

    assert response.status_code == 302
    with app.app_context():
        assert CredentialRecord.query.one().issue_date == date(2024, 3, 2)


def test_credential_confirmation_rejects_bad_issue_date(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)
    client.post("/student/learning-profile/documents", data={
        "document_type": "credential", "file": (io.BytesIO(b"demo"), "cert.pdf"),
    }, content_type="multipart/form-data")
    with app.app_context():
        document_id = SourceDocument.query.one().id

    response = client.post(f"/student/learning-profile/documents/{document_id}/review/confirm", data={
        "courses_json": "[]",
        "credentials_json": json.dumps([{"credential_name": "證照", "issue_date": "2024/99/99"}]),
    })

    assert response.status_code == 400


def test_student_home_shows_record_inside_its_year_folder(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)
    client.post("/student/portfolio", data={"title": "班級幹部－學藝股長", "category": "leadership", "school_year": "2"})

    html = client.get("/student/dashboard").get_data(as_text=True)

    folder = html.split('data-year-folder="2"', 1)[1].split("data-year-folder=", 1)[0]
    assert "班級幹部－學藝股長" in folder


def test_review_page_renders_editable_tables_and_real_csrf_token(tmp_path):
    app = records_app(tmp_path)
    client = app.test_client()
    login(client)
    client.post("/student/learning-profile/documents", data={
        "document_type": "transcript", "file": (io.BytesIO(b"demo"), "t.pdf"),
    }, content_type="multipart/form-data")
    with app.app_context():
        document_id = SourceDocument.query.one().id

    html = client.get(f"/student/learning-profile/documents/{document_id}/review").get_data(as_text=True)

    assert "data-record-table" in html
    assert "<function" not in html
