from flask import Flask

from app.config import Config
from app.extensions import db


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    from app.routes.main import main_bp
    from app import models

    app.register_blueprint(main_bp)

    return app
