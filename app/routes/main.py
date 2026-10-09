from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import AwardCertificate, PortfolioSubmission, SourceDocument, StudentTarget, SubmissionAssignment, TeacherReviewFeedback, User
from app.services.gap_service import analyze_gap
from app.services.package_service import latest_review
from app.services.teacher_scope import advised_classes, students_for_teacher
from app.content.five_year_plan import FIVE_YEAR_PLAN, NEXT_STOPS
from app.services.admission_sample import load_sample_programs
from app.services.journey_service import CATEGORY_KEYS, CATEGORY_LABELS, EXPERIENCE_CATEGORIES, build_journey

main_bp = Blueprint("main", __name__)


def get_current_user():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        return None
    return user


def feedback_by_submission(submission_ids):
    feedback_map = {}
    if not submission_ids:
        return feedback_map
    feedback_items = (
        TeacherReviewFeedback.query.filter(TeacherReviewFeedback.submission_id.in_(submission_ids))
        .order_by(TeacherReviewFeedback.created_at.asc())
        .all()
    )
    for feedback in feedback_items:
        feedback_map.setdefault(feedback.submission_id, []).append(feedback)
    return feedback_map


@main_bp.route("/")
def index():
    return render_template(
        "index.html",
        plan=FIVE_YEAR_PLAN,
        next_stops=NEXT_STOPS,
        sample_programs=load_sample_programs(),
    )


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = User.query.filter_by(username=username).first()
    if not user or not user.is_active or not user.check_password(password):
        return render_template("login.html", error="帳號或密碼錯誤"), 401

    session.clear()
    session["user_id"] = user.id
    destinations = {
        "student": "main.student_dashboard",
        "teacher": "main.teacher_dashboard",
        "staff": "main.staff_dashboard",
        "admin": "main.admin_dashboard",
    }
    endpoint = destinations.get(user.role)
    if not endpoint:
        session.clear()
        return render_template("login.html", error="此帳號尚未設定可用角色"), 403
    return redirect(url_for(endpoint))


@main_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                abort(401)
            if user.role not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


@main_bp.get("/student/dashboard")
@role_required("student")
def student_dashboard():
    user = get_current_user()
    journey = build_journey(user)
    targets = [
        {"program": target.program, "readiness": analyze_gap(user, target.program, journey)["readiness"]}
        for target in StudentTarget.query.filter_by(student_id=user.id).order_by(StudentTarget.selected_at).all()
    ]
    return render_template(
        "student_home.html",
        user=user,
        journey=journey,
        targets=targets,
        category_keys=CATEGORY_KEYS,
        category_labels=CATEGORY_LABELS,
        experience_categories=EXPERIENCE_CATEGORIES,
        source_documents=SourceDocument.query.filter_by(owner_id=user.id).all(),
    )


@main_bp.get("/teacher/dashboard")
@role_required("teacher")
def teacher_dashboard():
    user = get_current_user()
    assignments = (
        SubmissionAssignment.query.filter_by(teacher_id=user.id)
        .order_by(SubmissionAssignment.assigned_at.desc())
        .all()
    )
    students = students_for_teacher(user)
    rows = []
    for student in students:
        journey = build_journey(student)
        targets = StudentTarget.query.filter_by(student_id=student.id).all()
        reviews = [latest_review(student, target.program) for target in targets]
        rows.append({
            "student": student,
            "totals": journey["totals"],
            "missing": len(journey["missing_categories"]),
            "targets": [target.program for target in targets],
            "pending": sum(1 for review in reviews if review and review.status == "pending"),
        })
    return render_template(
        "dashboard.html",
        title="教師工作台",
        user=user,
        teacher_assignments=assignments,
        classes=advised_classes(user),
        class_rows=rows,
        category_keys=CATEGORY_KEYS,
        category_labels=CATEGORY_LABELS,
    )


@main_bp.get("/staff/dashboard")
@role_required("staff")
def staff_dashboard():
    user = get_current_user()
    pending_submissions = (
        PortfolioSubmission.query.filter_by(status="submitted")
        .order_by(PortfolioSubmission.created_at.desc())
        .all()
    )
    return render_template(
        "dashboard.html",
        title="科辦／行政工作台",
        user=user,
        staff_pending_submissions=pending_submissions,
        staff_pending_certificates=AwardCertificate.query.filter_by(status="pending").count(),
        staff_feedback_by_submission=feedback_by_submission(
            [item.id for item in pending_submissions]
        ),
    )


@main_bp.get("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    user = db.session.get(User, session["user_id"])
    return render_template(
        "admin_dashboard.html",
        user=user,
        student_count=User.query.filter_by(role="student", is_active=True).count(),
        teacher_count=User.query.filter_by(role="teacher", is_active=True).count(),
        staff_count=User.query.filter_by(role="staff", is_active=True).count(),
        submission_count=PortfolioSubmission.query.count(),
        pending_submission_count=PortfolioSubmission.query.filter_by(status="submitted").count(),
        recent_submissions=(
            PortfolioSubmission.query.order_by(PortfolioSubmission.created_at.desc())
            .limit(6)
            .all()
        ),
    )


@main_bp.get("/admin")
def admin_legacy_route():
    return redirect(url_for("main.admin_dashboard"))


@main_bp.get("/dashboard/<role>")
@role_required("student", "teacher", "staff", "admin")
def role_dashboard(role):
    user = db.session.get(User, session["user_id"])
    if role != user.role:
        abort(403)
    destinations = {
        "student": "main.student_dashboard",
        "teacher": "main.teacher_dashboard",
        "staff": "main.staff_dashboard",
        "admin": "main.admin_dashboard",
    }
    endpoint = destinations.get(role)
    if not endpoint:
        abort(403)
    return redirect(url_for(endpoint))


@main_bp.app_context_processor
def inject_student_progress():
    """學生的每一頁都要顯示主線步驟列與「下一步」。"""
    user = get_current_user()
    if user and user.role == "student":
        from app.services.student_progress import student_progress
        return {"student_progress": student_progress(user)}
    return {}
