import json

from app import create_app
from app.extensions import db
from app.models import (
    CredentialRecord,
    DocumentExtraction,
    LearningCourseRecord,
    SourceDocument,
    User,
)


def learning_profile_app(tmp_path):
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "UPLOAD_FOLDER": str(tmp_path),
    })
    with app.app_context():
        db.create_all()
        for username in ("student_demo", "other_student"):
            user = User(username=username, display_name=username, role="student")
            user.set_password("pw")
            db.session.add(user)
        db.session.commit()
        owner = User.query.filter_by(username="student_demo").one()
        document = SourceDocument(
            owner_id=owner.id,
            document_type="transcript",
            display_name="transcript.pdf",
            file_path=str(tmp_path / "transcript.pdf"),
            sha256="c" * 64,
            status="extracted",
        )
        db.session.add(document)
        db.session.flush()
        db.session.add(DocumentExtraction(
            source_document_id=document.id,
            provider="fake",
            status="extracted",
            result_json={"courses": []},
        ))
        db.session.commit()
        return app, document.id


def login(client, username="student_demo"):
    client.post("/login", data={"username": username, "password": "pw"})


def test_student_confirmation_persists_courses_and_credentials(tmp_path):
    app, document_id = learning_profile_app(tmp_path)
    client = app.test_client()
    login(client)

    response = client.post(
        f"/student/learning-profile/documents/{document_id}/review/confirm",
        data={
            "courses_json": json.dumps([
                {"course_name": "程式設計", "credits": 3, "score": 92},
                {"course_name": "資訊管理", "credits": 2, "status_mark": "抵"},
            ]),
            "credentials_json": json.dumps([
                {"credential_name": "資訊技術類測試證照", "level": "丙級", "issuing_organization": "測試發證單位"},
            ]),
        },
    )

    assert response.status_code == 302
    with app.app_context():
        courses = LearningCourseRecord.query.order_by(LearningCourseRecord.id).all()
        assert [(course.course_name, course.score, course.status_mark) for course in courses] == [
            ("程式設計", 92, None),
            ("資訊管理", None, "抵"),
        ]
        assert CredentialRecord.query.one().credential_name == "資訊技術類測試證照"
        extraction = DocumentExtraction.query.one()
        assert extraction.status == "confirmed"
        assert extraction.confirmed_by.username == "student_demo"


def test_other_student_cannot_confirm_source_document(tmp_path):
    app, document_id = learning_profile_app(tmp_path)
    client = app.test_client()
    login(client, "other_student")

    response = client.post(
        f"/student/learning-profile/documents/{document_id}/review/confirm",
        data={"courses_json": "[]", "credentials_json": "[]"},
    )

    assert response.status_code == 403
