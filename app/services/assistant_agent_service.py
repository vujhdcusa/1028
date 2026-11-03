"""學生對話 Agent 的安全導引與同意式計畫。

AI 可以閱讀資料、提出下一步；但建立可追蹤的規劃紀錄前，必須由學生按下同意。
站內連結完全由伺服器產生，模型不會提供任意 URL。
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models import AgentTask, SourceDocument, StudentTarget
from app.services.gap_service import analyze_gap
from app.services.journey_service import CATEGORY_LABELS, build_journey


PLAN_WORDS = ("規劃", "計畫", "待辦", "下一步", "幫我安排", "重新分析", "更新準備度")


SAFE_PATHS = {
    "grades": "/student/learning-profile",
    "credentials": "/student/learning-profile/credentials",
    "activities": "/student/portfolio",
    "targets": "/student/targets",
    "autobiography": "/student/autobiography",
    "schedule": "/student/schedule",
}


def _link(label, path_name):
    """只使用白名單內的站內路徑，服務在背景執行時也能安全回傳連結。"""
    return {"label": label, "url": SAFE_PATHS[path_name]}


def navigation_links(user, message):
    """依學生的問題回傳最多兩個安全的站內導引連結。"""
    if user.role != "student":
        return []
    text = (message or "").lower()
    links = []
    if any(word in text for word in ("ocr", "辨識", "核對", "成績單", "成績", "上傳")):
        links.append(_link("前往成績單與 OCR 核對", "grades"))
    if any(word in text for word in ("證照", "證書", "檢定")):
        links.append(_link("前往證照資料", "credentials"))
    if any(word in text for word in ("活動", "競賽", "服務", "幹部", "經歷")):
        links.append(_link("前往活動與經歷", "activities"))
    if any(word in text for word in ("校系", "志願", "準備度", "缺什麼", "缺件", "二技")):
        links.append(_link("前往目標校系", "targets"))
    if any(word in text for word in ("自傳", "備審", "書審")):
        links.append(_link("前往備審資料與自傳", "autobiography"))
    if any(word in text for word in ("報名", "時程", "日期")):
        links.append(_link("查看招生時程", "schedule"))
    unique = []
    for link in links:
        if link not in unique:
            unique.append(link)
    return unique[:2]


def _plan_payload(task):
    # JSON 欄位不可原地修改；建立新 dict 才能讓 SQLAlchemy 確實寫入待辦與執行結果。
    payload = dict(task.result_json or {})
    return {
        "id": task.id,
        "title": payload.get("title", "整理我的學習歷程計畫"),
        "reason": payload.get("reason", ""),
        "steps": payload.get("steps", []),
        "status": task.status,
        "action_url": f"/assistant/plans/{task.id}/approve",
        "reject_url": f"/assistant/plans/{task.id}/reject",
    }


def _todo(title, note, path_name):
    """待辦只連到站內白名單頁面，不能由模型或資料庫任意指定網址。"""
    return {"title": title, "note": note, "url": SAFE_PATHS[path_name]}


def _unconfirmed_document_count(user):
    return SourceDocument.query.filter(
        SourceDocument.owner_id == user.id, SourceDocument.status != "confirmed"
    ).count()


def _build_todos(user, journey, targets, unconfirmed):
    """根據已確認資料建立學生自己可追蹤的下一步，不改動任何學習歷程。"""
    todos = []
    if unconfirmed:
        todos.append(_todo("核對 OCR 資料", f"還有 {unconfirmed} 份上傳資料尚未確認；確認前不會納入分析。", "grades"))

    if not targets:
        todos.append(_todo("選擇目標校系", "先選擇想申請的校系，Agent 才能依實際加權整理缺件。", "targets"))
    else:
        missing = set()
        for target in targets:
            gap = analyze_gap(user, target.program, journey)
            missing.update(gap["missing_keys"])
        target_label = "、".join(CATEGORY_LABELS[key] for key in sorted(missing)[:3])
        if target_label:
            todos.append(_todo("補強目標校系缺件", f"已依目標校系加權整理，優先補強：{target_label}。", "targets"))

    if journey["totals"]["grades"] == 0:
        todos.append(_todo("補上成績資料", "上傳成績單後，請逐筆核對 OCR 結果。", "grades"))
    if journey["totals"]["credential"] == 0:
        todos.append(_todo("整理證照資料", "新增或確認已取得的證照，讓準備度分析更完整。", "credentials"))
    if not any(journey["totals"][key] for key in ("activity", "competition", "service", "leadership")):
        todos.append(_todo("補充活動與經歷", "填入已確認的活動、競賽、服務或幹部經歷。", "activities"))
    if targets:
        todos.append(_todo("檢查備審與自傳", "依目標校系加權檢查缺件與自傳佐證。", "autobiography"))
    return todos[:5]


def plan_history(user, limit=8):
    """學生只讀取自己的 Agent 計畫紀錄；不回傳對話內容。"""
    rows = (AgentTask.query.filter_by(task_type="assistant_plan", requester_id=user.id)
            .order_by(AgentTask.created_at.desc()).limit(limit).all())
    entries = []
    for task in rows:
        payload = task.result_json or {}
        entries.append({
            "id": task.id,
            "title": payload.get("title", "整理我的下一步計畫"),
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else "",
            "executed_at": payload.get("executed_at", ""),
            "todos": payload.get("todos", []) if task.status == "succeeded" else [],
        })
    return entries


def propose_plan(user, message):
    """只提出可控計畫；同一位學生先前尚未決定的計畫不重複建立。"""
    if user.role != "student" or not any(word in (message or "") for word in PLAN_WORDS):
        return None
    pending = (AgentTask.query.filter_by(task_type="assistant_plan", requester_id=user.id, status="pending")
               .order_by(AgentTask.id.desc()).first())
    if pending:
        return _plan_payload(pending)

    unconfirmed = _unconfirmed_document_count(user)
    target_count = StudentTarget.query.filter_by(student_id=user.id).count()
    steps = ["讀取你的已確認成績、證照與學習歷程資料"]
    if unconfirmed:
        steps.append(f"保留 {unconfirmed} 份尚未確認的 OCR 資料，不納入分析")
    if target_count:
        steps.append("依已選目標校系重新整理準備度與缺件")
    else:
        steps.append("確認你尚未選目標校系，提供選校系導引")
    steps.append("建立這次可回看的 Agent 建議與下一步連結")
    task = AgentTask(
        task_type="assistant_plan", requester_id=user.id, target_type="student", target_id=user.id,
        status="pending", result_json={
            "title": "整理我的下一步計畫",
            "reason": "我會讀取已確認的個人資料、重新整理準備度與缺件；不會新增、修改或刪除你的學習歷程資料。",
            "steps": steps,
        },
    )
    db.session.add(task)
    db.session.commit()
    return _plan_payload(task)


def decide_plan(user, plan_id, decision):
    task = db.session.get(AgentTask, plan_id)
    if not task or task.task_type != "assistant_plan" or task.requester_id != user.id:
        return None
    if task.status != "pending":
        return {"status": task.status, "message": "這份計畫已經處理過了。", "links": []}
    if decision == "reject":
        task.status = "cancelled"
        task.finished_at = datetime.now(timezone.utc)
        db.session.commit()
        return {"status": "cancelled", "message": "好的，這份 Agent 計畫沒有執行。", "links": []}
    if decision != "approve":
        return None

    journey = build_journey(user)
    targets = StudentTarget.query.filter_by(student_id=user.id).order_by(StudentTarget.selected_at).all()
    todos = _build_todos(user, journey, targets, _unconfirmed_document_count(user))
    if targets:
        readiness = [analyze_gap(user, target.program, journey)["readiness"] for target in targets]
        summary = f"已依 {len(targets)} 所目標校系與已確認資料完成本次準備度整理。"
        result = {"target_count": len(targets), "readiness": readiness}
        links = navigation_links(user, "校系 缺件")
    else:
        summary = "已完成資料盤點；你還沒有選目標校系，選定後我才能做個人化準備度分析。"
        result = {"target_count": 0, "readiness": []}
        links = [_link("前往選擇目標校系", "targets")]
    # JSON 欄位不可原地修改；建立新 dict 才能讓 SQLAlchemy 確實寫入待辦與執行結果。
    payload = dict(task.result_json or {})
    payload.update({
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
        "todos": todos,
    })
    task.result_json = payload
    task.status = "succeeded"
    task.finished_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"status": "succeeded", "message": summary, "links": links, "todos": todos}
