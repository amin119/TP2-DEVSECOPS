"""SecureNotes - application Flask de démonstration pour le TP2 DevSecOps."""
import os
import secrets

from flask import Flask

from . import db
from .routes import bp
from .security import register_security


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        # La clé est lue depuis l'environnement ; à défaut, une clé aléatoire
        # est générée (jamais de secret codé en dur dans le dépôt).
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.environ.get("DATABASE_PATH", "securenotes.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    register_security(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.init_db()

    return app
