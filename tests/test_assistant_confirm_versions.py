"""資管科小助手第 1 步「確認與版本」（規格第 10 節）。"""
from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    AdmissionProgram,
    ClassAdvisor,
    CredentialRecord,
    LearningCourseRecord,
    Portfolio,
    StudentProfile,
    User,
)
from app.services.admission_service import import_seed_programs
from app.services.autobiography_service import build_facts
from app.services.journey_service import academic_year_of

# 讓「stu」不論哪一年跑測試都是專三
GRADE3_ADMISSION_YEAR = academic_year_of(date.today()) - 2


@pytest.fixture()
def app(tmp_path):
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True, "UPLOAD_FOLDER": str(tmp_path)})
    with app.app_context():
        db.create_all()
        import_seed_programs()
        for username, role in (("stu", "student"), ("other", "student"), ("teacher", "teacher"),
                               ("stranger", "teacher")):
            user = User(username=username, display_name=username, role=role)
            user.set_password("pw")
            db.session.add(user)
        db.session.flush()
        stu = User.query.filter_by(username="stu").one()
        other = User.query.filter_by(username="other").one()
        db.session.add(StudentProfile(user_id=stu.id, student_no="111534100", class_name="資管科三甲",
                                      admission_year=GRADE3_ADMISSION_YEAR))
        db.session.add(StudentProfile(user_id=other.id, student_no="111534200", class_name="資管科三乙",
                                      admission_year=GRADE3_ADMISSION_YEAR))
        teacher = User.query.filter_by(username="teacher").one()
        db.session.add(ClassAdvisor(teacher_id=teacher.id, class_name="資管科三甲", school_year=115))
        db.session.commit()
        yield app


def login(app, username="stu"):
    client = app.test_client()
    client.post("/login", data={"username": username, "password": "pw"})
    return client


def user_id(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).one().id


def program_id(app, code="208003"):
    with app.app_context():
        return AdmissionProgram.query.filter_by(program_code=code).one().id


def add_portfolio(app, username="stu", title="校園黑客松", status="draft", **extra):
    with app.app_context():
        record = Portfolio(student_id=user_id(app, username), title=title, category="competition",
                           school_year=3, status=status, **extra)
        db.session.add(record)
        db.session.commit()
        return record.id


def facts_text(app, username="stu"):
    with app.app_context():
        student = User.query.filter_by(username=username).one()
        program = db.session.get(AdmissionProgram, program_id(app))
        return [item["text"] for item in build_facts(student, program)["items"]]


# ---------- Task 1：經歷確認＋build_facts 只讀已確認資料 ----------

def test_build_facts_skips_unconfirmed_records(app):
    add_portfolio(app, title="還在寫的草稿", status="draft")
    add_portfolio(app, title="確認過的競賽", status="confirmed")
    add_portfolio(app, title="舊流程送出的", status="submitted")
    with app.app_context():
        sid = user_id(app, "stu")
        db.session.add(LearningCourseRecord(student_id=sid, course_name="程式設計", normalized_course_name="程式設計",
                                            score=90, confirmation_status="confirmed"))
        db.session.add(LearningCourseRecord(student_id=sid, course_name="沒確認的課", normalized_course_name="沒確認的課",
                                            score=80, confirmation_status="pending"))
        db.session.add(CredentialRecord(student_id=sid, credential_name="網頁設計乙級", confirmation_status="confirmed"))
        db.session.add(CredentialRecord(student_id=sid, credential_name="沒確認的證照", confirmation_status="pending"))
        db.session.commit()

    texts = " ".join(facts_text(app))

    assert "確認過的競賽" in texts
    assert "舊流程送出的" in texts
    assert "程式設計" in texts
    assert "網頁設計乙級" in texts
    assert "還在寫的草稿" not in texts
    assert "沒確認的課" not in texts
    assert "沒確認的證照" not in texts


def test_student_confirms_own_record(app):
    record_id = add_portfolio(app)

    response = login(app).post(f"/student/portfolio/{record_id}/confirm")

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Portfolio, record_id).status == "confirmed"


def test_student_cannot_confirm_someone_elses_record(app):
    record_id = add_portfolio(app, username="other")

    response = login(app).post(f"/student/portfolio/{record_id}/confirm")

    assert response.status_code in (403, 404)
    with app.app_context():
        assert db.session.get(Portfolio, record_id).status == "draft"


