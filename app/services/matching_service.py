"""A3 媒合排序 Agent（最小版）：對全部正式校系判斷能不能報、算契合度、排序，每一間都寫理由。

規則（寫在這裡，方便報告時說明；規格見 AI_設計規格_Agent分工規劃_2026-10-22.md）：
- 契合度 = 缺件比對的準備度（gap_service.analyze_gap），兩邊數字一定相同。不是錄取機率。
- 報考資格條件依類型檢查；看不懂的條件或缺少學生資料時一律「需確認」，不當成符合（D8）。
- 排序：可報 → 需確認 → 不可報；同一組裡學群相關的科系在前、學群待確認的居中，再依契合度高到低。
  不可報的仍然列出來，並寫明原因。
- 相關與否比對「學生主要學群」（A2，eligibility_service 依已確認的成績與課綱算出）和「校系學群」（人工對照表）；
  任一邊待確認時理由會明說，不用系名關鍵字猜（系名有「資訊」「數位」不代表屬資訊學群）。
- 這一版的理由由規則產生；之後再交給 AI 改寫成白話（AI 額度用完時仍顯示規則版）。

目前支援的條件類型：
- fresh_graduate（C1 應屆）：預計畢業學年度 = 入學學年度 + 5。報考學年度之前就已畢業的，不是應屆。
- 其他類型：一律「需確認」，並顯示簡章原文。
"""

import csv
from pathlib import Path

from app.services.admission_links import admission_links, load_school_links
from app.services.admission_schedule import load_schedule, timeline
from app.services.eligibility_service import department_groups, load_department_groups, summarize_student_groups
from app.services.gap_service import ALL_LABELS, analyze_gap
from app.services.journey_service import build_journey

CONDITIONS_FILE = Path(__file__).resolve().parents[1] / "content" / "admission_conditions_demo.csv"

# 學群相關（True）→ 待確認（None）→ 不相關（False）
RELATED_ORDER = {True: 0, None: 1, False: 2}

STATUS_ORDER = {"eligible": 0, "needs_check": 1, "ineligible": 2}
STATUS_LABELS = {"eligible": "可報", "needs_check": "需確認", "ineligible": "不可報"}


def load_conditions(path=None):
    """讀報考資格條件 CSV，回傳 {志願代碼: [{type, text, source}]}。檔案不存在時回傳空的。"""
    path = path or CONDITIONS_FILE
    if not Path(path).is_file():
        return {}
    conditions = {}
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            conditions.setdefault(row["志願代碼"], []).append({
                "type": row["條件類型"].strip(),
                "text": row["條件原文"].strip(),
                "source": row["出處"].strip(),
            })
    return conditions


def _cite(condition):
    return f"（出處：{condition['source']}）" if condition.get("source") else ""


def _check_fresh_graduate(student, program, condition):
    profile = student.student_profile
    admission_year = profile.admission_year if profile else None
    if admission_year is None:
        return "needs_check", f"這個志願限應屆畢業生{_cite(condition)}，系統沒有你的入學年度，請確認。"
    graduation_year = admission_year + 5
    if graduation_year < program.admission_year:
        return "ineligible", (f"這個志願限應屆畢業生{_cite(condition)}。依入學年度推算你在 {graduation_year} 年畢業，"
                              f"報考 {program.admission_year} 學年度時已不是應屆；如果你延畢還沒畢業，請告訴導師更正。")
    return "eligible", (f"這個志願限應屆畢業生，依入學年度推算你在 {graduation_year} 年畢業，"
                        f"報考那一年是應屆；如有延畢或休學請告訴導師。")


CHECKS = {"fresh_graduate": _check_fresh_graduate}


def _check_conditions(student, program, conditions):
    status, reasons = "eligible", []
    for condition in conditions:
        check = CHECKS.get(condition["type"])
        if check:
            result, reason = check(student, program, condition)
        else:
            result, reason = "needs_check", f"簡章還有這項條件，系統無法自動判斷，請自己核對：「{condition['text']}」{_cite(condition)}"
        reasons.append(reason)
        if STATUS_ORDER[result] > STATUS_ORDER[status]:
            status = result
    return status, reasons


def _labels(keys):
    return "、".join(ALL_LABELS.get(key, key) for key in keys)


def _fit_reasons(gap):
    counted = [item for item in gap["items"] if item["fraction"] is not None]
    if not counted:
        return ["這個校系的評分項目都要自己準備（例如自傳、專題），系統還算不出契合度。"]
    reasons = []
    for item in sorted(counted, key=lambda item: -item["weight"]):
        if item["status"] == "complete":
            reasons.append(f"「{item['name']}」占 {item['weight']}%，你已有{_labels(item['have'])}資料。")
        elif item["status"] == "partial":
            reasons.append(f"「{item['name']}」占 {item['weight']}%，你已有{_labels(item['have'])}，"
                           f"還缺{_labels(item['missing'])}。")
        else:
            reasons.append(f"「{item['name']}」占 {item['weight']}%，你還沒有{_labels(item['missing'])}資料。")
    return reasons


def is_related(program, student_groups, department_table=None):
    """學生主要學群是否屬於這個校系的學群；任一邊待確認時回傳 None（排在相關與不相關中間）。"""
    department = department_groups(program, department_table)
    if student_groups["main_group"] is None or department is None:
        return None
    return student_groups["main_group"] in department["groups"]


def _relation_reason(related, student_groups, program, department_table=None):
    if student_groups["main_group"] is None:
        return f"和你的背景是否相關：{student_groups['reason']}"
    department = department_groups(program, department_table)
    if department is None:
        return "這個系的學群待確認：對照表還沒有這個系（或依據不足），請自己看簡章的報考資格與課程。"
    main = student_groups["main_group"]
    basis = (f"你修過的{main}類專業科目 {student_groups['group_counts'][main]} 科，"
             f"這個系屬{'、'.join(group + '學群' for group in department['groups'])}（依據：{department['basis']}）")
    if related:
        return f"{basis}，和你的背景相關。"
    return f"{basis}，和你的{main}學群關聯較低，可以參考，但排在相關科系後面。"


def rank_programs(student, programs, journey=None, conditions=None):
    """回傳排序好的 [{program, status, status_label, fit, related, reasons, gap, links, schedule}]。"""
    journey = journey or build_journey(student)
    conditions = load_conditions() if conditions is None else conditions
    school_links = load_school_links()
    schedule = load_schedule()
    student_groups = summarize_student_groups(student)
    department_table = load_department_groups()
    rows = []
    for program in programs:
        gap = analyze_gap(student, program, journey)
        status, condition_reasons = _check_conditions(student, program, conditions.get(program.program_code, []))
        related = is_related(program, student_groups, department_table)
        rows.append({
            "program": program,
            "status": status,
            "status_label": STATUS_LABELS[status],
            "fit": gap["readiness"],
            "related": related,
            "reasons": (condition_reasons + [_relation_reason(related, student_groups, program, department_table)]
                        + _fit_reasons(gap)),
            "gap": gap,
            "links": admission_links(program, school_links),
            "schedule": timeline(program, schedule),
        })
    rows.sort(key=lambda row: (STATUS_ORDER[row["status"]], RELATED_ORDER[row["related"]], row["fit"] is None,
                               -(row["fit"] or 0)))
    return rows
