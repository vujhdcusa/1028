"""Document-analysis boundary for the P0 learning-profile workflow.

The default provider is deterministic and returns an empty review payload.  It
keeps upload, confirmation, and output workflows testable without sending a
student's document to an external service.  A production Gemini provider is
enabled only after its credentials and data-sharing approval are configured.
"""


ALLOWED_DOCUMENT_TYPES = {"transcript", "credential"}


def analyze_document(document_type, file_path, provider_name="fake"):
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError("unsupported document type")
    if provider_name == "demo":
        warning = "本機模擬 OCR：這些是假辨識資料，請先修正欄位；不會連接外部服務。"
        if document_type == "transcript":
            return {
                "document_type": document_type,
                "courses": [{"school_year": 3, "semester": "上", "course_name": "模擬辨識課程",
                             "credits": 3, "score": 88}],
                "credentials": None,
                "warnings": [warning],
                "source_file_available": bool(file_path),
                "simulation": True,
            }
        return {
            "document_type": document_type,
            "courses": None,
            "credentials": [{"credential_name": "模擬辨識證照", "level": "丙級",
                             "issuing_organization": "模擬發證單位", "issue_date": ""}],
            "warnings": [warning],
            "source_file_available": bool(file_path),
            "simulation": True,
        }
    if provider_name != "fake":
        raise RuntimeError("目前尚未設定可用的文件分析服務")

    return {
        "document_type": document_type,
        "courses": [] if document_type == "transcript" else None,
        "credentials": [] if document_type == "credential" else None,
        "warnings": ["此為待學生確認的擷取草稿；未填資料不會由系統推測。"],
        "source_file_available": bool(file_path),
    }
