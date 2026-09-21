from flask import Flask

from app.config import Config
from app.extensions import db, migrate
from app.security import init_security


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db)
    init_security(app)

    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.student import student_bp
    from app.routes.review import review_bp
    from app.routes.staff import staff_bp
    from app import models

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(staff_bp)

    return app
