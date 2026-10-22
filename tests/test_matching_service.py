"""A3 媒合排序：全部校系判斷可不可報、依契合度排序，每一間都寫理由。"""
from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import (AdmissionProgram, AdmissionRequirementItem, CredentialRecord, StudentProfile, User)
from app.services.gap_service import analyze_gap
from app.services.matching_service import load_conditions, rank_programs


@pytest.fixture()
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        db.create_all()
        yield app


def make_student(admission_year=111):
    student = User(username="stu", display_name="stu", role="student")
    student.set_password("pw")
    db.session.add(student)
    db.session.flush()
    db.session.add(StudentProfile(user_id=student.id, student_no="stu", class_name="資管科五甲",
                                  admission_year=admission_year))
    db.session.flush()
    return student


def make_program(code, items, year=116, school="測試大學"):
    program = AdmissionProgram(program_code=code, admission_year=year, school_name=school,
                               department_name="資管系", status="published")
    for order, (name, weight, keys) in enumerate(items):
        program.items.append(AdmissionRequirementItem(
            source_item_name=name, weight_percent=weight, mapped_categories=keys, sort_order=order))
    db.session.add(program)
    db.session.flush()
    return program


FRESH_ONLY = {"type": "fresh_graduate", "text": "限應屆畢業生（測試原文）", "source": "測試簡章 p.3"}


def test_eligible_programs_are_sorted_by_fit_from_high_to_low(app):
    student = make_student()
    db.session.add(CredentialRecord(student_id=student.id, credential_name="網頁設計丙級", issue_date=date(2025, 3, 1)))
    low = make_program("900001", [("歷年成績", 100, "grades")])
    high = make_program("900002", [("證照", 100, "credential")])

    ranked = rank_programs(student, [low, high], conditions={})

    assert [row["program"].program_code for row in ranked] == ["900002", "900001"]
    assert [row["status"] for row in ranked] == ["eligible", "eligible"]


def test_fit_is_the_same_number_as_gap_readiness(app):
    student = make_student()
    db.session.add(CredentialRecord(student_id=student.id, credential_name="丙級", issue_date=date(2025, 3, 1)))
    program = make_program("900001", [("證照", 40, "credential"), ("歷年成績", 60, "grades")])

    ranked = rank_programs(student, [program], conditions={})

    assert ranked[0]["fit"] == analyze_gap(student, program)["readiness"] == 40


def test_graduate_cannot_apply_to_fresh_graduate_only_program_and_is_listed_last(app):
    student = make_student(admission_year=110)  # 推算 115 年畢業，報 116 學年度已不是應屆
    fresh_only = make_program("900001", [("證照", 100, "credential")])
    open_program = make_program("900002", [("歷年成績", 100, "grades")])

    ranked = rank_programs(student, [fresh_only, open_program], conditions={"900001": [FRESH_ONLY]})

    assert [row["program"].program_code for row in ranked] == ["900002", "900001"]
    last = ranked[-1]
    assert last["status"] == "ineligible"
    assert any("應屆" in reason and "115" in reason for reason in last["reasons"])


def test_student_graduating_in_the_admission_year_meets_fresh_graduate_rule(app):
    student = make_student(admission_year=111)  # 推算 116 年畢業
    program = make_program("900001", [("證照", 100, "credential")])

    ranked = rank_programs(student, [program], conditions={"900001": [FRESH_ONLY]})

    assert ranked[0]["status"] == "eligible"
    assert any("應屆" in reason for reason in ranked[0]["reasons"])


def test_younger_student_is_fresh_graduate_when_they_apply_later(app):
    student = make_student(admission_year=113)  # 推算 118 年畢業，到時候報考仍是應屆
    program = make_program("900001", [("證照", 100, "credential")])

    ranked = rank_programs(student, [program], conditions={"900001": [FRESH_ONLY]})

    assert ranked[0]["status"] == "eligible"


def test_missing_admission_year_needs_check_instead_of_eligible(app):
    student = make_student(admission_year=None)
    program = make_program("900001", [("證照", 100, "credential")])

    ranked = rank_programs(student, [program], conditions={"900001": [FRESH_ONLY]})

    assert ranked[0]["status"] == "needs_check"
    assert any("入學年度" in reason for reason in ranked[0]["reasons"])


def test_unknown_condition_type_needs_check_and_shows_original_text(app):
    student = make_student()
    program = make_program("900001", [("證照", 100, "credential")])
    odd = {"type": "other", "text": "須參加本校舉辦之說明會", "source": "測試簡章 p.5"}

    ranked = rank_programs(student, [program], conditions={"900001": [odd]})

    assert ranked[0]["status"] == "needs_check"
    assert any("須參加本校舉辦之說明會" in reason for reason in ranked[0]["reasons"])


