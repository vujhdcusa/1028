from app import create_app
from app.extensions import db
from sqlalchemy import inspect


def test_flask_migrate_commands_are_registered_on_the_application():
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
        }
    )

    result = app.test_cli_runner().invoke(args=["db", "--help"])

    assert result.exit_code == 0
    assert "upgrade" in result.output


def test_teacher_feedback_migration_creates_the_required_table(tmp_path):
    database_path = tmp_path / "migration-check.db"
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "TESTING": True,
        }
    )

    result = app.test_cli_runner().invoke(args=["db", "upgrade"])

    assert result.exit_code == 0
    with app.app_context():
        columns = {column["name"] for column in inspect(db.engine).get_columns("teacher_review_feedback")}
    assert {"id", "submission_id", "teacher_id", "comment", "created_at"} <= columns


def test_teacher_feedback_migration_downgrade_removes_the_table(tmp_path):
    database_path = tmp_path / "migration-downgrade-check.db"
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "TESTING": True,
        }
    )
    runner = app.test_cli_runner()

    assert runner.invoke(args=["db", "upgrade"]).exit_code == 0
    assert runner.invoke(args=["db", "downgrade", "base"]).exit_code == 0
    with app.app_context():
        assert not inspect(db.engine).has_table("teacher_review_feedback")


def test_admission_main_line_migration_upgrades_and_downgrades(tmp_path):
    database_path = tmp_path / "admission-migration.db"
    app = create_app({"SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}", "TESTING": True})
    runner = app.test_cli_runner()

    assert runner.invoke(args=["db", "upgrade"]).exit_code == 0
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())
    assert {"admission_rule_versions", "admission_rule_items", "student_targets",
            "class_advisors", "package_reviews"} <= tables

    assert runner.invoke(args=["db", "downgrade", "fc61707846c7"]).exit_code == 0
    with app.app_context():
        db.engine.dispose()
        tables = set(inspect(db.engine).get_table_names())
    assert "package_reviews" not in tables
