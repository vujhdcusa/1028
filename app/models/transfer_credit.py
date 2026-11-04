from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


MAX_MISSING_DOCUMENTS = 20
MAX_MISSING_DOCUMENT_NAME_LENGTH = 255


def normalize_missing_document_names(value, *, reject_duplicates=False):
    """將使用者輸入轉成安全、可儲存的一份文件一列格式。"""
    text = str(value or "")
    if len(text) > 1000:
        raise ValueError("待補資料總長度不可超過 1000 個字元。")
    if "\x00" in text or any(ord(char) < 32 and char not in "\r\n\t" for char in text):
        raise ValueError("待補資料不可包含特殊控制字元。")

    names = []
    seen = set()
    for raw_name in text.replace("\r", "").replace("、", "\n").split("\n"):
        name = raw_name.strip()
        if not name:
            continue
        if len(name) > MAX_MISSING_DOCUMENT_NAME_LENGTH:
            raise ValueError(f"每一份待補資料不可超過 {MAX_MISSING_DOCUMENT_NAME_LENGTH} 個字元。")
        if name in seen:
            if reject_duplicates:
                raise ValueError("待補資料不可重複，請保留一份即可。")
            continue
        names.append(name)
        seen.add(name)
    if len(names) > MAX_MISSING_DOCUMENTS:
        raise ValueError(f"一次最多可列出 {MAX_MISSING_DOCUMENTS} 份待補資料。")
    return names


class TransferCreditRecord(db.Model):
    """轉學生自行維護的抵免進度；不代表學校正式審核結果。"""

    __tablename__ = "transfer_credit_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="not_started")
    submitted_on = db.Column(db.Date, nullable=True)
    note = db.Column(db.String(2000), nullable=False, default="")
    teacher_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    teacher_confirmed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    student = db.relationship("User", foreign_keys=[student_id])
    teacher = db.relationship("User", foreign_keys=[teacher_id])
    missing_document_items = db.relationship(
        "TransferCreditMissingDocument",
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="TransferCreditMissingDocument.sort_order",
    )

    @property
    def missing_documents(self):
        """供既有文字欄位使用；實際資料一項一列保存。"""
        return "\n".join(item.document_name for item in self.missing_document_items)

    @missing_documents.setter
    def missing_documents(self, value):
        names = normalize_missing_document_names(value)
        self.missing_document_items = [
            TransferCreditMissingDocument(document_name=name, sort_order=index)
            for index, name in enumerate(names)
        ]


class TransferCreditMissingDocument(db.Model):
    """抵免申請尚待補交的一份文件。"""

    __tablename__ = "transfer_credit_missing_documents"
    __table_args__ = (
        db.UniqueConstraint("transfer_credit_record_id", "document_name", name="uq_transfer_missing_document"),
        db.CheckConstraint("length(document_name) > 0", name="ck_transfer_missing_document_not_blank"),
        db.CheckConstraint("sort_order >= 0", name="ck_transfer_missing_document_sort_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    transfer_credit_record_id = db.Column(
        db.Integer,
        db.ForeignKey("transfer_credit_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_name = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    record = db.relationship("TransferCreditRecord", back_populates="missing_document_items")
