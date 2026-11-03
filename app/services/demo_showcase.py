"""專題展示帳號的合成資料工具。

展示資料刻意保留一份「已擷取、尚未確認」的 OCR 成績單。這能讓老師演示：
學生可先修正 OCR，且未確認內容不會進到準備度或 Agent 的個人分析。
"""

from base64 import b64decode
from hashlib import sha256

from app.extensions import db
from app.models import DocumentExtraction, SourceDocument
from app.services import storage_service


# 1×1 的有效 PNG；只作展示用來源檔，沒有任何真實學生資料。
_DEMO_TRANSCRIPT_PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/"
    "FDrYVQAAAABJRU5ErkJggg=="
)


def seed_pending_ocr_review(student):
    """新增一份可在 OCR 核對畫面操作的合成草稿，回傳來源文件。

    呼叫端要在自己的資料庫交易中 commit。這份草稿不建立
    ``LearningCourseRecord``，因此確認前自然不會被任何分析使用。
    """
    filename = "展示用_待核對成績單.png"
    location = storage_service.save(
        _DEMO_TRANSCRIPT_PNG,
        owner_id=student.id,
        folder="demo-showcase",
        filename=filename,
    )
    document = SourceDocument(
        owner_id=student.id,
        document_type="transcript",
        display_name=filename,
        file_path=location,
        sha256=sha256(_DEMO_TRANSCRIPT_PNG).hexdigest(),
        status="extracted",
    )
    db.session.add(document)
    db.session.flush()
    db.session.add(DocumentExtraction(
        source_document_id=document.id,
        provider="demo",
        status="extracted",
        result_json={
            "draft_revision": "demo-showcase-ocr-v1",
            "source": {"engine": "demo"},
            "raw_text": "專五上學期 雲端服務實務 92\n專五上學期 分散式系統 87",
            "warnings": ["這是展示用合成 OCR 草稿；請示範核對或修正後，再按確認儲存。"],
            "processing_steps": [
                {"step": "uploaded", "message": "展示來源檔已建立"},
                {"step": "extracted", "message": "已產生可核對的合成 OCR 草稿"},
            ],
            "courses": [
                {
                    "grade_level": "五年級",
                    "semester": "第一學期",
                    "course_name": "雲端服務實務",
                    "credits": 3,
                    "score": 92,
                    "field_confidence": {"course_name": 0.98, "credits": 0.98, "score": 0.98},
                },
                {
                    "grade_level": "五年級",
                    "semester": "第一學期",
                    "course_name": "分散式系統",
                    "credits": 3,
                    "score": 87,
                    "field_confidence": {"course_name": 0.94, "credits": 0.92, "score": 0.72},
                },
            ],
            "credentials": [],
        },
    ))
    return document
