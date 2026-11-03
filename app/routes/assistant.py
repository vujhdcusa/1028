"""資管科小助手的對話介面（右下角聊天視窗呼叫這裡）。"""

import json

from flask import Blueprint, jsonify, request

from app.routes.main import get_current_user, role_required
from app.services.assistant_agent_service import decide_plan, plan_history
from app.services.assistant_service import ask

assistant_bp = Blueprint("assistant", __name__)


@assistant_bp.post("/assistant/ask")
@role_required("student", "teacher")
def assistant_ask():
    try:
        history = json.loads(request.form.get("history") or "[]")
    except ValueError:
        history = []
    if not isinstance(history, list):
        history = []
    result = ask(get_current_user(), request.form.get("message", ""), history=history,
                 page=request.form.get("page", ""))
    return jsonify(result)


@assistant_bp.post("/assistant/plans/<int:plan_id>/<decision>")
@role_required("student")
def assistant_plan_decide(plan_id, decision):
    result = decide_plan(get_current_user(), plan_id, decision)
    if not result:
        return jsonify({"error": "找不到這份 Agent 計畫。"}), 404
    return jsonify(result)


@assistant_bp.get("/assistant/plans")
@role_required("student")
def assistant_plan_history():
    return jsonify({"plans": plan_history(get_current_user())})
