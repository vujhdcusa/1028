"""Evidence-backed field parsing for the Taiwanese technician certificate."""

from datetime import date
from copy import deepcopy
from functools import lru_cache
import re

from opencc import OpenCC


# Ratios describe broad printed areas, not values to insert into a field.
TECHNICIAN_REGIONS = {
    "title": (.18, .03, .70, .23),
    "certificate_number": (.18, .44, .53, .58),
    "occupation": (.18, .56, .55, .73),
    "level": (.70, .70, .90, .84),
    "effective_date": (.18, .78, .53, .92),
    "issue_date": (.63, .78, .96, .92),
    "issuer": (.79, .93, .98, 1.00),
}

# The grade moves vertically between commonly seen card scans. Each crop is
# narrow enough for Tesseract's character mode to separate the two glyphs.
LEVEL_FALLBACK_REGIONS = (
    (.751, .731, .846, .820),
    (.750, .700, .860, .790),
    (.670, .649, .780, .740),
)
NUMBER_FALLBACK_REGIONS = (
    (.190, .500, .460, .610),
    (.190, .480, .480, .590),
)
USER_CONFIRMED_ISSUER_READINGS = {"勞助部發": "勞動部"}


@lru_cache(maxsize=1)
def _traditional_converter():
    return OpenCC("s2twp")


def traditional_text(text):
    """Convert OCR output for presentation while preserving stored raw text."""
    return _traditional_converter().convert(text) if isinstance(text, str) else text


def _number_value(text):
    match = re.search(r"\b\d{2,4}\s*[-－]\s*\d{5,10}\b", text)
    return (re.sub(r"\s+|－", lambda m: "-" if m.group() == "－" else "",
                   match.group()) if match else None)


def _issuer_value(text):
    return "勞動部" if "勞動部" in traditional_text(text or "") else None


def _issuer_candidate(text):
    """Keep the OCR reading visible while converting it to Traditional Chinese."""
    candidate = re.sub(r"\s+", "", traditional_text(text or ""))
    return USER_CONFIRMED_ISSUER_READINGS.get(candidate, candidate) or None


def _issuer_has_manual_correction(text):
    candidate = re.sub(r"\s+", "", traditional_text(text or ""))
    return candidate in USER_CONFIRMED_ISSUER_READINGS


def _occupation_candidate(text):
    candidate = re.sub(r"\s+", "", traditional_text(text or ""))
    candidate = re.sub(r"稱$", "", candidate)
    return candidate or None


def recognize_number_fallback(image):
    """Retry complete number OCR from focused crops, never fill a missing prefix."""
    from app.services.ocr_engines import recognize_tesseract_number

    candidates = []
    for left_ratio, top_ratio, right_ratio, bottom_ratio in NUMBER_FALLBACK_REGIONS:
        left = round(left_ratio * image.width)
        top = round(top_ratio * image.height)
        right = round(right_ratio * image.width)
        bottom = round(bottom_ratio * image.height)
        if right <= left or bottom <= top:
            continue
        try:
            words = recognize_tesseract_number(image.crop((left, top, right, bottom)).convert("RGB"))
        except RuntimeError:
            return []
        matching = [word for word in words if _number_value(str(word.get("text") or ""))]
        if not matching:
            continue
        mapped = [{**word, "bbox": [word["bbox"][0] + left, word["bbox"][1] + top,
                                   word["bbox"][2] + left, word["bbox"][3] + top]}
                  for word in matching]
        confidences = [word.get("confidence") for word in matching
                       if isinstance(word.get("confidence"), (int, float))]
        candidates.append((min(confidences) if confidences else -1, mapped))
    return max(candidates, key=lambda item: item[0])[1] if candidates else []


def _level_value(text):
    match = re.search(r"[甲乙丙丁]\s*[級级]", text)
    return re.sub(r"\s+", "", match.group()).replace("级", "級") if match else None


def recognize_level_fallback(image, engine):
    """Use focused Tesseract OCR when either primary engine misses the grade."""
    from app.services.ocr_engines import recognize_tesseract_level

    candidates = []
    for left_ratio, top_ratio, right_ratio, bottom_ratio in LEVEL_FALLBACK_REGIONS:
        left = round(left_ratio * image.width)
        top = round(top_ratio * image.height)
        right = round(right_ratio * image.width)
        bottom = round(bottom_ratio * image.height)
        if right <= left or bottom <= top:
            continue
        try:
            words = recognize_tesseract_level(image.crop((left, top, right, bottom)).convert("RGB"))
        except RuntimeError:
            return []
        words = [word for word in words
                 if re.search(r"[甲乙丙丁級级]", str(word.get("text") or ""))]
        if not _level_value(" ".join(str(word.get("text") or "") for word in words)):
            continue
        mapped = [{**word, "bbox": [word["bbox"][0] + left, word["bbox"][1] + top,
                                   word["bbox"][2] + left, word["bbox"][3] + top]}
                  for word in words]
        confidences = [word.get("confidence") for word in words
                       if isinstance(word.get("confidence"), (int, float))]
        candidates.append((min(confidences) if confidences else -1, mapped))
    return max(candidates, key=lambda item: item[0])[1] if candidates else []

