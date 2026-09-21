from flask import Blueprint, render_template

from app.models import SubmissionAssignment
from app.routes.main import get_current_user, role_required


review_bp = Blueprint("review", __name__)


@review_bp.get("/teacher/reviews")
@role_required("teacher")
def teacher_reviews():
    user = get_current_user()
    return render_template("review_queue.html", assignments=SubmissionAssignment.query.filter_by(teacher_id=user.id).all())
