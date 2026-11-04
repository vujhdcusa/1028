"""資料正規化：重複值必須是一項一列，不可藏在逗號或一大段文字中。"""

from sqlalchemy import inspect

from app import create_app
from app.extensions import db
from app.models import AdmissionProgram, AdmissionRequirementItem, TransferCreditRecord, User


def test_repeating_values_are_stored_in_child_tables(tmp_path):
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'normalized.db'}",
            "TESTING": True,
        }
    )
    with app.app_context():
        db.create_all()

        program = AdmissionProgram(
            program_code="NORM-001",
            admission_year=116,
            school_name="測試學校",
            department_name="測試科系",
        )
        student = User(username="normalization-student", password_hash="test", display_name="測試學生")
        requirement = AdmissionRequirementItem(
            source_item_name="證照與競賽",
            weight_percent=30,
            mapped_categories="credential, competition,credential",
        )
        program.items.append(requirement)
        credit_record = TransferCreditRecord(student=student)
        credit_record.missing_documents = "歷年成績單\n修課證明\n歷年成績單"
        db.session.add_all([program, student, credit_record])
        db.session.commit()

        assert requirement.category_keys == ["credential", "competition"]
        assert requirement.mapped_categories == "credential,competition"
        assert credit_record.missing_documents == "歷年成績單\n修課證明"
        assert [item.document_name for item in credit_record.missing_document_items] == ["歷年成績單", "修課證明"]

        inspector = inspect(db.engine)
        assert "mapped_categories" not in {column["name"] for column in inspector.get_columns("admission_rule_items")}
        assert "missing_documents" not in {column["name"] for column in inspector.get_columns("transfer_credit_records")}
        assert inspector.has_table("admission_requirement_categories")
        assert inspector.has_table("transfer_credit_missing_documents")

        db.session.remove()
        db.drop_all()


def test_models_declare_key_duplicate_guards():
    from app.models import PortfolioSubmission, ProjectMember, StudentProfile

    assert any(constraint.name == "uq_student_profile_user" for constraint in StudentProfile.__table__.constraints)
    assert any(constraint.name == "uq_project_group_member" for constraint in ProjectMember.__table__.constraints)
    assert any(constraint.name == "uq_portfolio_submission_version" for constraint in PortfolioSubmission.__table__.constraints)


def test_normalized_model_rejects_invalid_repeating_values():
    from app.models.transfer_credit import normalize_missing_document_names

    try:
        AdmissionRequirementItem(mapped_categories="x" * 51)
    except ValueError as error:
        assert "50" in str(error)
    else:
        raise AssertionError("過長的招生類別應被拒絕")

    try:
        normalize_missing_document_names("文件\x00名稱")
    except ValueError as error:
        assert "控制字元" in str(error)
    else:
        raise AssertionError("控制字元應被拒絕")