def recognize_credential_region(image, box, engine):
    """Read a raw card region and map OCR boxes back to the source image."""
    from app.services.ocr_engines import recognize

    left, top, right, bottom = [round(value) for value in box]
    left, top = max(0, left), max(0, top)
    right, bottom = min(image.width, right), min(image.height, bottom)
    if right <= left or bottom <= top:
        return []
    crop = image.crop((left, top, right, bottom)).convert("RGB")
    raw_words = recognize(crop, engine)
    raw_confidences = [word.get("confidence") for word in raw_words
                       if isinstance(word.get("confidence"), (int, float))]
    from app.services.ocr_engines import LINE_LEVEL_ENGINES
    is_paddle = engine in LINE_LEVEL_ENGINES
    # Paddle's large detector/recognizer already sees the complete field crop.
    # Re-running every low-confidence crop at 2x multiplies CPU and memory use
    # on textured or reflective cards. Retry only empty Paddle results; retain
    # the low score so the review UI can ask for human verification.
    needs_zoom = not raw_words or (not is_paddle and
                                   (not raw_confidences or min(raw_confidences) < .85))
    zoom_words = []
    if needs_zoom:
        zoom_words = recognize(crop.resize((crop.width * 2, crop.height * 2)), engine)
    raw_length = sum(char.isalnum() for word in raw_words for char in word["text"])
    zoom_length = sum(char.isalnum() for word in zoom_words for char in word["text"])
    zoom_confidences = [word.get("confidence") for word in zoom_words
                        if isinstance(word.get("confidence"), (int, float))]
    use_zoom = bool(zoom_words) and (not raw_words or (
        zoom_length >= raw_length and zoom_confidences and
        min(zoom_confidences) > (min(raw_confidences) if raw_confidences else 0) + .1
    ))
    selected = zoom_words if use_zoom else raw_words
    scale = 2 if use_zoom else 1
    return [{**word, "bbox": [word["bbox"][0] / scale + left, word["bbox"][1] / scale + top,
                               word["bbox"][2] / scale + left, word["bbox"][3] / scale + top]}
            for word in selected]


def _field(words, page, value, *, invalid=False):
    text = " ".join(str(item.get("text") or "").strip() for item in words).strip()
    boxes = [item["bbox"] for item in words if item.get("bbox") and len(item["bbox"]) == 4]
    bbox = ([min(box[0] for box in boxes), min(box[1] for box in boxes),
             max(box[2] for box in boxes), max(box[3] for box in boxes)] if boxes else None)
    confidences = [item["confidence"] for item in words
                   if isinstance(item.get("confidence"), (int, float)) and item["confidence"] >= 0]
    confidence = min(confidences) if confidences else None
    if invalid:
        reason = "日期不完整或無效，請對照原圖"
    elif value is None:
        reason = "未辨識到欄位值，請對照原圖"
    elif confidence is None:
        reason = "OCR 信心未知，請核對"
    elif confidence < .85:
        reason = "OCR 信心偏低，請核對"
    else:
        reason = None
    return {"value": value, "raw_text": text, "bbox": bbox, "confidence": confidence,
            "page": page, "reason": reason}


def _roc_date(text):
    match = re.search(r"民國\s*(\d{2,3})\s*年?\s*(\d{1,2})\s*月?\s*(\d{1,2})(?!\s*\d)\s*日?", text)
    if not match:
        return None
    try:
        return date(int(match[1]) + 1911, int(match[2]), int(match[3])).isoformat()
    except ValueError:
        return None


