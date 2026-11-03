"""資管科小助手可以呼叫的工具（Agent 的「手」）。

安全原則：
- 每個工具都只「讀」資料，不能新增、修改、刪除或送出任何東西。
- 「是誰在問」一律用登入的帳號判斷（user 參數），AI 不能指定別人的帳號。
  學生只查得到自己；導師只查得到 class_advisors 指定班級的學生。
- 新增工具：寫一個函式＋在 STUDENT_TOOLS／TEACHER_TOOLS 加一筆說明。
"""

from app.extensions import db
import re

from app.models import AdmissionScheduleEvent, CredentialRecord, Portfolio, StudentProfile, StudentTarget, User
from app.services import knowledge_service
from app.services.admission_service import published_programs
from app.services.autobiography_service import CONFIRMED_PORTFOLIO_STATUSES, build_facts, latest_draft
from app.services.gap_service import ALL_LABELS, analyze_gap
from app.services.journey_service import CATEGORY_KEYS, CATEGORY_LABELS, build_journey
from app.services.package_service import latest_review
from app.services.teacher_scope import can_view_student, students_for_teacher

REVIEW_TEXT = {"pending": "等待導師確認", "confirmed": "導師已確認", "needs_revision": "導師請學生修改"}


class ToolError(Exception):
    """工具不能執行（例如查別班學生），訊息會交給 AI 轉告使用者。"""


# ---------- 共用 ----------

def _program_by_code(code):
    program = next((p for p in published_programs() if p.program_code == str(code).strip()), None)
    if not program:
        raise ToolError(f"找不到志願代碼 {code} 的正式校系資料。")
    return program


def _overview(student):
    journey = build_journey(student)
    profile = student.student_profile
    targets = []
    for target in StudentTarget.query.filter_by(student_id=student.id).order_by(StudentTarget.selected_at):
        gap = analyze_gap(student, target.program, journey)
        review = latest_review(student, target.program)
        draft = latest_draft(student, target.program)
        targets.append({
            "program_code": target.program.program_code,
            "school_department": f"{target.program.school_name} {target.program.department_name}",
            "readiness_percent": gap["readiness"],
            "missing_categories": [CATEGORY_LABELS[k] for k in gap["missing_keys"]],
            "teacher_review": REVIEW_TEXT.get(review.status, "") if review else "尚未送導師確認",
            "autobiography": ("已修改儲存" if draft.content_json.get("edited") else "有草稿未修改") if draft else "還沒寫",
        })
    return {
        "name": student.display_name,
        "student_no": profile.student_no if profile else None,
        "class_name": profile.class_name if profile else None,
        "current_grade": f"專{'一二三四五'[journey['current_grade'] - 1]}" if journey.get("current_grade") else "未知",
        "record_counts": {CATEGORY_LABELS[k]: journey["totals"][k] for k in CATEGORY_KEYS},
        "credentials": [c.credential_name + (f"（{c.level}）" if c.level else "")
                        for c in CredentialRecord.query.filter_by(
                            student_id=student.id, confirmation_status="confirmed")],
        "targets": targets,
    }


def _gap(student, program):
    gap = analyze_gap(student, program)
    return {
        "school_department": f"{program.school_name} {program.department_name}",
        "admission_year": program.admission_year,
        "readiness_percent": gap["readiness"],
        "readiness_rule": "準備度＝Σ（項目加權×已有資料比例）÷ 列入計算的加權；自傳、專題屬於自己準備的文件，不列入計算",
        "items": [{
            "item": item["name"], "weight_percent": item["weight"],
            "status": {"complete": "已備齊", "partial": "部分備齊", "missing": "缺資料", "prepare": "需自己準備的文件"}[item["status"]],
            "have": [f"{ALL_LABELS[k]} {item['counts'][k]} 筆" for k in item["have"]],
            "missing": [ALL_LABELS[k] for k in item["missing"]],
            "documents_to_prepare": [ALL_LABELS[k] for k in item["documents"]],
            "mapping_unconfirmed": item["mapping_pending"],
        } for item in gap["items"]],
    }


