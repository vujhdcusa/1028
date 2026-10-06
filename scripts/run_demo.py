"""用測試資料啟動展示版網站（SQLite，不會連到 MySQL）。

用法（在專案根目錄）：
    .venv\\Scripts\\python.exe scripts\\run_demo.py
然後打開 http://127.0.0.1:5000

展示帳號（皆為假資料）：
    學生  111534105 / demo1234
    導師  teacher01 / demo1234
    管理者 admin     / demo1234
每次啟動都會重建 instance/demo.db。
"""

import os
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    CredentialRecord,
    LearningCourseRecord,
    Portfolio,
    StudentProfile,
    User,
)

DEMO_DB = PROJECT_ROOT / "instance" / "demo.db"
DEMO_PASSWORD = "demo1234"


def seed():
    student = User(username="111534105", display_name="王小明", role="student")
    teacher = User(username="teacher01", display_name="陳導師", role="teacher")
    admin = User(username="admin", display_name="系統管理者", role="admin")
    for user in (student, teacher, admin):
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
    db.session.flush()
    db.session.add(StudentProfile(user_id=student.id, student_no="111534105", class_name="資管科三甲", admission_year=113))

    courses = [
        (1, "上", "計算機概論", 3, 88), (1, "下", "程式設計（一）", 3, 91), (1, "下", "國文", 2, 82),
        (2, "上", "資料庫管理", 3, 85), (2, "下", "網頁設計", 3, 93), (3, "上", "系統分析", 3, 79),
    ]
    for year, semester, name, credits, score in courses:
        db.session.add(LearningCourseRecord(
            student_id=student.id, school_year=year, semester=semester, course_name=name,
            normalized_course_name="".join(name.split()), credits=credits, score=score,
        ))
    db.session.add(CredentialRecord(student_id=student.id, credential_name="電腦軟體應用丙級", level="丙級",
                                    issuing_organization="勞動部", issue_date=date(2025, 5, 20)))
    db.session.add(CredentialRecord(student_id=student.id, credential_name="網頁設計乙級", level="乙級",
                                    issuing_organization="勞動部", issue_date=date(2025, 11, 2)))
    records = [
        ("activity", 1, 1, "資管科迎新宿營", "擔任小隊輔，帶領新生認識校園。"),
        ("service", 2, 1, "資訊週志工", "協助活動報到與場地引導。"),
        ("leadership", 2, 2, "班級學藝股長", "負責班級公告與學習資料整理。"),
        ("activity", 3, 1, "校園黑客松", "三人一組，兩天內完成活動報名網站。"),
    ]
    for category, year, semester, title, description in records:
        db.session.add(Portfolio(student_id=student.id, category=category, school_year=year,
                                 semester=semester, title=title, description=description))
    db.session.commit()


def main():
    DEMO_DB.parent.mkdir(parents=True, exist_ok=True)
    DEMO_DB.unlink(missing_ok=True)
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{DEMO_DB.as_posix()}",
        "UPLOAD_FOLDER": str(PROJECT_ROOT / "instance" / "demo-uploads"),
    })
    with app.app_context():
        db.create_all()
        seed()
    port = int(os.getenv("DEMO_PORT", "5000"))
    print(f"展示網站：http://127.0.0.1:{port}  （學生 111534105 / {DEMO_PASSWORD}）")
    app.run(port=port, debug=False)


if __name__ == "__main__":
    main()