def analyze_technician_regions(regions, *, page):
    """Require a title or three independent field signals for a tentative match."""
    title = "".join(str(item.get("text") or "") for item in regions.get("title", []))
    title_found = bool(re.search(r"技術\s*士\s*證", title))

    def text_for(key):
        return " ".join(str(item.get("text") or "") for item in regions.get(key, []))

    occupation_text = re.sub(r"職\s*類\s*[（(]?\s*項?\s*[）)]?|名\s*稱", " ", text_for("occupation"))
    occupation_text = re.sub(r"稱\s*$", "", occupation_text)
    occupation_text = re.sub(r"稱\s*$", "", occupation_text)
    occupation_text = re.sub(r"\s+", "", occupation_text)
    occupation_match = re.search(
        r"[\u4e00-\u9fff]{2,16}(?:[-－—–][\u4e00-\u9fff]{1,16})*",
        occupation_text)
    occupation_value = (occupation_match.group().translate(
        str.maketrans({"-": "－", "—": "－", "–": "－"}))
        if occupation_match else None)
    level_value = _level_value(text_for("level"))
    values = {
        "occupation": occupation_value,
        "level": level_value,
        "certificate_number": _number_value(text_for("certificate_number")),
        "effective_date": _roc_date(text_for("effective_date")),
        "issue_date": _roc_date(text_for("issue_date")),
        "issuer": _issuer_candidate(text_for("issuer")),
    }
    if not title_found and not (values["occupation"] and values["certificate_number"]
                                and (values["issue_date"] or values["effective_date"])):
        return None
    fields = {}
    for key, value in values.items():
        raw = text_for(key)
        fields[key] = _field(regions.get(key, []), page, value,
                             invalid=(key in {"issue_date", "effective_date"} and bool(raw) and value is None))
        if value is None and raw and key == "certificate_number":
            fields[key]["reason"] = "總編號不完整；信心分數僅對已讀片段，請對照原圖"
        if key == "issuer" and value and value != "勞動部":
            fields[key]["reason"] = "OCR 辨識文字疑似有誤，請核對發證單位後再儲存"
        elif key == "issuer" and value and _issuer_has_manual_correction(raw):
            fields[key]["reason"] = "已依人工核對修正為「勞動部」，請確認後再儲存"
    title_evidence = _field(regions.get("title", []), page, title if title_found else None)
    if not title_found:
        classification_reason = "證照標題未辨識；依職類、總編號與日期僅列為疑似"
    elif title_evidence["reason"]:
        classification_reason = "證照標題 OCR 信心不足，請核對原圖"
    else:
        classification_reason = None
    certain_title = title_found and classification_reason is None
    return {
        "source_page": page,
        "document_kind": ("taiwan_technician_certificate" if certain_title
                          else "possible_taiwan_technician_certificate"),
        "document_label": ("中華民國技術士證" if certain_title
                           else "疑似中華民國技術士證（標題需核對）"),
        "classification_reason": classification_reason,
        "title_evidence": title_evidence,
        "fields": fields,
        "needs_review": bool(classification_reason) or any(field["reason"] for field in fields.values()),
        "steps": ["辨識證照標題", "依版面分區重讀欄位", "解析欄位並標示待確認原因"],
    }


def prepare_credential_review_result(result, *, preserve_confirmed_credentials=False):
    """Show OCR issuer text in Traditional Chinese and flag uncertain readings."""
    review = deepcopy(result)
    analyses = review.get("credential_analyses") or (
        [review["credential_analysis"]] if review.get("credential_analysis") else [])
    for analysis in analyses:
        fields = analysis.get("fields") or {}
        occupation = fields.get("occupation")
        if occupation:
            occupation["value"] = _occupation_candidate(
                occupation.get("value") or occupation.get("raw_text"))
        issuer = fields.get("issuer")
        if issuer:
            candidate = _issuer_candidate(issuer.get("raw_text") or issuer.get("value"))
            issuer["value"] = candidate
            if candidate and candidate != "勞動部":
                issuer["reason"] = "OCR 辨識文字疑似有誤，請核對發證單位後再儲存"
            elif candidate and _issuer_has_manual_correction(issuer.get("raw_text") or issuer.get("value")):
                issuer["reason"] = "已依人工核對修正為「勞動部」，請確認後再儲存"
        number = fields.get("certificate_number")
        if number and number.get("value") is None and number.get("raw_text"):
            number["reason"] = "總編號不完整；信心分數僅對已讀片段，請對照原圖"
        level = fields.get("level")
        if level and level.get("value"):
            level["value"] = traditional_text(level["value"])
    for credential in review.get("credentials") or []:
        analysis = next((item for item in analyses
                         if item.get("source_page") == credential.get("source_page")), None)
        if analysis is None and len(analyses) == 1:
            analysis = analyses[0]
        if analysis:
            occupation = (analysis.get("fields") or {}).get("occupation")
            if occupation and occupation.get("value") and not preserve_confirmed_credentials:
                credential["credential_name"] = occupation["value"]
            issuer = (analysis.get("fields") or {}).get("issuer")
            if issuer and not preserve_confirmed_credentials:
                credential["issuing_organization"] = issuer.get("value")
        for key in ("credential_name", "level", "issuing_organization"):
            if credential.get(key):
                credential[key] = traditional_text(credential[key])
    return review
