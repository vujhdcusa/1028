from app import create_app
from app.extensions import db
from app.models import DocumentExtraction, SourceDocument, User
from app.services.demo_showcase import seed_pending_ocr_review
from app.services.journey_service import build_journey


def test_showcase_ocr_draft_is_previewable_but_not_part_of_journey(tmp_path):
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "UPLOAD_FOLDER": str(tmp_path),
    })
    with app.app_context():
        db.create_all()
        student = User(username="showcase", display_name="展示學生", role="student")
        student.set_password("pw")
        db.session.add(student)
        db.session.flush()

        document = seed_pending_ocr_review(student)
        db.session.commit()

        assert document.status == "extracted"
        assert document.display_name.endswith(".png")
        assert SourceDocument.query.count() == 1
        assert DocumentExtraction.query.one().status == "extracted"
        assert len(DocumentExtraction.query.one().result_json["courses"]) == 2
        # OCR 草稿尚未被學生確認，所以不能算入旅程資料或 Agent 準備度資料。
        assert build_journey(student)["totals"]["grades"] == 0
        assert list(tmp_path.joinpath("demo-showcase", str(student.id)).glob("*.png"))
