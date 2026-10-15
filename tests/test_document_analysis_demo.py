import io
import json
import html
import re

from app import create_app
from app.extensions import db
from app.models import DocumentExtraction, LearningCourseRecord, SourceDocument, User
from app.services.document_analysis_service import analyze_document


def test_demo_provider_returns_explicitly_labelled_synthetic_ocr_rows(tmp_path):
    result = analyze_document("transcript", tmp_path / "synthetic.pdf", "demo")

    assert result["simulation"] is True
    assert result["courses"] == [{
        "school_year": 3,
        "semester": "上",
        "course_name": "模擬辨識課程",
        "credits": 3,
        "score": 88,
    }]
    assert any("模擬" in warning for warning in result["warnings"])


def test_student_can_correct_demo_ocr_before_confirming(tmp_path):
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "UPLOAD_FOLDER": str(tmp_path),
        "DOCUMENT_ANALYSIS_PROVIDER": "demo",
    })
    with app.app_context():
        db.create_all()
        student = User(username="student_demo", display_name="合成學生", role="student")
        student.set_password("pw")
        db.session.add(student)
        db.session.commit()
    client = app.test_client()
    client.post("/login", data={"username": "student_demo", "password": "pw"})
    response = client.post("/student/learning-profile/documents", data={
        "document_type": "transcript",
        "file": (io.BytesIO(b"synthetic-only"), "synthetic.pdf"),
    }, content_type="multipart/form-data")
    assert response.status_code == 302
    with app.app_context():
        source = SourceDocument.query.one()
        source_id = source.id
    review_page = client.get(f"/student/learning-profile/documents/{source_id}/review").get_data(as_text=True)

    assert "本機模擬 OCR" in review_page
    initial_attribute = re.search(r"data-initial=(['\"])(.*?)\1", review_page)
    assert initial_attribute is not None
    assert json.loads(html.unescape(initial_attribute.group(2)))[0]["course_name"] == "模擬辨識課程"
    response = client.post(f"/student/learning-profile/documents/{source_id}/review/confirm", data={
        "courses_json": json.dumps([{
            "school_year": "3", "semester": "上", "course_name": "修正後課程", "credits": "3", "score": "93",
        }]),
        "credentials_json": "[]",
    })

    assert response.status_code == 302
    with app.app_context():
        course = LearningCourseRecord.query.one()
        extraction = DocumentExtraction.query.one()
        assert (course.course_name, course.score, course.confirmation_status) == ("修正後課程", 93, "confirmed")
        assert extraction.result_json["simulation"] is True
        assert extraction.confirmed_by.username == "student_demo"
