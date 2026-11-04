"""normalize repeating values and add duplicate guards

Revision ID: f6a2c4d9e713
Revises: e5b9d1c3a826
Create Date: 2026-11-04

這個遷移不會清除任何資料。若舊資料已存在會違反新唯一規則的重複列，會在
任何結構異動前停止，讓管理者先人工確認資料。
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a2c4d9e713"
down_revision = "e5b9d1c3a826"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name, column_name):
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_unique_constraint(inspector, table_name, constraint_name):
    return any(item.get("name") == constraint_name for item in inspector.get_unique_constraints(table_name))


def _stop_if_duplicates(bind, inspector, table_name, columns):
    """資料不合法時停止；絕不由遷移自行刪掉任何一筆。"""
    if not inspector.has_table(table_name) or not all(_has_column(inspector, table_name, column) for column in columns):
        return
    quoted_columns = ", ".join(columns)
    duplicate = bind.execute(
        sa.text(
            f"SELECT {quoted_columns}, COUNT(*) AS duplicate_count "
            f"FROM {table_name} GROUP BY {quoted_columns} HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicate:
        values = ", ".join(f"{column}={value!r}" for column, value in zip(columns, duplicate[:-1]))
        raise RuntimeError(
            f"無法套用資料正規化：{table_name} 有重複資料（{values}）。"
            "請先人工確認並合併重複資料；本遷移沒有刪除任何資料。"
        )


def _add_unique_guard(inspector, table_name, columns, constraint_name):
    if not inspector.has_table(table_name) or _has_unique_constraint(inspector, table_name, constraint_name):
        return
    # 空白 SQLite 遷移測試可能只建立了部分歷史資料表；不要讓 batch reflection
    # 嘗試載入不存在的外鍵目標。正式資料庫的相關表都存在時才會套用規則。
    if any(
        foreign_key.get("referred_table") and not inspector.has_table(foreign_key["referred_table"])
        for foreign_key in inspector.get_foreign_keys(table_name)
    ):
        return
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.create_unique_constraint(constraint_name, columns)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 先完整檢查，避免 MySQL 的 DDL 自動提交造成做一半才發現重複資料。
    _stop_if_duplicates(bind, inspector, "student_profiles", ["user_id"])
    _stop_if_duplicates(bind, inspector, "project_members", ["project_group_id", "student_id"])
    _stop_if_duplicates(bind, inspector, "portfolio_submissions", ["portfolio_id", "version_no"])

    if inspector.has_table("admission_rule_items") and not inspector.has_table("admission_requirement_categories"):
        op.create_table(
            "admission_requirement_categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("requirement_item_id", sa.Integer(), nullable=False),
            sa.Column("category_key", sa.String(length=50), nullable=False),
            sa.ForeignKeyConstraint(["requirement_item_id"], ["admission_rule_items.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("requirement_item_id", "category_key", name="uq_requirement_category"),
            sa.CheckConstraint("length(category_key) > 0", name="ck_requirement_category_not_blank"),
        )
        op.create_index(
            "ix_admission_requirement_categories_requirement_item_id",
            "admission_requirement_categories",
            ["requirement_item_id"],
        )
        if _has_column(inspector, "admission_rule_items", "mapped_categories"):
            rows = bind.execute(sa.text("SELECT id, mapped_categories FROM admission_rule_items")).mappings()
            for row in rows:
                keys = []
                for raw_key in (row["mapped_categories"] or "").split(","):
                    key = raw_key.strip()
                    if key and key not in keys:
                        keys.append(key)
                for key in keys:
                    bind.execute(
                        sa.text(
                            "INSERT INTO admission_requirement_categories (requirement_item_id, category_key) "
                            "VALUES (:requirement_item_id, :category_key)"
                        ),
                        {"requirement_item_id": row["id"], "category_key": key},
                    )
            op.drop_column("admission_rule_items", "mapped_categories")

    inspector = sa.inspect(bind)
    if inspector.has_table("transfer_credit_records") and not inspector.has_table("transfer_credit_missing_documents"):
        op.create_table(
            "transfer_credit_missing_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("transfer_credit_record_id", sa.Integer(), nullable=False),
            sa.Column("document_name", sa.String(length=255), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["transfer_credit_record_id"], ["transfer_credit_records.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("transfer_credit_record_id", "document_name", name="uq_transfer_missing_document"),
            sa.CheckConstraint("length(document_name) > 0", name="ck_transfer_missing_document_not_blank"),
            sa.CheckConstraint("sort_order >= 0", name="ck_transfer_missing_document_sort_order"),
        )
        op.create_index(
            "ix_transfer_credit_missing_documents_transfer_credit_record_id",
            "transfer_credit_missing_documents",
            ["transfer_credit_record_id"],
        )
        if _has_column(inspector, "transfer_credit_records", "missing_documents"):
            rows = bind.execute(sa.text("SELECT id, missing_documents FROM transfer_credit_records")).mappings()
            for row in rows:
                names = []
                raw_documents = (row["missing_documents"] or "").replace("\r", "").replace("、", "\n")
                for raw_name in raw_documents.split("\n"):
                    name = raw_name.strip()
                    if name and name not in names:
                        names.append(name)
                for index, name in enumerate(names):
                    bind.execute(
                        sa.text(
                            "INSERT INTO transfer_credit_missing_documents "
                            "(transfer_credit_record_id, document_name, sort_order) "
                            "VALUES (:record_id, :document_name, :sort_order)"
                        ),
                        {"record_id": row["id"], "document_name": name, "sort_order": index},
                    )
            op.drop_column("transfer_credit_records", "missing_documents")

    inspector = sa.inspect(bind)
    _add_unique_guard(inspector, "student_profiles", ["user_id"], "uq_student_profile_user")
    _add_unique_guard(inspector, "project_members", ["project_group_id", "student_id"], "uq_project_group_member")
    _add_unique_guard(inspector, "portfolio_submissions", ["portfolio_id", "version_no"], "uq_portfolio_submission_version")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name, constraint_name in (
        ("portfolio_submissions", "uq_portfolio_submission_version"),
        ("project_members", "uq_project_group_member"),
        ("student_profiles", "uq_student_profile_user"),
    ):
        if inspector.has_table(table_name) and _has_unique_constraint(inspector, table_name, constraint_name):
            with op.batch_alter_table(table_name) as batch_op:
                batch_op.drop_constraint(constraint_name, type_="unique")

    inspector = sa.inspect(bind)
    if inspector.has_table("transfer_credit_missing_documents"):
        if inspector.has_table("transfer_credit_records") and not _has_column(inspector, "transfer_credit_records", "missing_documents"):
            op.add_column(
                "transfer_credit_records",
                sa.Column("missing_documents", sa.String(length=1000), nullable=False, server_default=""),
            )
            rows = bind.execute(
                sa.text(
                    "SELECT transfer_credit_record_id, document_name FROM transfer_credit_missing_documents "
                    "ORDER BY transfer_credit_record_id, sort_order, id"
                )
            ).mappings()
            grouped = {}
            for row in rows:
                grouped.setdefault(row["transfer_credit_record_id"], []).append(row["document_name"])
            for record_id, names in grouped.items():
                bind.execute(
                    sa.text("UPDATE transfer_credit_records SET missing_documents = :value WHERE id = :record_id"),
                    {"record_id": record_id, "value": "\n".join(names)},
                )
        op.drop_index(
            "ix_transfer_credit_missing_documents_transfer_credit_record_id",
            table_name="transfer_credit_missing_documents",
        )
        op.drop_table("transfer_credit_missing_documents")

    inspector = sa.inspect(bind)
    if inspector.has_table("admission_requirement_categories"):
        if inspector.has_table("admission_rule_items") and not _has_column(inspector, "admission_rule_items", "mapped_categories"):
            op.add_column(
                "admission_rule_items",
                sa.Column("mapped_categories", sa.String(length=200), nullable=False, server_default=""),
            )
            rows = bind.execute(
                sa.text(
                    "SELECT requirement_item_id, category_key FROM admission_requirement_categories "
                    "ORDER BY requirement_item_id, id"
                )
            ).mappings()
            grouped = {}
            for row in rows:
                grouped.setdefault(row["requirement_item_id"], []).append(row["category_key"])
            for item_id, keys in grouped.items():
                bind.execute(
                    sa.text("UPDATE admission_rule_items SET mapped_categories = :value WHERE id = :item_id"),
                    {"item_id": item_id, "value": ",".join(keys)},
                )
        op.drop_index(
            "ix_admission_requirement_categories_requirement_item_id",
            table_name="admission_requirement_categories",
        )
        op.drop_table("admission_requirement_categories")