def test_form_save_and_confirm(app):
    client = login(app)
    form = {"title": "資訊週志工", "category": "service", "school_year": "2", "semester": "1"}

    client.post("/student/portfolio", data=form)
    client.post("/student/portfolio", data={**form, "title": "迎新宿營", "confirm": "1"})

    with app.app_context():
        assert Portfolio.query.filter_by(title="資訊週志工").one().status == "draft"
        assert Portfolio.query.filter_by(title="迎新宿營").one().status == "confirmed"


def test_editing_confirmed_record_needs_confirming_again(app):
    record_id = add_portfolio(app, status="confirmed")
    client = login(app)
    form = {"title": "校園黑客松（改）", "category": "competition", "school_year": "3"}

    client.post(f"/student/portfolio/{record_id}/edit", data=form)
    with app.app_context():
        assert db.session.get(Portfolio, record_id).status == "draft"

    client.post(f"/student/portfolio/{record_id}/edit", data={**form, "confirm": "1"})
    with app.app_context():
        assert db.session.get(Portfolio, record_id).status == "confirmed"


def test_portfolio_page_shows_unconfirmed_tag_and_confirm_button(app):
    record_id = add_portfolio(app)

    html = login(app).get("/student/portfolio").get_data(as_text=True)

    assert "未確認" in html
    assert f"/student/portfolio/{record_id}/confirm" in html


# ---------- Task 2：年級限制與目標校系上限 ----------

def set_admission_year(app, year, username="stu"):
    with app.app_context():
        profile = StudentProfile.query.filter_by(user_id=user_id(app, username)).one()
        profile.admission_year = year
        db.session.commit()


def add_programs(app, count, year=None):
    """再建立幾個正式校系（種子資料只有 4 個）。"""
    year = year or academic_year_of(date.today())
    ids = []
    with app.app_context():
        start = AdmissionProgram.query.count()
        for index in range(start, start + count):
            program = AdmissionProgram(program_code=f"9{index:05d}", admission_year=year, school_name=f"測試大學{index}",
                                       department_name="資管系", status="published")
            db.session.add(program)
            db.session.flush()
            ids.append(program.id)
        db.session.commit()
    return ids


def target_count(app):
    from app.models import StudentTarget
    with app.app_context():
        return StudentTarget.query.filter_by(student_id=user_id(app, "stu")).count()


def test_sixth_target_is_refused(app):
    client = login(app)
    with app.app_context():
        seeded = [p.id for p in AdmissionProgram.query.filter_by(status="published").all()]
    for pid in seeded + add_programs(app, 1):
        client.post("/student/targets", data={"program_id": pid})
    assert target_count(app) == 5

    response = client.post("/student/targets", data={"program_id": add_programs(app, 1)[0]})

    assert target_count(app) == 5
    assert "最多 5 所" in response.get_data(as_text=True)


def test_old_year_target_does_not_use_a_slot_and_can_be_removed(app):
    from app.models import StudentTarget
    stu_id = user_id(app, "stu")
    with app.app_context():
        newest = AdmissionProgram.query.filter_by(program_code="208003").one()
        old = AdmissionProgram(program_code="208003", admission_year=newest.admission_year - 1,
                               school_name=newest.school_name, department_name=newest.department_name,
                               status="published")
        db.session.add(old)
        db.session.flush()
        db.session.add(StudentTarget(student_id=stu_id, rule_version_id=old.id))
        db.session.commit()
        old_id = old.id
    client = login(app)

    html = client.get("/student/targets").get_data(as_text=True)
    assert "舊學年度" in html
    assert "已選 0／5" in html

    client.post(f"/student/targets/{old_id}/remove")
    assert target_count(app) == 0


def test_missing_admission_year_blocks_and_can_be_filled_once(app):
    set_admission_year(app, None)
    client = login(app)
    pid = program_id(app)

    blocked = client.post("/student/targets", data={"program_id": pid})
    assert blocked.status_code == 403
    assert "入學學年度" in blocked.get_data(as_text=True)
    assert target_count(app) == 0
    record = client.post("/student/portfolio", data={"title": "志工", "category": "service", "school_year": "1"})
    assert record.status_code == 400
    assert "入學學年度" in record.get_data(as_text=True)

    client.post("/student/profile/admission-year", data={"admission_year": str(GRADE3_ADMISSION_YEAR)})
    client.post("/student/profile/admission-year", data={"admission_year": "100"})
    with app.app_context():
        assert StudentProfile.query.filter_by(user_id=user_id(app, "stu")).one().admission_year == GRADE3_ADMISSION_YEAR
    client.post("/student/targets", data={"program_id": pid})
    assert target_count(app) == 1


