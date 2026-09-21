from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models import ProjectType, RequirementItem, RequirementTemplate, User
from app.routes.main import get_current_user, role_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin/accounts")
@role_required("admin")
def accounts():
    return render_template(
        "admin_accounts.html",
        user=get_current_user(),
        accounts=User.query.order_by(User.role.asc(), User.username.asc()).all(),
    )


@admin_bp.post("/admin/accounts/<int:user_id>/toggle-active")
@role_required("admin")
def toggle_account_active(user_id):
    actor = get_current_user()
    account = db.session.get(User, user_id)
    if not account:
        abort(404)
    if account.id == actor.id:
        abort(400, description="Administrators cannot disable their own account")
    account.is_active = not account.is_active
    db.session.commit()
    return redirect(url_for("admin.accounts"))


@admin_bp.route("/admin/project-types", methods=["GET", "POST"])
@role_required("admin")
def project_types():
    if request.method == "POST":
        code = request.form.get("code", "").strip().lower()
        name = request.form.get("name", "").strip()
        try:
            school_year = int(request.form.get("school_year", ""))
        except ValueError:
            abort(400, description="School year must be a number")
        if not code or not name or ProjectType.query.filter_by(code=code).first():
            abort(400, description="Project type code and name must be unique and complete")
        db.session.add(
            ProjectType(code=code, name=name, school_year=school_year, is_active=True)
        )
        db.session.commit()
        return redirect(url_for("admin.project_types"))
    return render_template(
        "admin_rules.html",
        user=get_current_user(),
        project_types=ProjectType.query.order_by(ProjectType.school_year.desc(), ProjectType.name.asc()).all(),
    )


@admin_bp.post("/admin/project-types/<int:project_type_id>/toggle-active")
@role_required("admin")
def toggle_project_type_active(project_type_id):
    project_type = db.session.get(ProjectType, project_type_id)
    if not project_type:
        abort(404)
    project_type.is_active = not project_type.is_active
    db.session.commit()
    return redirect(url_for("admin.project_types"))


@admin_bp.post("/admin/project-types/<int:project_type_id>/templates")
@role_required("admin")
def create_requirement_template(project_type_id):
    project_type = db.session.get(ProjectType, project_type_id)
    if not project_type:
        abort(404)
    name = request.form.get("name", "").strip()
    version = request.form.get("version", "").strip()
    if not name or not version:
        abort(400, description="Template name and version are required")
    db.session.add(
        RequirementTemplate(
            project_type_id=project_type.id,
            name=name,
            version=version,
            is_active=True,
        )
    )
    db.session.commit()
    return redirect(url_for("admin.project_types"))


@admin_bp.post("/admin/templates/<int:template_id>/toggle-active")
@role_required("admin")
def toggle_template_active(template_id):
    template = db.session.get(RequirementTemplate, template_id)
    if not template:
        abort(404)
    template.is_active = not template.is_active
    db.session.commit()
    return redirect(url_for("admin.project_types"))


@admin_bp.post("/admin/templates/<int:template_id>/items")
@role_required("admin")
def create_requirement_item(template_id):
    template = db.session.get(RequirementTemplate, template_id)
    if not template:
        abort(404)
    title = request.form.get("title", "").strip()
    if not title:
        abort(400, description="Requirement title is required")
    try:
        sort_order = int(request.form.get("sort_order", "0"))
    except ValueError:
        abort(400, description="Sort order must be a number")
    db.session.add(
        RequirementItem(
            template_id=template.id,
            title=title,
            description=request.form.get("description", "").strip() or None,
            stage=request.form.get("stage", "midterm").strip() or "midterm",
            is_required=request.form.get("is_required", "on") == "on",
            sort_order=sort_order,
        )
    )
    db.session.commit()
    return redirect(url_for("admin.project_types"))
