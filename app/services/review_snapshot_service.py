"""導師確認備審（規格 10.3、10.4）：送審時存快照，確認與撤回都寫操作紀錄。

- 學生按「請導師確認」：把當下的事實清單、自傳版本、完成度存進 PackageReview.snapshot_json。
  還在等導師時再按一次，會更新同一筆的快照；導師確認過或請學生修改後再送，會新增一筆。
- 導師確認的是那一份快照；學生之後再改資料，快照不變（舊的確認紀錄保留）。
- 確認、請學生修改、撤回確認都寫進 audit_logs，撤回要填原因；紀錄裡不放學生原文。
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models import AuditLog, PackageReview
from app.services import autobiography_service
from app.services.gap_service import analyze_gap
from app.services.package_service import latest_review


def build_snapshot(student, program):
    draft = autobiography_service.latest_draft(student, program)
    return {
        "facts": autobiography_service.build_facts(student, program)["items"],
        "autobiography": ({"output_id": draft.id, "version": autobiography_service.version_of(draft)}
                          if draft else None),
        "readiness": analyze_gap(student, program)["readiness"],
        "program": {"id": program.id, "school_name": program.school_name, "department_name": program.department_name},
        "taken_at": datetime.now(timezone.utc).isoformat(),
    }


def request_review(student, program):
    """學生送審；回傳這次的 PackageReview。"""
    snapshot = build_snapshot(student, program)
    review = latest_review(student, program)
    if not review or review.status != "pending":
        review = PackageReview(student_id=student.id, rule_version_id=program.id, status="pending")
        db.session.add(review)
    review.snapshot_json = snapshot
    review.readiness_percent = snapshot["readiness"]
    review.requested_at = datetime.now(timezone.utc)
    db.session.commit()
    return review


def snapshot_diff(new, old):
    """兩份快照的事實差異：新增了哪些、少了哪些（比較文字）。"""
    new_texts = [fact["text"] for fact in (new or {}).get("facts", [])]
    old_texts = [fact["text"] for fact in (old or {}).get("facts", [])]
    return {
        "added": [text for text in new_texts if text not in old_texts],
        "removed": [text for text in old_texts if text not in new_texts],
    }


def previous_confirmed(review):
    """同一位學生、同一個校系，在這次之前最近一次導師確認的送審。"""
    return (PackageReview.query.filter(
        PackageReview.student_id == review.student_id,
        PackageReview.rule_version_id == review.rule_version_id,
        PackageReview.status == "confirmed",
        PackageReview.id < review.id,
    ).order_by(PackageReview.id.desc()).first())


def confirmed_facts(student, program):
    """最近一次導師確認的快照事實；給 AI 與導師摘要引用。沒有確認過回傳 None。"""
    review = (PackageReview.query.filter_by(student_id=student.id, rule_version_id=program.id, status="confirmed")
              .order_by(PackageReview.id.desc()).first())
    return review.snapshot_json.get("facts", []) if review and review.snapshot_json else None


def _log(actor, action, review, **detail):
    db.session.add(AuditLog(user_id=actor.id, action=action, target_type="package_review", target_id=review.id,
                            detail_json={"student_id": review.student_id, "program_id": review.rule_version_id,
                                         "status": review.status, **detail}))


def decide(review, teacher, decision, comment):
    """導師確認（confirmed）或請學生修改（needs_revision）。"""
    review.status = decision
    review.comment = comment or None
    review.teacher_id = teacher.id
    review.reviewed_at = datetime.now(timezone.utc)
    _log(teacher, "package_review.confirm" if decision == "confirmed" else "package_review.needs_revision", review)
    db.session.commit()


def withdraw(review, teacher, reason):
    """導師按錯時撤回確認：回到等待確認，原本的確認紀錄保留在 audit_logs。"""
    if review.status != "confirmed":
        raise ValueError("這份送審還沒有被確認，不需要撤回。")
    if not reason:
        raise ValueError("撤回確認時，請寫下原因。")
    review.status = "pending"
    review.teacher_id = teacher.id
    review.reviewed_at = datetime.now(timezone.utc)
    _log(teacher, "package_review.withdraw", review, reason=reason[:500])
    db.session.commit()
