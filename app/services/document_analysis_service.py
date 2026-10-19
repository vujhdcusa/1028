"""Document-analysis boundary for the P0 learning-profile workflow.

The default provider is deterministic and returns an empty review payload.  It
keeps upload, confirmation, and output workflows testable without sending a
student's document to an external service.  A production Gemini provider is
enabled only after its credentials and data-sharing approval are configured.
"""


import re
from pathlib import Path


ALLOWED_DOCUMENT_TYPES = {"transcript", "credential"}
CANDIDATE_WARNING = "此為 OCR 候選欄位；必須由學生逐項確認後才會成為正式資料。"
DEFAULT_OCR_MODEL_DIR = Path(__file__).resolve().parents[2] / "instance" / "ocr-models"
OCR_MODEL_FILES = {
    "Det": "ch_PP-OCRv5_det_mobile.onnx",
    "Rec": "ch_PP-OCRv5_rec_mobile.onnx",  # 簡體、繁體、英文、日文共用一個模型
    "Cls": "ch_ppocr_mobile_v2.0_cls_mobile.onnx",
}
FIELD_LABELS = ("課程", "學分", "分數", "證照名稱", "等級", "發證單位", "日期")


class RapidOcrEngine:
    """離線 OCR（RapidOCR PP-OCRv5，在本機執行，圖片不離開伺服器）。

    只讀本機模型檔，不會自動下載；模型由 scripts/download_ocr_models.py 預先下載並核對雜湊。
    """

    def __init__(self, model_dir=None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_OCR_MODEL_DIR
        self._ocr = None

    def _load(self):
        paths = {stage: self.model_dir / name for stage, name in OCR_MODEL_FILES.items()}
        missing = [path.name for path in paths.values() if not path.exists()]
        if missing:
            raise RuntimeError(
                f"離線 OCR 模型檔不存在（{', '.join(missing)}）；請先執行 scripts/download_ocr_models.py"
            )
        from rapidocr import OCRVersion, RapidOCR

        params = {"Global.log_level": "error",
                  "Det.ocr_version": OCRVersion.PPOCRV5, "Rec.ocr_version": OCRVersion.PPOCRV5}
        params.update({f"{stage}.model_path": str(path) for stage, path in paths.items()})
        return RapidOCR(params=params)

    def recognize_text(self, image_path):
        if self._ocr is None:
            self._ocr = self._load()
        output = self._ocr(str(image_path))
        if output.boxes is None or not output.txts:
            return ""
        result = zip(output.boxes.tolist(), output.txts)
        # 同一行的文字框 y 座標相近：先依 y 中心分行，再依 x 由左到右排序
        boxes = sorted(result, key=lambda item: (sum(p[1] for p in item[0]) / 4))
        lines, current, current_y, current_h = [], [], None, None
        for box, text in boxes:
            ys = [p[1] for p in box]
            xs = [p[0] for p in box]
            center_y, height = (min(ys) + max(ys)) / 2, max(ys) - min(ys)
            if current_y is not None and abs(center_y - current_y) > current_h / 2:
                lines.append(current)
                current = []
            current.append((min(xs), text))
            current_y, current_h = center_y, height
        if current:
            lines.append(current)
        return "\n".join("  ".join(text for _x, text in sorted(line)) for line in lines)


class NotConfiguredOcrEngine:
    """尚未選定離線 OCR 套件（RapidOCR 待使用者確認）前的預設值：一律失敗，不猜測。"""

    def recognize_text(self, image_path):
        raise RuntimeError("目前尚未設定離線 OCR 引擎")


def _field(line, label):
    # 值到空白或下一個欄位標籤為止（OCR 常把「學分：3  分數：88」黏成「學分：3分數：88」）
    next_label = "|".join(f"{other}[:：]" for other in FIELD_LABELS if other != label)
    match = re.search(rf"{label}[:：]\s*(.+?)(?=\s|{next_label}|$)", line)
    return match.group(1) if match else ""


def parse_candidates(text, document_type):
    """把 OCR 文字轉成候選欄位；查不到的欄位留空，不推測。"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if document_type == "transcript":
        courses = [
            {
                "school_year": None,
                "semester": None,
                "course_name": _field(line, "課程"),
                "credits": _field(line, "學分"),
                "score": _field(line, "分數"),
            }
            for line in lines if _field(line, "課程")
        ]
        return {"document_type": document_type, "courses": courses, "credentials": None}

    credentials = [
        {
            "credential_name": _field(line, "證照名稱"),
            "level": _field(line, "等級"),
            "issuing_organization": _field(line, "發證單位"),
            "issue_date": _field(line, "日期"),
        }
        for line in lines if _field(line, "證照名稱")
    ]
    return {"document_type": document_type, "courses": None, "credentials": credentials}


def analyze_document(document_type, file_path, provider_name="fake", ocr_engine=None):
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError("unsupported document type")
    if provider_name == "offline_ocr":
        engine = ocr_engine or NotConfiguredOcrEngine()
        text = engine.recognize_text(file_path)
        result = parse_candidates(text, document_type)
        result["warnings"] = [CANDIDATE_WARNING]
        result["source_file_available"] = bool(file_path)
        result["simulation"] = False
        return result
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
