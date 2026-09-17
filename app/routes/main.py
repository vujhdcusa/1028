from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import User

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


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
        "reviewer": "main.teacher_dashboard",
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
            user_id = session.get("user_id")
            user = db.session.get(User, user_id) if user_id else None
            if not user or not user.is_active:
                abort(401)
            if user.role not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


@main_bp.get("/student/dashboard")
@role_required("student")
def student_dashboard():
    return render_template("dashboard.html", title="學生首頁", user=db.session.get(User, session["user_id"]))


@main_bp.get("/teacher/dashboard")
@role_required("teacher", "reviewer")
def teacher_dashboard():
    return render_template("dashboard.html", title="教師工作台", user=db.session.get(User, session["user_id"]))


@main_bp.get("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", user=db.session.get(User, session["user_id"]))


@main_bp.get("/admin")
def admin_legacy_route():
    return redirect(url_for("main.admin_dashboard"))


@main_bp.get("/dashboard/<role>")
@role_required("student", "teacher", "reviewer", "staff", "admin")
def role_dashboard(role):
    user = db.session.get(User, session["user_id"])
    if role != user.role:
        abort(403)
    destinations = {
        "student": "main.student_dashboard",
        "teacher": "main.teacher_dashboard",
        "reviewer": "main.teacher_dashboard",
        "admin": "main.admin_dashboard",
    }
    endpoint = destinations.get(role)
    if not endpoint:
        abort(403)
    return redirect(url_for(endpoint))