def test_record_for_a_future_grade_is_refused_and_input_kept(app):
    client = login(app)

    response = client.post("/student/portfolio", data={"title": "未來的比賽", "category": "competition", "school_year": "4"})
    html = response.get_data(as_text=True)
    roc = client.post("/student/portfolio", data={"title": "未來的比賽", "category": "competition",
                                                  "school_year": str(GRADE3_ADMISSION_YEAR + 3)})
    ok = client.post("/student/portfolio", data={"title": "現在的比賽", "category": "competition", "school_year": "3"})

    assert response.status_code == 400
    assert "專三" in html and "未來的比賽" in html
    assert roc.status_code == 400
    assert ok.status_code == 302


def test_course_for_a_future_grade_is_refused(app, tmp_path):
    import json
    from app.models import DocumentExtraction, SourceDocument
    with app.app_context():
        document = SourceDocument(owner_id=user_id(app, "stu"), document_type="transcript", display_name="t.pdf",
                                  file_path=str(tmp_path / "t.pdf"), sha256="c" * 64, status="extracted")
        db.session.add(document)
        db.session.flush()
        db.session.add(DocumentExtraction(source_document_id=document.id, provider="fake", status="extracted",
                                          result_json={"courses": []}))
        db.session.commit()
        document_id = document.id
    client = login(app)

    response = client.post(f"/student/learning-profile/documents/{document_id}/review/confirm", data={
        "courses_json": json.dumps([{"course_name": "專題實作", "school_year": 5, "score": 90}]),
        "credentials_json": "[]",
    })

    assert response.status_code == 400
    assert "專三" in response.get_data(as_text=True)


def test_first_year_student_can_look_but_not_send_or_write(app):
    set_admission_year(app, academic_year_of(date.today()))
    client = login(app)
    pid = program_id(app)
    client.post("/student/targets", data={"program_id": pid})

    gap = client.get(f"/student/targets/{pid}")
    review = client.post(f"/student/targets/{pid}/review")
    generate = client.post("/student/autobiography/generate", data={"program_id": pid, "motivation": "想讀資管"})

    from app.models import LearningProfileOutput, PackageReview
    assert gap.status_code == 200
    assert review.status_code == 403
    assert generate.status_code == 403
    assert "專二" in review.get_data(as_text=True)
    with app.app_context():
        assert PackageReview.query.count() == 0
        assert LearningProfileOutput.query.count() == 0


# ---------- Task 3：送審快照、導師確認與撤回 ----------

def choose_and_send(app, client, pid=None):
    pid = pid or program_id(app)
    client.post("/student/targets", data={"program_id": pid})
    client.post(f"/student/targets/{pid}/review")
    return pid


def latest_review_row(app):
    from app.models import PackageReview
    with app.app_context():
        review = PackageReview.query.order_by(PackageReview.id.desc()).first()
        return {"id": review.id, "status": review.status, "snapshot": review.snapshot_json}


def add_credential(app, name="勞動部網頁設計乙級"):
    with app.app_context():
        db.session.add(CredentialRecord(student_id=user_id(app, "stu"), credential_name=name, level="乙級"))
        db.session.commit()


def test_request_review_saves_a_snapshot(app):
    add_portfolio(app, title="確認過的競賽", status="confirmed")
    add_portfolio(app, title="還在寫的草稿", status="draft")

    choose_and_send(app, login(app))

    snapshot = latest_review_row(app)["snapshot"]
    texts = " ".join(fact["text"] for fact in snapshot["facts"])
    assert "確認過的競賽" in texts
    assert "還在寫的草稿" not in texts
    assert snapshot["program"]["id"] == program_id(app)
    assert "readiness" in snapshot
    assert snapshot["autobiography"] is None


