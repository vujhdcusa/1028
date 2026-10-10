from pathlib import Path
from hashlib import sha256
import json
from datetime import date, datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for

from app.extensions import db
from app.models import (
    AdmissionProgram,
    CredentialRecord,
    DocumentExtraction,
    LearningCourseRecord,
    LearningProfileOutput,
    Portfolio,
    PortfolioEvidence,
    SourceDocument,
    StudentProfile,
    StudentTarget,
    User,
)
from app.routes.main import get_current_user, role_required
from app.services.focus_service import focus_view
from app.services.portfolio_service import owned_portfolio, create_submission_snapshot
from app.security import validate_upload_filename
from app.services.document_analysis_service import ALLOWED_DOCUMENT_TYPES, analyze_document
from app.services.learning_profile_docx_service import output_to_docx_bytes
from app.services.learning_profile_service import generate_learning_profile_outputs
from app.services.admission_service import published_programs
from app.services.gap_service import ALL_LABELS, analyze_gap, chapter_order
from app.services.journey_service import CATEGORY_LABELS, EXPERIENCE_CATEGORIES, build_journey
from app.services.package_service import build_package_docx, latest_review
from app.services.file_preview import inline_file
from app.services.record_status import learning_profile_state, portfolio_state
from app.services import ai_quota_service, autobiography_service, review_snapshot_service, student_rules
from app.services.gemini_client import AIUnavailable, ai_ready


student_bp = Blueprint("student", __name__)


@student_bp.post("/student/learning-profile/documents")
@role_required("student")
def learning_profile_document_upload():
    user = get_current_user()
    document_type = request.form.get("document_type", "").strip()
    uploaded = request.files.get("file")
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        return "unsupported document type", 400
    if not uploaded or not uploaded.filename:
        return "file is required", 400
    try:
        safe_name = validate_upload_filename(
            uploaded.filename,
            current_app.config["LEARNING_PROFILE_ALLOWED_EXTENSIONS"],
        )
    except ValueError as exc:
        return str(exc), 400

    file_bytes = uploaded.read()
    if not file_bytes:
        return "file is empty", 400
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / "learning-profile" / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / f"{uuid4().hex}_{safe_name}"
    stored_path.write_bytes(file_bytes)
    try:
        document = SourceDocument(
            owner_id=user.id,
            document_type=document_type,
            display_name=safe_name,
            file_path=str(stored_path),
            sha256=sha256(file_bytes).hexdigest(),
            status="uploaded",
        )
        db.session.add(document)
        db.session.flush()
        try:
            result = analyze_document(
                document_type,
                stored_path,
                current_app.config["DOCUMENT_ANALYSIS_PROVIDER"],
            )
            extraction = DocumentExtraction(
                source_document_id=document.id,
                provider=current_app.config["DOCUMENT_ANALYSIS_PROVIDER"],
                status="extracted",
                result_json=result,
            )
            document.status = "extracted"
        except RuntimeError as exc:
            extraction = DocumentExtraction(
                source_document_id=document.id,
                provider=current_app.config["DOCUMENT_ANALYSIS_PROVIDER"],
                status="failed",
                error_message=str(exc),
            )
            document.status = "analysis_failed"
        db.session.add(extraction)
        db.session.commit()
    except Exception:
        db.session.rollback()
        stored_path.unlink(missing_ok=True)
        raise
    return redirect(url_for("student.learning_profile"))


@student_bp.get("/student/learning-profile")
@role_required("student")
def learning_profile():
    user = get_current_user()
    documents = SourceDocument.query.filter_by(owner_id=user.id).filter(
        SourceDocument.document_type.in_(ALLOWED_DOCUMENT_TYPES)).order_by(SourceDocument.created_at.desc()).all()
    outputs = LearningProfileOutput.query.filter_by(student_id=user.id).order_by(LearningProfileOutput.created_at.desc()).all()
    courses = LearningCourseRecord.query.filter_by(student_id=user.id).order_by(
        LearningCourseRecord.school_year, LearningCourseRecord.id).all()
    credentials = CredentialRecord.query.filter_by(student_id=user.id).order_by(CredentialRecord.id).all()
    return render_template(
        "learning_profile.html",
        user=user,
        documents=documents,
        outputs=outputs,
        courses=courses,
        credentials=credentials,
        record_state=learning_profile_state,
    )


