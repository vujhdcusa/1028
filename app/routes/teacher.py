"""導師：查看本班學生資料，確認備審內容或留下修改建議。"""

from datetime import datetime, timezone

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models import PackageReview, Portfolio, PortfolioEvidence, SourceDocument, StudentTarget, User
from app.routes.main import get_current_user, role_required
from app.services.gap_service import ALL_LABELS, analyze_gap
from app.services.journey_service import CATEGORY_KEYS, CATEGORY_LABELS, build_journey
from app.services.package_service import latest_review
from app.services.autobiography_service import latest_draft
from app.services.file_preview import inline_file
from app.services.teacher_scope import can_view_student

teacher_bp = Blueprint("teacher", __name__)


@teacher_bp.get("/teacher/students/<int:student_id>")
@role_required("teacher")
def student_detail(student_id):
    teacher = get_current_user()
    student = db.session.get(User, student_id)
    if not student or not can_view_student(teacher, student):
        abort(403)
    journey = build_journey(student)
    targets = []
    for target in StudentTarget.query.filter_by(student_id=student.id).order_by(StudentTarget.selected_at).all():
        targets.append({
            "program": target.program,
            "gap": analyze_gap(student, target.program, journey),
            "review": latest_review(student, target.program),
            "autobiography": latest_draft(student, target.program),
        })
    return render_template(
        "teacher_student.html",
        user=teacher,
        student=student,
        journey=journey,
        targets=targets,
        documents=SourceDocument.query.filter_by(owner_id=student.id, status="confirmed")
                                      .order_by(SourceDocument.created_at).all(),
        records_with_evidence=[r for r in Portfolio.query.filter_by(student_id=student.id).order_by(Portfolio.id).all()
                               if r.evidence_items],
        category_keys=CATEGORY_KEYS,
        category_labels=CATEGORY_LABELS,
        labels=ALL_LABELS,
        error=request.args.get("error"),
    )


@teacher_bp.get("/teacher/evidence/<int:evidence_id>/view")
@role_required("teacher")
def evidence_view(evidence_id):
    """導師看本班學生的佐證照片；不是自己班的學生就 403。"""
    evidence = db.session.get(PortfolioEvidence, evidence_id)
    if not evidence:
        abort(404)
    if not can_view_student(get_current_user(), evidence.portfolio.student):
        abort(403)
    return inline_file(evidence.file_path, evidence.display_name)


@teacher_bp.get("/teacher/documents/<int:document_id>/view")
@role_required("teacher")
def document_view(document_id):
    """導師看本班學生上傳的成績單、證照原始檔（只限學生已確認的）。"""
    document = db.session.get(SourceDocument, document_id)
    if not document or document.status != "confirmed":
        abort(404)
    if not can_view_student(get_current_user(), document.owner):
        abort(403)
    return inline_file(document.file_path, document.display_name)


@teacher_bp.post("/teacher/package-reviews/<int:review_id>")
@role_required("teacher")
def decide_review(review_id):
    teacher = get_current_user()
    review = db.session.get(PackageReview, review_id)
    if not review:
        abort(404)
    if not can_view_student(teacher, review.student):
        abort(403)
    decision = request.form.get("decision", "")
    comment = request.form.get("comment", "").strip()
    if decision not in {"confirmed", "needs_revision"}:
        abort(400, description="請選擇「確認」或「需要修改」")
    if decision == "needs_revision" and not comment:
        abort(400, description="需要修改時，請寫下給學生的建議")
    review.status = decision
    review.comment = comment or None
    review.teacher_id = teacher.id
    review.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    return redirect(url_for("teacher.student_detail", student_id=review.student_id))