def test_resending_while_pending_updates_the_same_snapshot(app):
    client = login(app)
    choose_and_send(app, client)
    first = latest_review_row(app)
    add_credential(app)

    client.post(f"/student/targets/{program_id(app)}/review")

    second = latest_review_row(app)
    from app.models import PackageReview
    with app.app_context():
        assert PackageReview.query.count() == 1
    assert second["id"] == first["id"]
    assert any("網頁設計乙級" in fact["text"] for fact in second["snapshot"]["facts"])


def test_confirmed_snapshot_does_not_change_when_student_adds_credential(app):
    from app.services.review_snapshot_service import confirmed_facts
    client = login(app)
    pid = choose_and_send(app, client)
    review_id = latest_review_row(app)["id"]
    login(app, "teacher").post(f"/teacher/package-reviews/{review_id}", data={"decision": "confirmed"})
    before = latest_review_row(app)["snapshot"]

    add_credential(app)
    client.post(f"/student/targets/{pid}/review")

    from app.models import PackageReview
    with app.app_context():
        confirmed = db.session.get(PackageReview, review_id)
        assert confirmed.snapshot_json == before
        assert confirmed.status == "confirmed"
        student = User.query.filter_by(username="stu").one()
        program = db.session.get(AdmissionProgram, pid)
        assert not any("網頁設計乙級" in fact["text"] for fact in confirmed_facts(student, program))
        assert PackageReview.query.count() == 2
    teacher_html = login(app, "teacher").get(f"/teacher/students/{user_id(app, 'stu')}").get_data(as_text=True)
    assert "新增" in teacher_html and "勞動部網頁設計乙級" in teacher_html


def test_teacher_confirm_and_withdraw_are_logged(app):
    from app.models import AuditLog
    choose_and_send(app, login(app))
    review_id = latest_review_row(app)["id"]
    teacher = login(app, "teacher")
    teacher.post(f"/teacher/package-reviews/{review_id}", data={"decision": "confirmed"})

    no_reason = teacher.post(f"/teacher/package-reviews/{review_id}/withdraw", data={"reason": " "})
    assert no_reason.status_code == 400
    teacher.post(f"/teacher/package-reviews/{review_id}/withdraw", data={"reason": "按錯了，自傳還沒看完"})

    assert latest_review_row(app)["status"] == "pending"
    with app.app_context():
        actions = [log.action for log in AuditLog.query.order_by(AuditLog.id).all()]
        withdraw = AuditLog.query.filter_by(action="package_review.withdraw").one()
    assert actions == ["package_review.confirm", "package_review.withdraw"]
    assert withdraw.detail_json["reason"] == "按錯了，自傳還沒看完"
    assert withdraw.target_id == review_id


def test_other_class_teacher_cannot_withdraw(app):
    choose_and_send(app, login(app))
    review_id = latest_review_row(app)["id"]
    login(app, "teacher").post(f"/teacher/package-reviews/{review_id}", data={"decision": "confirmed"})

    response = login(app, "stranger").post(f"/teacher/package-reviews/{review_id}/withdraw", data={"reason": "測試"})

    assert response.status_code == 403
    assert latest_review_row(app)["status"] == "confirmed"


def test_teacher_still_sees_review_after_student_cancels_target(app):
    client = login(app)
    pid = choose_and_send(app, client)
    client.post(f"/student/targets/{pid}/remove")

    html = login(app, "teacher").get(f"/teacher/students/{user_id(app, 'stu')}").get_data(as_text=True)

    assert "國立臺北商業大學" in html
    assert "學生已取消這個目標" in html


def test_review_snapshot_migration_upgrades_and_downgrades(tmp_path):
    from sqlalchemy import inspect
    app = create_app({"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'm.db'}", "TESTING": True})
    runner = app.test_cli_runner()

    assert runner.invoke(args=["db", "upgrade"]).exit_code == 0
    with app.app_context():
        columns = {c["name"] for c in inspect(db.engine).get_columns("package_reviews")}
        assert "snapshot_json" in columns
        assert inspect(db.engine).has_table("ai_daily_usage")
    assert runner.invoke(args=["db", "downgrade", "d5b9a2c7e104"]).exit_code == 0
    with app.app_context():
        db.engine.dispose()
        columns = {c["name"] for c in inspect(db.engine).get_columns("package_reviews")}
        assert "snapshot_json" not in columns
        assert not inspect(db.engine).has_table("ai_daily_usage")
