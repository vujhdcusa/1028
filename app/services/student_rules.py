"""學生端的使用限制：年級（看得到但不能用）與目標校系上限。規格第 10.4、10.5 節。

- 沒有入學學年度就不知道年級：擋下並請學生先補，不猜年級。
- 不能填寫比目前年級更高的成績或經歷。
- 送審與送審相關的 AI（自傳）要到 MIN_REVIEW_GRADE 年級才能用；更低年級只能看。
- 目標校系同時最多 TARGET_LIMIT 所，只算最新學年度的校系；舊學年度的另外列出，可以刪除。
"""

from datetime import date

from flask import current_app

from app.models import StudentTarget
from app.services.admission_service import published_programs
from app.services.journey_service import GRADE_LABELS, academic_year_of, current_grade, grade_for

MISSING_ADMISSION_YEAR = "系統還不知道你的入學學年度，沒辦法判斷你現在幾年級。請先補上入學學年度。"


def admission_year_of(student):
    profile = student.student_profile
    return profile.admission_year if profile else None


def grade_of(student, today=None):
    return current_grade(admission_year_of(student), today)


def grade_block_reason(student, today=None):
    """沒有入學學年度時回傳提示文字；可以判斷年級時回傳 None。"""
    return MISSING_ADMISSION_YEAR if grade_of(student, today) is None else None


def review_block_reason(student, today=None):
    """送審、產生自傳前的檢查。回傳提示文字，或 None（可以使用）。"""
    reason = grade_block_reason(student, today)
    if reason:
        return reason
    minimum = current_app.config.get("MIN_REVIEW_GRADE", 2)
    grade = grade_of(student, today)
    if grade < minimum:
        return (f"你現在是{GRADE_LABELS[grade]}，可以先看目標校系的要求和還缺什麼；"
                f"送導師確認和用 AI 寫自傳，要到{GRADE_LABELS[minimum]}才能使用。")
    return None


def check_record_year(student, school_year, today=None):
    """填成績、經歷時，年級不能比現在高。年級可以是 1～5 或民國學年度；有問題時丟 ValueError。"""
    reason = grade_block_reason(student, today)
    if reason:
        raise ValueError(reason)
    if school_year is None:
        return
    grade = grade_for(school_year, admission_year_of(student))
    now = grade_of(student, today)
    if grade is not None and grade > now:
        raise ValueError(f"你現在是{GRADE_LABELS[now]}，還不能填{GRADE_LABELS[grade]}的資料。"
                         "高年級的內容可以先看，等升上去再填。")
    if grade is None and school_year > 5 and school_year > academic_year_of(today or date.today()):
        raise ValueError(f"{school_year} 學年度還沒到，請確認學年度。")


def target_slots(student):
    """目前占名額的目標（最新學年度）與舊學年度的目標。"""
    newest = {program.id for program in published_programs()}
    targets = StudentTarget.query.filter_by(student_id=student.id).order_by(StudentTarget.selected_at).all()
    current = [t for t in targets if t.rule_version_id in newest]
    return {
        "limit": current_app.config.get("TARGET_LIMIT", 5),
        "used": len(current),
        "current": current,
        "old": [t for t in targets if t.rule_version_id not in newest],
    }
