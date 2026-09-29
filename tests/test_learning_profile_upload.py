import io

from app import create_app
from app.extensions import db
from app.models import DocumentExtraction, SourceDocument, User


def learning_profile_app(tmp_path):
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "UPLOAD_FOLDER": str(tmp_path),
        "DOCUMENT_ANALYSIS_PROVIDER": "fake",
    })
    with app.app_context():
        db.create_all()
        student = User(username="student_demo", display_name="測試學生甲", role="student")
        student.set_password("pw")
        db.session.add(student)
        db.session.commit()
    return app


def login(client):
    client.post("/login", data={"username": "student_demo", "password": "pw"})


def test_student_upload_creates_private_source_document_and_extraction(tmp_path):
    app = learning_profile_app(tmp_path)
    client = app.test_client()
    login(client)

    response = client.post(
        "/student/learning-profile/documents",
        data={
            "document_type": "transcript",
            "file": (io.BytesIO(b"demo transcript"), "transcript.pdf"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    with app.app_context():
        document = SourceDocument.query.one()
        extraction = DocumentExtraction.query.one()
        assert document.owner.username == "student_demo"
        assert document.document_type == "transcript"
        assert document.status == "extracted"
        assert document.file_path != "transcript.pdf"
        assert extraction.source_document_id == document.id
        assert extraction.provider == "fake"
        assert extraction.status == "extracted"
        assert extraction.result_json["document_type"] == "transcript"


def test_learning_profile_rejects_unapproved_document_type(tmp_path):
    app = learning_profile_app(tmp_path)
    client = app.test_client()
    login(client)

    response = client.post(
        "/student/learning-profile/documents",
        data={
            "document_type": "identity_card",
            "file": (io.BytesIO(b"private"), "card.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    with app.app_context():
        assert SourceDocument.query.count() == 0
