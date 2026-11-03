"""只供本機展示使用的合成資料應用程式。"""

from datetime import date

from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db
from app.models import (
    AdmissionProgram,
    AuditLog,
    ClassAdvisor,
    CredentialRecord,
    LearningCourseRecord,
    Portfolio,
    StudentProfile,
    StudentTarget,
    User,
)
from app.services.admission_service import import_seed_programs
from app.services.demo_showcase import seed_pending_ocr_review
from app.services.journey_service import academic_year_of


DEMO_PASSWORD = "demo2026"

# 登入頁「Demo 快速登入」列出的帳號（只有設定 DEMO_ACCOUNTS 的展示站會顯示）
DEMO_ACCOUNTS = [
    {"role": "student", "label": "學生", "username": "student_demo", "password": DEMO_PASSWORD, "name": "合成新生", "note": "專一新生・從零開始整理"},
    {"role": "student", "label": "學生", "username": "student_showcase", "password": DEMO_PASSWORD, "name": "合成專五學生", "note": "專五完整示範・含待核對 OCR 與 Agent 流程"},
    {"role": "teacher", "label": "導師", "username": "teacher_demo", "password": DEMO_PASSWORD, "name": "合成導師"},
    {"role": "staff", "label": "科辦", "username": "staff_demo", "password": DEMO_PASSWORD, "name": "合成科助"},
    {"role": "admin", "label": "管理者", "username": "admin_demo", "password": DEMO_PASSWORD, "name": "合成管理者"},
]


class SerializedWSGI:
    """讓展示站一次只處理一個請求（網站仍可同時接受多條連線）。

    展示站的資料庫在記憶體中，所有執行緒共用同一條 SQLite 連線（StaticPool）；
    同時處理多個請求時查詢會互相干擾，實測會把已登入的人誤判為未登入、或誤回 404。
    正式環境使用 MySQL 連線池，不需要這一層。
    """

    def __init__(self, app):
        import threading

        self.app = app
        self.lock = threading.Lock()

    def __call__(self, environ, start_response):
        with self.lock:
            response = self.app(environ, start_response)
            try:
                return list(response)  # 在鎖內讀完整個回應（含檔案下載）
            finally:
                if hasattr(response, "close"):
                    response.close()


def create_local_demo_app():
    """建立只在記憶體 SQLite 運作的合成資料展示站，絕不連到 .env 資料庫。"""
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
        "TESTING": False,
        "SECRET_KEY": "local-demo-only-not-for-production",
        "LOCAL_DEMO_MODE": True,
        "DEMO_ACCOUNTS": DEMO_ACCOUNTS,
        "AI_ENABLED": False,
        "AI_PROVIDER": "none",
        "AI_API_KEY": "",
        "DOCUMENT_ANALYSIS_PROVIDER": "demo",
        "GOOGLE_DRIVE_PREVIEW_ENABLED": False,
        "GOOGLE_OAUTH_CLIENT_ID": "",
        "GOOGLE_PICKER_API_KEY": "",
        "GOOGLE_CLOUD_PROJECT_NUMBER": "",
    })
    with app.app_context():
        db.create_all()
        users = {}
        for role in ("student", "teacher", "staff", "admin"):
            user = User(username=f"{role}_demo", display_name=f"合成{role}帳號", role=role)
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
            users[role] = user
        db.session.flush()
        current_year = academic_year_of(date.today())
        db.session.add(StudentProfile(
            user_id=users["student"].id,
            student_no="DEMO-0001",
            class_name="資管科測試班",
            admission_year=current_year,
        ))
        db.session.add(ClassAdvisor(
            teacher_id=users["teacher"].id,
            class_name="資管科測試班",
            school_year=current_year,
        ))
        db.session.add(AuditLog(user_id=users["student"].id, action="student.welcome_done"))
        import_seed_programs()
        showcase = User(username="student_showcase", display_name="合成專五學生", role="student")
        showcase.set_password(DEMO_PASSWORD)
        db.session.add(showcase)
        db.session.flush()
        db.session.add(StudentProfile(
            user_id=showcase.id,
            student_no="DEMO-0002",
            class_name="資管科展示班",
            admission_year=current_year - 4,
        ))
        db.session.add(ClassAdvisor(
            teacher_id=users["teacher"].id,
            class_name="資管科展示班",
            school_year=current_year,
        ))
        courses = (
            (1, "上", "計算機概論", 90), (1, "下", "程式設計", 88),
            (2, "上", "網頁設計", 85), (2, "下", "管理資訊系統", 82),
            (3, "上", "資料庫管理", 89), (3, "下", "系統分析與設計", 86),
            (4, "上", "行動裝置程式設計", 91), (4, "下", "網路管理實務", 84),
            (5, "上", "專題製作", 93), (5, "上", "資訊專題研究", 90),
        )
        for grade_level, semester, course_name, score in courses:
            db.session.add(LearningCourseRecord(
                student_id=showcase.id, school_year=grade_level, semester=semester,
                course_name=course_name, normalized_course_name=course_name,
                credits=3, score=score,
            ))
        db.session.add(CredentialRecord(
            student_id=showcase.id, credential_name="電腦軟體應用丙級", level="丙級",
            issuing_organization="勞動部", issue_date=date(2025, 4, 12),
        ))
        for category, grade_level, title in (
            ("activity", 1, "資管科迎新活動"),
            ("competition", 2, "全國商業類技藝競賽佳作"),
            ("service", 3, "資訊志工服務"),
            ("leadership", 4, "班級學藝股長"),
        ):
            db.session.add(Portfolio(
                student_id=showcase.id, category=category, school_year=grade_level,
                semester=1, title=title, status="confirmed",
            ))
        program = AdmissionProgram.query.filter_by(program_code="208003").one()
        db.session.add(StudentTarget(student_id=showcase.id, rule_version_id=program.id))
        seed_pending_ocr_review(showcase)
        db.session.add(AuditLog(user_id=showcase.id, action="student.welcome_done"))
        db.session.commit()
    app.wsgi_app = SerializedWSGI(app.wsgi_app)
    return app