def _consistency(student, program):
    draft = latest_draft(student, program)
    if not draft:
        return {"autobiography": None, "note": "這個校系還沒有自傳草稿，請先用「自傳小幫手」寫。"}
    facts = build_facts(student, program)["items"]
    records = (Portfolio.active().filter_by(student_id=student.id)
               .filter(Portfolio.status.in_(CONFIRMED_PORTFOLIO_STATUSES)).all())
    return {
        "autobiography_paragraphs": [{"title": p["title"], "text": p["text"]} for p in draft.content_json["paragraphs"]],
        "confirmed_facts": [f["text"] for f in facts],
        "records_without_evidence_files": [r.title for r in records if r.category in CATEGORY_KEYS and not r.evidence_items],
        "instruction": "逐句比對自傳中的具體經歷、獎項、證照、成績，是否都出現在 confirmed_facts；"
                       "列出找不到依據的句子，以及有寫進自傳但沒有佐證檔案的經歷。",
    }


# ---------- 學生與導師都能用 ----------

def search_department_rules(user, query):
    results = knowledge_service.search(query)
    if not results:
        return {"found": False, "available_documents": knowledge_service.documents(),
                "hint": "沒有找到，請換成文件裡可能出現的關鍵字再查一次。"}
    return {"found": True, "passages": results}


def list_admission_programs(user):
    return {"programs": [{
        "program_code": p.program_code, "admission_year": p.admission_year,
        "school_department": f"{p.school_name} {p.department_name}", "category": p.admission_category,
        "weights": [f"{i.source_item_name} {i.weight_percent}%" for i in p.items],
    } for p in published_programs()]}


def _official_url(program):
    """種子資料有些把網址留在來源備註，統一只取 http(s) 官方連結。"""
    if program.source_url and program.source_url.startswith(("https://", "http://")):
        return program.source_url
    match = re.search(r"https?://[^\s)）]+", program.source_note or "")
    return match.group(0) if match else ""


def get_latest_admission_sources(user):
    """回傳學生目前可看的已發布招生資料及其可追溯來源。

    學生只能讀取管理者已發布的版本；候選資料、未審核的 Agent 擷取結果不會出現在回答裡。
    """
    sources = []
    seen = set()
    for program in published_programs():
        url = _official_url(program)
        key = (url, program.admission_year, program.school_name, program.department_name)
        if key in seen:
            continue
        seen.add(key)
        checked = program.checked_at.isoformat() if program.checked_at else "未記錄查核日期"
        sources.append({
            "title": f"{program.school_name}{program.department_name}（{program.admission_year} 學年度）",
            "url": url,
            "detail": f"資料年度：{program.admission_year}；最後查核：{checked}",
        })

    events = (AdmissionScheduleEvent.query.filter_by(status="published")
              .order_by(AdmissionScheduleEvent.admission_year.desc(), AdmissionScheduleEvent.start_at).all())
    for event in events:
        if not event.source_url or not event.source_url.startswith(("https://", "http://")):
            continue
        key = (event.source_url, event.admission_year, event.channel)
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "title": f"{event.channel}時程（{event.admission_year} 學年度）",
            "url": event.source_url,
            "detail": f"資料年度：{event.admission_year}；已發布時程",
        })
    return {
        "sources": sources[:12],
        "notice": "僅列出管理者已發布的資料。正式報名資格與日期仍以連結中的招生單位公告為準。",
    }


# ---------- 學生 ----------

def get_my_overview(user):
    return _overview(user)


def get_my_target_gap(user, program_code):
    return _gap(user, _program_by_code(program_code))


def check_my_autobiography(user, program_code):
    return _consistency(user, _program_by_code(program_code))


# ---------- 導師 ----------

def _class_student(teacher, student_no):
    profile = StudentProfile.query.filter_by(student_no=str(student_no).strip()).first()
    student = db.session.get(User, profile.user_id) if profile else None
    if not student or not can_view_student(teacher, student):
        raise ToolError(f"學號 {student_no} 不是你負責班級的學生，不能查詢。")
    return student