def test_needs_check_is_listed_between_eligible_and_ineligible(app):
    student = make_student(admission_year=110)
    eligible = make_program("900001", [("證照", 100, "credential")])
    check = make_program("900002", [("證照", 100, "credential")])
    blocked = make_program("900003", [("證照", 100, "credential")])
    odd = {"type": "other", "text": "其他條件", "source": ""}

    ranked = rank_programs(student, [blocked, check, eligible],
                           conditions={"900002": [odd], "900003": [FRESH_ONLY]})

    assert [row["status"] for row in ranked] == ["eligible", "needs_check", "ineligible"]


def test_every_program_gets_a_reason_naming_its_heaviest_item(app):
    student = make_student()
    db.session.add(CredentialRecord(student_id=student.id, credential_name="丙級", issue_date=date(2025, 3, 1)))
    program = make_program("900001", [("歷年成績", 30, "grades"), ("證照證明", 70, "credential")])

    ranked = rank_programs(student, [program], conditions={})

    reasons = " ".join(ranked[0]["reasons"])
    assert "證照證明" in reasons and "70%" in reasons
    assert "歷年成績" in reasons  # 還缺的項目也要說


def test_program_with_only_self_prepared_items_has_no_fit_but_still_a_reason(app):
    student = make_student()
    program = make_program("900001", [("自傳", 100, "autobiography")])

    ranked = rank_programs(student, [program], conditions={})

    assert ranked[0]["fit"] is None
    assert ranked[0]["reasons"]


def test_related_departments_rank_before_unrelated_ones_with_higher_fit(app):
    student = make_student()
    db.session.add(CredentialRecord(student_id=student.id, credential_name="丙級", issue_date=date(2025, 3, 1)))
    unrelated = make_program("900001", [("證照", 100, "credential")])
    unrelated.department_name = "模具工程系"
    related = make_program("900002", [("證照", 50, "credential"), ("歷年成績", 50, "grades")])
    related.department_name = "資訊管理系"

    ranked = rank_programs(student, [unrelated, related], conditions={})

    assert [row["program"].department_name for row in ranked] == ["資訊管理系", "模具工程系"]
    assert any("資管" in reason for reason in ranked[0]["reasons"])
    assert any("關聯較低" in reason for reason in ranked[1]["reasons"])
    assert ranked[1]["status"] == "eligible"  # 不相關不代表不能報


def test_load_conditions_groups_rows_by_program_code(tmp_path):
    path = tmp_path / "conditions.csv"
    path.write_text("志願代碼,條件類型,條件原文,出處\n"
                    "208003,fresh_graduate,限應屆,示範\n"
                    "208003,other,須面試,示範\n"
                    "208001,fresh_graduate,限應屆,示範\n", encoding="utf-8-sig")

    conditions = load_conditions(path)

    assert [c["type"] for c in conditions["208003"]] == ["fresh_graduate", "other"]
    assert conditions["208001"][0]["text"] == "限應屆"
    assert conditions["208001"][0]["source"] == "示範"


def test_load_conditions_returns_empty_when_file_is_missing(tmp_path):
    assert load_conditions(tmp_path / "missing.csv") == {}


# ---------- 推薦排序頁 ----------

@pytest.fixture()
def site(tmp_path, monkeypatch):
    from app.services import matching_service
    conditions = tmp_path / "conditions.csv"
    conditions.write_text("志願代碼,條件類型,條件原文,出處\n900001,fresh_graduate,限應屆畢業生,測試簡章 p.3\n",
                          encoding="utf-8-sig")
    monkeypatch.setattr(matching_service, "CONDITIONS_FILE", conditions)
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        db.create_all()
        make_student(admission_year=110)
        make_program("900001", [("證照證明", 100, "credential")], school="應屆大學")
        make_program("900002", [("歷年成績", 100, "grades")], school="開放大學")
        db.session.commit()
    yield app


def login(app):
    client = app.test_client()
    client.post("/login", data={"username": "stu", "password": "pw"})
    return client


def test_matching_page_lists_every_program_with_status_and_reasons(site):
    html = login(site).get("/student/matching").get_data(as_text=True)

    assert "開放大學" in html and "應屆大學" in html
    assert html.index("開放大學") < html.index("應屆大學")  # 不可報的排最後，但仍列出
    assert "不可報" in html and "可報" in html
    assert "限應屆畢業生" in html
    assert "不是錄取機率" in html


def test_targets_page_links_to_matching_page(site):
    html = login(site).get("/student/targets").get_data(as_text=True)

    assert "/student/matching" in html


def test_matching_page_requires_student_login(site):
    response = site.test_client().get("/student/matching")

    assert response.status_code in (302, 401, 403)
