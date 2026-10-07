from pathlib import Path
from hashlib import sha256
import json
from datetime import date, datetime, timezone
from uuid import uuid4

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for

from app.extensions import db
from app.models import (
    AdmissionProgram,
    CredentialRecord,
    DocumentExtraction,
    LearningCourseRecord,
    LearningProfileOutput,
    PackageReview,
    Portfolio,
    PortfolioEvidence,
    SourceDocument,
    StudentTarget,
)
from app.routes.main import get_current_user, role_required
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
from app.services import autobiography_service
from app.services.gemini_client import AIUnavailable


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
    documents = SourceDocument.query.filter_by(owner_id=user.id).order_by(SourceDocument.created_at.desc()).all()
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
            db.session.add(LearningCourseRecord(
                student_id=user.id,
                source_document_id=document.id,
                school_year=int(item["school_year"]) if item.get("school_year") else None,
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


def _record_form_values():
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
    return {
        "title": title,
        "category": category,
        "school_year": school_year,
        "semester": semester,
        "description": request.form.get("description", "").strip(),
    }


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
            values = _record_form_values()
        except ValueError as exc:
            return _render_record_form(user, values=request.form, error=str(exc))
        db.session.add(Portfolio(student_id=user.id, **values))
        db.session.commit()
        return redirect(url_for("student.portfolio_list", added=values["category"]))
    records = Portfolio.query.filter_by(student_id=user.id).order_by(Portfolio.created_at.desc()).all()
    return render_template(
        "student_portfolio.html",
        user=user,
        grouped={key: [r for r in records if r.category == key] for key in EXPERIENCE_CATEGORIES},
        legacy=[r for r in records if r.category not in EXPERIENCE_CATEGORIES],
        categories=EXPERIENCE_CATEGORIES,
        category_labels=CATEGORY_LABELS,
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
            values = _record_form_values()
        except ValueError as exc:
            return _render_record_form(user, portfolio, values=request.form, error=str(exc))
        for key, value in values.items():
            setattr(portfolio, key, value)
        db.session.commit()
        return redirect(url_for("student.portfolio_list"))
    return _render_record_form(user, portfolio, values=portfolio)


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
    if request.method == "POST":
        try:
            program = _published_program_or_404(int(request.form.get("program_id", "")))
        except ValueError:
            abort(400)
        if not StudentTarget.query.filter_by(student_id=user.id, rule_version_id=program.id).first():
            db.session.add(StudentTarget(student_id=user.id, rule_version_id=program.id))
            db.session.commit()
        return redirect(url_for("student.target_gap", program_id=program.id))
    journey = build_journey(user)
    selected = {t.rule_version_id for t in StudentTarget.query.filter_by(student_id=user.id).all()}
    programs = published_programs()
    return render_template(
        "student_targets.html",
        user=user,
        programs=programs,
        selected=selected,
        gaps={p.id: analyze_gap(user, p, journey) for p in programs},
    )


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
    review = latest_review(user, program)
    if not review or review.status != "pending":
        db.session.add(PackageReview(
            student_id=user.id,
            rule_version_id=program.id,
            status="pending",
            readiness_percent=analyze_gap(user, program)["readiness"],
        ))
        db.session.commit()
    return redirect(url_for("student.target_gap", program_id=program.id))


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


def _render_autobiography(user, program, targets, error=None, answers=None):
    draft = autobiography_service.latest_draft(user, program) if program else None
    asking = program and (not draft or request.args.get("redo") or error)
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
        error=error,
    ), (503 if error else 200)


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
    answers = {key: request.form.get(key, "") for key, _, _ in autobiography_service.QUESTIONS}
    # 學生自己的金鑰：只放在這個函式的變數裡用一次，不存資料庫、不放 session、不放網址
    own_key = request.form.get("own_api_key", "").strip() or None
    try:
        autobiography_service.generate_draft(user, program, answers, api_key=own_key)
    except AIUnavailable as exc:
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
    autobiography_service.save_edits(output, [request.form.get(f"paragraph_{i}", "") for i in range(count)])
    return redirect(url_for("student.autobiography", program_id=output.content_json["program_id"], saved=1))