@student_bp.get("/student/learning-profile/upload")
@role_required("student")
def learning_profile_upload_page():
    return render_template("learning_profile_upload.html", user=get_current_user())


@student_bp.post("/student/learning-profile/generate")
@role_required("student")
def learning_profile_generate():
    try:
        school_year = int(request.form.get("school_year", ""))
        if not 1 <= school_year <= 999:
            raise ValueError
    except ValueError:
        return "school_year is required", 400
    generate_learning_profile_outputs(get_current_user(), school_year)
    return redirect(url_for("student.learning_profile"))


@student_bp.get("/student/learning-profile/outputs/<int:output_id>/docx")
@role_required("student")
def learning_profile_output_docx(output_id):
    output = db.session.get(LearningProfileOutput, output_id)
    if not output:
        abort(404)
    user = get_current_user()
    if output.student_id != user.id:
        abort(403)
    stream = output_to_docx_bytes(output, user.display_name)
    return send_file(
        stream,
        as_attachment=True,
        download_name=f"learning-profile-{output.output_type}-{output.id}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@student_bp.get("/student/learning-profile/documents/<int:document_id>/review")
@role_required("student")
def learning_profile_document_review(document_id):
    document = db.session.get(SourceDocument, document_id)
    if not document:
        abort(404)
    user = get_current_user()
    if document.owner_id != user.id:
        abort(403)
    result = (document.extraction.result_json or {}) if document.extraction else {}
    saved_courses = LearningCourseRecord.query.filter_by(student_id=user.id, source_document_id=document.id).all()
    saved_credentials = CredentialRecord.query.filter_by(student_id=user.id, source_document_id=document.id).all()
    if saved_courses or saved_credentials:
        courses = [{
            "school_year": c.school_year or "", "semester": c.semester or "", "course_name": c.course_name,
            "credits": "" if c.credits is None else c.credits, "score": "" if c.score is None else c.score,
            "status_mark": c.status_mark or "",
        } for c in saved_courses]
        credentials = [{
            "credential_name": c.credential_name, "level": c.level or "",
            "issuing_organization": c.issuing_organization or "",
            "issue_date": c.issue_date.isoformat() if c.issue_date else "",
        } for c in saved_credentials]
    else:
        courses = result.get("courses") or []
        credentials = result.get("credentials") or []
    return render_template(
        "learning_profile_review.html",
        user=user,
        document=document,
        courses=courses,
        credentials=credentials,
        warnings=result.get("warnings") or [],
    )


@student_bp.get("/student/learning-profile/documents/<int:document_id>/view")
@role_required("student")
def learning_profile_document_view(document_id):
    """確認頁旁邊顯示學生上傳的成績單或證照，方便對照。"""
    document = db.session.get(SourceDocument, document_id)
    if not document:
        abort(404)
    if document.owner_id != get_current_user().id:
        abort(403)
    return inline_file(document.file_path, document.display_name)


def _load_record_list(raw_value, field_name):
    try:
        value = json.loads(raw_value or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} 格式錯誤") from exc
    if not isinstance(value, list):
        raise ValueError(f"{field_name} 必須是清單")
    return value


def _normalise_name(value):
    return "".join(str(value or "").split())


@student_bp.post("/student/learning-profile/documents/<int:document_id>/review/confirm")
@role_required("student")
def learning_profile_document_confirm(document_id):
    document = db.session.get(SourceDocument, document_id)
    if not document:
        abort(404)
    user = get_current_user()
    if document.owner_id != user.id:
        abort(403)
    extraction = document.extraction
    if not extraction:
        return "document extraction is required", 400
    try:
        courses = _load_record_list(request.form.get("courses_json"), "courses_json")
        credentials = _load_record_list(request.form.get("credentials_json"), "credentials_json")
        db.session.query(LearningCourseRecord).filter_by(
            student_id=user.id, source_document_id=document.id
        ).delete()
        db.session.query(CredentialRecord).filter_by(
            student_id=user.id, source_document_id=document.id
        ).delete()
        for item in courses:
            if not isinstance(item, dict):
                raise ValueError("課程資料格式錯誤")
            course_name = str(item.get("course_name", "")).strip()
            normalized_name = _normalise_name(course_name)
            if not normalized_name:
                raise ValueError("課程名稱為必填")
            status_mark = str(item.get("status_mark") or "").strip() or None
            if status_mark not in {None, "抵", "免", "補"}:
                raise ValueError("課程狀態只可使用 抵、免、補")
            score = item.get("score")
            if status_mark:
                score = None
            elif score not in (None, ""):
                score = int(score)
                if not 0 <= score <= 100:
                    raise ValueError("分數必須介於 0 至 100")
            else:
                score = None
            credits = item.get("credits")
            credits = int(credits) if credits not in (None, "") else None
            course_year = int(item["school_year"]) if item.get("school_year") else None
            if student_rules.grade_block_reason(user) is None:
                student_rules.check_record_year(user, course_year)
            db.session.add(LearningCourseRecord(
                student_id=user.id,
                source_document_id=document.id,
                school_year=course_year,
                semester=str(item.get("semester") or "").strip() or None,
                course_name=course_name,
                normalized_course_name=normalized_name,
                credits=credits,
                score=score,
                status_mark=status_mark,
                confirmation_status="confirmed",
            ))
        for item in credentials:
            if not isinstance(item, dict):
                raise ValueError("證照資料格式錯誤")
            credential_name = str(item.get("credential_name", "")).strip()
            if not credential_name:
                raise ValueError("證照名稱為必填")
            issue_date = None
            raw_date = str(item.get("issue_date") or "").strip()
            if raw_date:
                try:
                    issue_date = date.fromisoformat(raw_date)
                except ValueError as exc:
                    raise ValueError("取得日期格式應為 YYYY-MM-DD") from exc
            db.session.add(CredentialRecord(
                student_id=user.id,
                source_document_id=document.id,
                credential_name=credential_name,
                issue_date=issue_date,
                level=str(item.get("level") or "").strip() or None,
                issuing_organization=str(item.get("issuing_organization") or "").strip() or None,
                category=str(item.get("category") or "").strip() or None,
                confirmation_status="confirmed",
            ))
        extraction.status = "confirmed"
        extraction.confirmed_at = datetime.now(timezone.utc)
        extraction.confirmed_by_id = user.id
        document.status = "confirmed"
        db.session.commit()
    except (TypeError, ValueError) as exc:
        db.session.rollback()
        return str(exc), 400
    return redirect(url_for("student.learning_profile"))


def _record_form_values(user):
    """讀取並檢查活動／競賽／服務學習／幹部經歷的表單；有錯時丟出 ValueError。"""
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    if not title:
        raise ValueError("請填寫名稱")
    if category not in EXPERIENCE_CATEGORIES:
        raise ValueError("請選擇類別：活動、競賽、服務學習或幹部經歷")
    try:
        raw_year = request.form.get("school_year", "").strip()
        school_year = int(raw_year) if raw_year else None
        raw_semester = request.form.get("semester", "").strip()
        semester = int(raw_semester) if raw_semester else None
    except ValueError as exc:
        raise ValueError("年級與學期請填數字") from exc
    if school_year is not None and not (1 <= school_year <= 5 or 100 <= school_year <= 200):
        raise ValueError("年級請填 1～5，或民國學年度（例如 113）")
    if semester not in (None, 1, 2):
        raise ValueError("學期只能是上學期或下學期")
    student_rules.check_record_year(user, school_year)
    return {
        "title": title,
        "category": category,
        "school_year": school_year,
        "semester": semester,
        "description": request.form.get("description", "").strip(),
    }


def _record_status():
    """表單按「儲存並確認」是 confirmed；只按「儲存」是 draft（內容改過要重新確認）。"""
    return "confirmed" if request.form.get("confirm") else "draft"


def _render_record_form(user, portfolio=None, values=None, error=None):
    """新增與編輯共用同一個表單頁（student_portfolio_form.html）。"""
    return render_template(
        "student_portfolio_form.html",
        user=user,
        portfolio=portfolio,
        values=values,
        categories=EXPERIENCE_CATEGORIES,
        category_labels=CATEGORY_LABELS,
        error=error,
    ), (400 if error else 200)


@student_bp.get("/student/portfolio")
@student_bp.post("/student/portfolio")
@role_required("student")
def portfolio_list():
    user = get_current_user()
    if request.method == "POST":
        try:
            values = _record_form_values(user)
        except ValueError as exc:
            return _render_record_form(user, values=request.form, error=str(exc))
        db.session.add(Portfolio(student_id=user.id, status=_record_status(), **values))
        db.session.commit()
        return redirect(url_for("student.portfolio_list", added=values["category"]))
    records = Portfolio.query.filter_by(student_id=user.id).order_by(Portfolio.created_at.desc()).all()
    return render_template(
        "student_portfolio.html",
        user=user,
        grouped={key: [r for r in records if r.category == key] for key in EXPERIENCE_CATEGORIES},
        legacy=[r for r in records if r.category not in EXPERIENCE_CATEGORIES],
        unconfirmed_count=sum(1 for r in records if r.status == "draft"),
        categories=EXPERIENCE_CATEGORIES,
        category_labels=CATEGORY_LABELS,
        record_state=portfolio_state,
    )


@student_bp.get("/student/portfolio/new")
@role_required("student")
def portfolio_new():
    return _render_record_form(get_current_user(), values={"category": request.args.get("category", "")})


@student_bp.get("/student/portfolio/<int:portfolio_id>/edit")
@student_bp.post("/student/portfolio/<int:portfolio_id>/edit")
@role_required("student")
def portfolio_edit(portfolio_id):
    user = get_current_user()
    portfolio = owned_portfolio(portfolio_id, user)
    if request.method == "POST":
        try:
            values = _record_form_values(user)
        except ValueError as exc:
            return _render_record_form(user, portfolio, values=request.form, error=str(exc))
        for key, value in values.items():
            setattr(portfolio, key, value)
        # 內容改過就要重新確認（舊流程 submitted 的也一樣），未確認的不會進自傳
        portfolio.status = _record_status()
        db.session.commit()
        return redirect(url_for("student.portfolio_list"))
    return _render_record_form(user, portfolio, values=portfolio)


@student_bp.post("/student/portfolio/<int:portfolio_id>/confirm")
@role_required("student")
def portfolio_confirm(portfolio_id):
    """學生確認這筆經歷內容正確；確認過的經歷才會被 AI 寫進自傳。"""
    portfolio = owned_portfolio(portfolio_id, get_current_user())
    if portfolio.status == "draft":
        portfolio.status = "confirmed"
        db.session.commit()
    return redirect(url_for("student.portfolio_list", confirmed=1))


@student_bp.post("/student/portfolio/<int:portfolio_id>/submit")
@role_required("student")
def portfolio_submit(portfolio_id):
    portfolio = owned_portfolio(portfolio_id, get_current_user())
    submission = create_submission_snapshot(portfolio, get_current_user())
    portfolio.status = "submitted"
    db.session.add(submission)
    db.session.commit()
    return redirect(url_for("student.portfolio_list"))


@student_bp.post("/student/portfolio/<int:portfolio_id>/evidence")
@role_required("student")
def evidence_upload(portfolio_id):
    portfolio = owned_portfolio(portfolio_id, get_current_user())
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return "file is required", 400
    try:
        safe_name = validate_upload_filename(uploaded.filename, current_app.config["ALLOWED_UPLOAD_EXTENSIONS"])
    except ValueError as exc:
        return str(exc), 400
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / str(get_current_user().id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / f"{uuid4().hex}_{safe_name}"
    uploaded.save(stored_path)
    db.session.add(PortfolioEvidence(portfolio_id=portfolio.id, evidence_type="file", display_name=safe_name, file_path=str(stored_path)))
    db.session.commit()
    return redirect(url_for("student.portfolio_edit", portfolio_id=portfolio.id))


def _owned_evidence_or_404(evidence_id):
    evidence = db.session.get(PortfolioEvidence, evidence_id)
    if not evidence:
        abort(404)
    owned_portfolio(evidence.portfolio_id, get_current_user())
    if not evidence.file_path or not Path(evidence.file_path).is_file():
        abort(404)
    return evidence


@student_bp.get("/student/evidence/<int:evidence_id>")
@role_required("student")
def evidence_download(evidence_id):
    evidence = _owned_evidence_or_404(evidence_id)
    return send_file(evidence.file_path, as_attachment=True, download_name=evidence.display_name)


@student_bp.get("/student/evidence/<int:evidence_id>/view")
@role_required("student")
def evidence_view(evidence_id):
    """在瀏覽器直接顯示圖片或 PDF（規則見 services/file_preview.py）。"""
    evidence = _owned_evidence_or_404(evidence_id)
    return inline_file(evidence.file_path, evidence.display_name)


@student_bp.post("/student/evidence/<int:evidence_id>/delete")
@role_required("student")
def evidence_delete(evidence_id):
    evidence = db.session.get(PortfolioEvidence, evidence_id)
    if not evidence:
        abort(404)
    portfolio = owned_portfolio(evidence.portfolio_id, get_current_user())
    file_path = evidence.file_path
    db.session.delete(evidence)
    db.session.commit()
    if file_path:
        Path(file_path).unlink(missing_ok=True)
    return redirect(url_for("student.portfolio_edit", portfolio_id=portfolio.id))


# ---------- 主線後半：目標校系、缺件比對、請導師確認、產出備審資料 ----------

def _blocked(user, reason):
    """不能使用某個功能時的說明頁（年級還沒到、或還不知道入學學年度）。"""
    back = urlparse(request.referrer).path if request.referrer else ""
    return render_template(
        "student_blocked.html", user=user, reason=reason, back=back or url_for("student.target_list"),
    ), 403


def _published_program_or_404(program_id):
    program = db.session.get(AdmissionProgram, program_id)
    if not program or program.status != "published":
        abort(404)
    return program


def _selected_target_or_404(user, program_id):
    program = _published_program_or_404(program_id)
    if not StudentTarget.query.filter_by(student_id=user.id, rule_version_id=program.id).first():
        abort(404)
    return program


@student_bp.get("/student/targets")
@student_bp.post("/student/targets")
@role_required("student")
def target_list():
    user = get_current_user()
    error = None
    if request.method == "POST":
        try:
            program = _published_program_or_404(int(request.form.get("program_id", "")))
        except ValueError:
            abort(400)
        reason = student_rules.grade_block_reason(user)
        if reason:
            return _blocked(user, reason)
        if not StudentTarget.query.filter_by(student_id=user.id, rule_version_id=program.id).first():
            slots = student_rules.target_slots(user)
            if slots["limit"] is not None and slots["used"] >= slots["limit"]:
                error = f"目標校系同時最多 {slots['limit']} 所，請先取消一所再加入新的。"
            else:
                db.session.add(StudentTarget(student_id=user.id, rule_version_id=program.id))
                db.session.commit()
        if not error:
            return redirect(url_for("student.target_gap", program_id=program.id))
    journey = build_journey(user)
    selected = {t.rule_version_id for t in StudentTarget.query.filter_by(student_id=user.id).all()}
    programs = published_programs()
    return render_template(
        "student_targets.html",
        user=user,
        programs=programs,
        selected=selected,
        slots=student_rules.target_slots(user),
        cancelled_programs=_cancelled_autobiography_programs(user),
        gaps={p.id: analyze_gap(user, p, journey) for p in programs},
        focus=focus_view(user, journey),
        error=error,
    ), (400 if error else 200)


@student_bp.post("/student/targets/<int:program_id>/remove")
@role_required("student")
def target_remove(program_id):
    user = get_current_user()
    StudentTarget.query.filter_by(student_id=user.id, rule_version_id=program_id).delete()
    db.session.commit()
    return redirect(url_for("student.target_list"))


@student_bp.get("/student/targets/<int:program_id>")
@role_required("student")
def target_gap(program_id):
    user = get_current_user()
    program = _selected_target_or_404(user, program_id)
    journey = build_journey(user)
    targets = StudentTarget.query.filter_by(student_id=user.id).order_by(StudentTarget.selected_at).all()
    return render_template(
        "student_gap.html",
        user=user,
        program=program,
        gap=analyze_gap(user, program, journey),
        chapters=chapter_order(program),
        targets=[t.program for t in targets],
        review=latest_review(user, program),
        autobiography=autobiography_service.latest_draft(user, program),
        labels=ALL_LABELS,
    )


@student_bp.post("/student/targets/<int:program_id>/review")
@role_required("student")
def target_request_review(program_id):
    user = get_current_user()
    program = _selected_target_or_404(user, program_id)
    reason = student_rules.review_block_reason(user) or student_rules.over_limit_reason(user)
    if reason:
        return _blocked(user, reason)
    review_snapshot_service.request_review(user, program)
    return redirect(url_for("student.target_gap", program_id=program.id, sent=1))


@student_bp.get("/student/targets/<int:program_id>/package.docx")
@role_required("student")
def target_package(program_id):
    user = get_current_user()
    program = _selected_target_or_404(user, program_id)
    return send_file(
        build_package_docx(user, program),
        as_attachment=True,
        download_name=f"備審資料-{program.school_name}-{program.department_name}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ---------- AI 自傳小幫手：先回答幾題，AI 再依資料與校系加權寫草稿 ----------

def _autobiography_program(user, program_id):
    """自傳要針對一個目標校系寫；沒指定就用第一個目標校系。"""
    targets = [t.program for t in StudentTarget.query.filter_by(student_id=user.id).order_by(StudentTarget.selected_at)]
    if not targets:
        return None, []
    if program_id:
        program = next((p for p in targets if p.id == program_id), None)
        if not program:
            abort(404)
        return program, targets
    return targets[0], targets


def _render_autobiography(user, program, targets, error=None, answers=None, status=503, stale=None):
    """stale：用舊頁面存檔被擋下時，顯示最新版，並把沒存到的文字列出來（不讓學生白打）。"""
    draft = autobiography_service.latest_draft(user, program) if program else None
    asking = program and (not draft or request.args.get("redo") or error) and not stale
    return render_template(
        "student_autobiography.html",
        user=user,
        program=program,
        targets=targets,
        draft=draft,
        asking=asking,
        questions=autobiography_service.QUESTIONS,
        answers=answers or (draft.content_json.get("answers", {}) if draft else {}),
        facts=autobiography_service.build_facts(user, program) if program else None,
        version=autobiography_service.version_of(draft) if draft else None,
        school_turns=ai_quota_service.remaining(user) if ai_ready() else None,
        error=error,
        stale=stale,
    ), (409 if stale else status if error else 200)


@student_bp.get("/student/autobiography")
@role_required("student")
def autobiography():
    user = get_current_user()
    program, targets = _autobiography_program(user, request.args.get("program_id", type=int))
    return _render_autobiography(user, program, targets)


@student_bp.post("/student/autobiography/generate")
@role_required("student")
def autobiography_generate():
    user = get_current_user()
    program, targets = _autobiography_program(user, request.form.get("program_id", type=int))
    if not program:
        return redirect(url_for("student.target_list"))
    reason = student_rules.review_block_reason(user)
    if reason:
        return _blocked(user, reason)
    answers = {key: request.form.get(key, "") for key, _, _ in autobiography_service.QUESTIONS}
    # 學生自己的金鑰：只放在這個函式的變數裡用一次，不存資料庫、不放 session、不放網址
    own_key = request.form.get("own_api_key", "").strip() or None
    try:
        # 學校金鑰每人每天有次數限制；先扣，AI 失敗時 rollback 就會退回
        if not own_key and ai_ready():
            ai_quota_service.consume(user)
        autobiography_service.generate_draft(user, program, answers, api_key=own_key)
    except ai_quota_service.QuotaExceeded as exc:
        return _render_autobiography(user, program, targets, error=str(exc), answers=answers, status=429)
    except AIUnavailable as exc:
        db.session.rollback()
        return _render_autobiography(user, program, targets, error=str(exc), answers=answers)
    finally:
        own_key = None
    return redirect(url_for("student.autobiography", program_id=program.id,
                            used_own_key=1 if request.form.get("own_api_key", "").strip() else None))


@student_bp.post("/student/autobiography/<int:output_id>/save")
@role_required("student")
def autobiography_save(output_id):
    user = get_current_user()
    output = db.session.get(LearningProfileOutput, output_id)
    if not output or output.output_type != autobiography_service.OUTPUT_TYPE:
        abort(404)
    if output.student_id != user.id:
        abort(403)
    count = len(output.content_json.get("paragraphs", []))
    texts = [request.form.get(f"paragraph_{i}", "") for i in range(count)]
    try:
        autobiography_service.save_edits(output, texts, user)
    except autobiography_service.StaleVersion as exc:
        program, targets = _autobiography_program(user, output.content_json["program_id"])
        return _render_autobiography(user, program, targets, stale={"message": str(exc), "texts": texts,
                                                                    "paragraphs": output.content_json["paragraphs"]})
    return redirect(url_for("student.autobiography", program_id=output.content_json["program_id"], saved=1))


@student_bp.get("/student/autobiography/versions")
@role_required("student")
def autobiography_versions():
    """自傳的所有版本：誰在什麼時候改的、和上一版差在哪裡。不能刪除。"""
    user = get_current_user()
    program_id = request.args.get("program_id", type=int)
    # 取消目標後仍可以看那個校系的自傳紀錄（唯讀，主持人 2026-10-10）
    program = next((p for p in _cancelled_autobiography_programs(user) if p.id == program_id), None)
    cancelled = program is not None
    if not program:
        program, targets = _autobiography_program(user, program_id)
    if not program:
        return redirect(url_for("student.target_list"))
    return render_template("autobiography_versions.html", user=user, program=program, cancelled=cancelled,
                           **_version_view(user, program, request.args.get("v", type=int)))


def _cancelled_autobiography_programs(user):
    """學生取消了目標、但留有自傳版本的校系。"""
    chosen = {t.rule_version_id for t in StudentTarget.query.filter_by(student_id=user.id)}
    outputs = LearningProfileOutput.query.filter_by(student_id=user.id, output_type=autobiography_service.OUTPUT_TYPE)
    ids = {o.content_json.get("program_id") for o in outputs} - chosen - {None}
    return AdmissionProgram.query.filter(AdmissionProgram.id.in_(ids)).all() if ids else []


def _version_view(student, program, selected_id):
    """版本頁共用的資料（學生和導師都會用）。"""
    versions = list(reversed(autobiography_service.versions(student, program)))
    if not versions:
        return {"versions": [], "selected": None, "diff": [], "editors": {}}
    selected = next((v for v in versions if v.id == selected_id), versions[0])
    by_id = {v.id: v for v in versions}
    previous = by_id.get(selected.content_json.get("based_on"))
    if previous is None:
        older = [v for v in versions if v.id < selected.id]
        previous = older[0] if older else None
    editor_ids = {v.content_json.get("editor_id") for v in versions} - {None}
    editors = {u.id: u for u in User.query.filter(User.id.in_(editor_ids)).all()} if editor_ids else {}
    return {
        "versions": versions,
        "selected": selected,
        "previous": previous,
        "diff": autobiography_service.version_diff(selected, previous),
        "editors": editors,
        "version_of": autobiography_service.version_of,
    }
