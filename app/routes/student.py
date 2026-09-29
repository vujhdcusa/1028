from pathlib import Path
from hashlib import sha256
import json
from datetime import datetime, timezone
from uuid import uuid4

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for

from app.extensions import db
from app.models import (
    CredentialRecord,
    DocumentExtraction,
    LearningCourseRecord,
    LearningProfileOutput,
    Portfolio,
    PortfolioEvidence,
    SourceDocument,
)
from app.routes.main import get_current_user, role_required
from app.services.portfolio_service import owned_portfolio, create_submission_snapshot
from app.security import validate_upload_filename
from app.services.document_analysis_service import ALLOWED_DOCUMENT_TYPES, analyze_document
from app.services.learning_profile_docx_service import output_to_docx_bytes
from app.services.learning_profile_service import generate_learning_profile_outputs


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
    documents = SourceDocument.query.filter_by(owner_id=get_current_user().id).order_by(SourceDocument.created_at.desc()).all()
    outputs = LearningProfileOutput.query.filter_by(student_id=get_current_user().id).order_by(LearningProfileOutput.created_at.desc()).all()
    return render_template("learning_profile.html", documents=documents, outputs=outputs)


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
    if document.owner_id != get_current_user().id:
        abort(403)
    return render_template("learning_profile_review.html", document=document)


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
            db.session.add(CredentialRecord(
                student_id=user.id,
                source_document_id=document.id,
                credential_name=credential_name,
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


@student_bp.get("/student/portfolio")
@student_bp.post("/student/portfolio")
@role_required("student")
def portfolio_list():
    user = get_current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        if not title or not category:
            return render_template("student_portfolio.html", portfolios=Portfolio.query.filter_by(student_id=user.id).all(), error="標題與類型為必填"), 400
        portfolio = Portfolio(student_id=user.id, title=title, category=category, description=request.form.get("description", "").strip())
        db.session.add(portfolio)
        db.session.commit()
        return redirect(url_for("student.portfolio_list"))
    return render_template("student_portfolio.html", portfolios=Portfolio.query.filter_by(student_id=user.id).all())


@student_bp.get("/student/portfolio/<int:portfolio_id>/edit")
@student_bp.post("/student/portfolio/<int:portfolio_id>/edit")
@role_required("student")
def portfolio_edit(portfolio_id):
    portfolio = owned_portfolio(portfolio_id, get_current_user())
    if request.method == "POST":
        portfolio.title = request.form.get("title", "").strip()
        portfolio.category = request.form.get("category", "").strip()
        portfolio.description = request.form.get("description", "").strip()
        db.session.commit()
        return redirect(url_for("student.portfolio_list"))
    return render_template("student_portfolio_form.html", portfolio=portfolio)


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
    return redirect(url_for("student.portfolio_list"))


@student_bp.get("/student/evidence/<int:evidence_id>")
@role_required("student")
def evidence_download(evidence_id):
    evidence = db.session.get(PortfolioEvidence, evidence_id)
    if not evidence:
        abort(404)
    owned_portfolio(evidence.portfolio_id, get_current_user())
    if not evidence.file_path or not Path(evidence.file_path).is_file():
        abort(404)
    return send_file(evidence.file_path, as_attachment=True, download_name=evidence.display_name)