def list_my_class_students(user):
    return {"students": [_overview(student) for student in students_for_teacher(user)]}


def get_student_overview(user, student_no):
    return _overview(_class_student(user, student_no))


def get_student_target_gap(user, student_no, program_code):
    return _gap(_class_student(user, student_no), _program_by_code(program_code))


def check_student_autobiography(user, student_no, program_code):
    return _consistency(_class_student(user, student_no), _program_by_code(program_code))


# ---------- 工具說明（給 Gemini 看的） ----------

def _decl(name, description, **params):
    declaration = {"name": name, "description": description}
    if params:
        declaration["parameters"] = {"type": "OBJECT", "properties": {k: {"type": "STRING", "description": v}
                                                                      for k, v in params.items()},
                                     "required": list(params)}
    return declaration


SEARCH = _decl("search_department_rules", "查詢資管科／學校的規定文件：畢業門檻、重補修選課、專題繳交與評分、轉科、二技甄審時程等。",
               query="要查的關鍵字，使用文件可能出現的詞，例如「畢業門檻 證照」")
PROGRAMS = _decl("list_admission_programs", "列出系統中所有正式的二技校系、志願代碼與備審加權。")
ADMISSION_SOURCES = _decl(
    "get_latest_admission_sources",
    "查詢目前已發布招生資料的學年度、最後查核日期與官方來源連結。問到最新簡章、報名日期、招生時程或資料來源時必須先使用。",
)
PROGRAM_CODE = "6 位數志願代碼，例如 208003"
STUDENT_NO = "學生學號"

STUDENT_TOOLS = {
    "search_department_rules": (search_department_rules, SEARCH, "查科上規定"),
    "list_admission_programs": (list_admission_programs, PROGRAMS, "查校系加權"),
    "get_latest_admission_sources": (get_latest_admission_sources, ADMISSION_SOURCES, "查官方招生來源"),
    "get_my_overview": (get_my_overview, _decl(
        "get_my_overview", "查詢目前登入學生自己的資料：年級、六類資料筆數、證照、已選的目標校系、準備度、導師確認與自傳狀態。"),
        "查你的資料"),
    "get_my_target_gap": (get_my_target_gap, _decl(
        "get_my_target_gap", "查詢目前登入學生對某個校系的缺件比對：每個評分項目的加權、已有與缺少的資料。",
        program_code=PROGRAM_CODE), "缺件比對"),
    "check_my_autobiography": (check_my_autobiography, _decl(
        "check_my_autobiography", "取得目前登入學生某校系的自傳與已確認資料，用來檢查自傳內容是否都有依據。",
        program_code=PROGRAM_CODE), "自傳一致性檢查"),
}

TEACHER_TOOLS = {
    "search_department_rules": (search_department_rules, SEARCH, "查科上規定"),
    "list_admission_programs": (list_admission_programs, PROGRAMS, "查校系加權"),
    "get_latest_admission_sources": (get_latest_admission_sources, ADMISSION_SOURCES, "查官方招生來源"),
    "list_my_class_students": (list_my_class_students, _decl(
        "list_my_class_students", "列出導師負責班級的所有學生：資料筆數、目標校系、準備度、是否等待導師確認。"),
        "查本班學生"),
    "get_student_overview": (get_student_overview, _decl(
        "get_student_overview", "查詢導師班上某位學生的資料概況。", student_no=STUDENT_NO), "查學生資料"),
    "get_student_target_gap": (get_student_target_gap, _decl(
        "get_student_target_gap", "查詢導師班上某位學生對某校系的缺件比對。", student_no=STUDENT_NO,
        program_code=PROGRAM_CODE), "缺件比對"),
    "check_student_autobiography": (check_student_autobiography, _decl(
        "check_student_autobiography", "取得導師班上某位學生的自傳與已確認資料，檢查自傳內容是否都有依據。",
        student_no=STUDENT_NO, program_code=PROGRAM_CODE), "自傳一致性檢查"),
}


def tools_for(user):
    return {"student": STUDENT_TOOLS, "teacher": TEACHER_TOOLS}.get(user.role, {})
