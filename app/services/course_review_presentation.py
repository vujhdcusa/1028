"""Display grouping for editable transcript drafts; never rewrite source rows."""

from functools import lru_cache
import re

from opencc import OpenCC


_TRADITIONAL_CONVERTER = OpenCC("s2twp")

GRADE_NAMES = ("一年級", "二年級", "三年級", "四年級", "五年級")
CHINESE_NUMERALS = "一二三四五"


def _grade_key(value):
    raw = str(value or "").strip()
    for number, numeral in enumerate(CHINESE_NUMERALS, 1):
        if raw in (str(number), f"{number}年級", f"{numeral}年級"):
            return str(number)
    return "unknown"


def _semester_label(value):
    raw = str(value or "").strip()
    if raw in ("1", "一", "第一學期", "上學期"):
        return "第一學期"
    if raw in ("2", "二", "第二學期", "下學期"):
        return "第二學期"
    return raw or "學期待確認"


@lru_cache(maxsize=1024)
def traditionalize_course_name(value):
    """Convert only the editable course-name candidate to Taiwanese Traditional Chinese."""
    if not isinstance(value, str):
        return value
    return _TRADITIONAL_CONVERTER.convert(value)


_MAKEUP_MARKER = re.compile(r"^\s*(?:\[|【)?\s*(暑|寒)\s*(?:\]|】)?\s*")


def split_makeup_marker(value):
    """Return (course text without a leading [暑]/[寒] marker, season)."""
    raw = str(value or "")
    # Some OCR layouts prefix a required/elective mark before the season marker.
    raw = re.sub(r"^\s*(?:[必選密]\s*[|｜]\s*)", "", raw)
    match = _MAKEUP_MARKER.match(raw)
    if not match:
        return raw.strip(), None
    season = "summer" if match.group(1) == "暑" else "winter"
    return raw[match.end():].strip(), season


def prepare_course_review_rows(courses):
    """Build editable Traditional-Chinese values without mutating stored evidence."""
    prepared = []
    for course in courses:
        row = dict(course)
        missing_value = any(
            row.get(field) is None
            or not str(row.get(field)).strip()
            or "待確認" in str(row.get(field))
            for field in ("course_name", "credits", "score", "semester", "grade_level")
        )
        # Page-wide semester/header inference flags every row in some transcripts.
        # Only content fields with their own low OCR confidence should make a
        # populated course pending; layout warnings remain visible in the row.
        confidence = row.get("field_confidence") or {}
        low_content_confidence = any(
            isinstance(confidence.get(field), (int, float))
            and not isinstance(confidence.get(field), bool)
            and 0 <= confidence[field] < 0.85
            for field in ("course_name", "credits", "score")
        )
        row["needs_review"] = missing_value or low_content_confidence
        raw_cells = row.get("raw_cells") or []
        first_cell = raw_cells[0] if raw_cells else ""
        if isinstance(first_cell, (list, tuple)):
            first_cell = " ".join(str(value) for value in first_cell)
        name_without_marker, name_season = split_makeup_marker(row.get("course_name"))
        _raw_name_without_marker, cell_season = split_makeup_marker(first_cell)
        if row.get("makeup_season") not in ("summer", "winter"):
            row["makeup_season"] = name_season or cell_season
        row["course_name"] = traditionalize_course_name(name_without_marker)
        prepared.append(row)
    return prepared


def build_course_review_groups(courses):
    """Return five grade groups plus unknown, preserving source-list indices."""
    groups = [
        {"key": str(number), "label": label, "passed": [], "failed": [],
         "pending": [], "highest": None}
        for number, label in enumerate(GRADE_NAMES, 1)
    ]
    groups.append({"key": "unknown", "label": "年級待確認", "passed": [],
                   "failed": [], "pending": [], "highest": None})
    by_key = {group["key"]: group for group in groups}
    for index, course in enumerate(courses):
        group = by_key[_grade_key(course.get("grade_level"))]
        entry = {"index": index, "course": course,
                 "semester_label": _semester_label(course.get("semester")),
                 "school_year": course.get("school_year"),
                 "makeup_season": course.get("makeup_season")}
        score = course.get("score")
        if type(score) is not int or not 0 <= score <= 100:
            group["pending"].append(entry)
        elif score < 60:
            group["failed"].append(entry)
        else:
            group["passed"].append(entry)
    for group in groups:
        for kind in ("passed", "failed"):
            group[kind].sort(key=lambda entry: (-entry["course"]["score"], entry["index"]))
        semester_labels = ["第一學期", "第二學期"]
        for entry in sorted(
            group["passed"] + group["failed"] + group["pending"],
            key=lambda item: item["index"],
        ):
            if entry["semester_label"] not in semester_labels:
                semester_labels.append(entry["semester_label"])
        group["semesters"] = [
            {
                "label": label,
                **{
                    kind: [entry for entry in group[kind] if entry["semester_label"] == label]
                    for kind in ("passed", "failed", "pending")
                },
            }
            for label in semester_labels
            if any(entry["semester_label"] == label
                   for kind in ("passed", "failed", "pending") for entry in group[kind])
        ]
        scored = group["passed"] + group["failed"]
        group["top_three"] = sorted(
            scored, key=lambda entry: (-entry["course"]["score"], entry["index"])
        )[:3]
        group["highest"] = min(scored, key=lambda entry: (-entry["course"]["score"], entry["index"])) if scored else None
        group["empty"] = not (group["passed"] or group["failed"] or group["pending"])
    return groups
