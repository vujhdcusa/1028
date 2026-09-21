from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for

from app.extensions import db
from app.models import Portfolio, PortfolioEvidence
from app.routes.main import get_current_user, role_required
from app.services.portfolio_service import owned_portfolio, create_submission_snapshot
from app.security import validate_upload_filename


student_bp = Blueprint("student", __name__)


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
