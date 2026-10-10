"""學生首頁「我的五年路線」要用的資料。規格：docs/02_需求與設計/AI_設計規格_我的五年路線首頁_2026-10-10.md

- stops：專一到專五五個節點；走過的是 past、今年是 now、之後是 future，count 是那一年留下幾筆。
- pieces：今年的六塊拼圖（六類學習資料），沒有資料的是空白，點了去補。
- away_days：上次登入在 RETURN_DAYS 天以前才有值，用來播「好久不見」那一幕。
  登入紀錄存在操作紀錄（action="student.login"），最新一筆就是這次登入。
"""

from datetime import datetime, timezone

from flask import url_for

from app.content.five_year_plan import FIVE_YEAR_PLAN
from app.models import AuditLog
from app.services.journey_service import CATEGORY_KEYS, CATEGORY_LABELS, GRADE_LABELS, build_journey

RETURN_DAYS = 60
PIECE_LABELS = {"grades": "成績", "credential": "證照", "activity": "活動", "competition": "競賽", "service": "服務", "leadership": "幹部"}


def _add_link(category):
    if category in ("grades", "credential"):
        return url_for("student.learning_profile_upload_page")
    return url_for("student.portfolio_new", category=category)


def _aware(moment):
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def away_days(user, now=None):
    logins = (AuditLog.query.filter_by(user_id=user.id, action="student.login")
              .order_by(AuditLog.created_at.desc()).limit(2).all())
    if len(logins) < 2:
        return None
    days = (_aware(logins[0].created_at) - _aware(logins[1].created_at)).days
    return days if days >= RETURN_DAYS else None


def journey_home(user, journey=None, now=None):
    journey = journey or build_journey(user)
    grade = journey["current_grade"] or 1
    words = {stop["grade"]: stop["title"].split("・")[-1] for stop in FIVE_YEAR_PLAN}

    stops = [{
        "grade": year["grade"],
        "label": GRADE_LABELS[year["grade"]],
        "word": words.get(year["grade"], ""),
        "count": year["count"],
        "state": "past" if year["grade"] < grade else ("now" if year["grade"] == grade else "future"),
    } for year in journey["years"]]

    this_year = next(year for year in journey["years"] if year["grade"] == grade)
    pieces = [{
        "key": key,
        "label": PIECE_LABELS[key],
        "full_label": CATEGORY_LABELS[key],
        "filled": len(this_year["categories"][key]) > 0,
        "href": _add_link(key),
    } for key in CATEGORY_KEYS]

    previous = next((year for year in journey["years"] if year["grade"] == grade - 1), None)
    return {
        "grade": grade,
        "grade_label": GRADE_LABELS[grade],
        "stops": stops,
        "pieces": pieces,
        "blanks": sum(1 for piece in pieces if not piece["filled"]),
        "away_days": away_days(user, now),
        "previous": {"label": previous["label"], "count": previous["count"]} if previous else None,
    }
