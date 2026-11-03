"""
Flask Application Factory for Alzheimer's Classification and Cognitive Assessment Platform.
"""

import os
from pathlib import Path
from flask import Flask, render_template, session, redirect, url_for, g
from dotenv import load_dotenv

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Base configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "alzheimers-super-secure-dev-key-2026"),
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", "app/static/uploads"),
        HEATMAP_FOLDER=os.getenv("HEATMAP_FOLDER", "app/static/heatmaps"),
        REPORT_FOLDER=os.getenv("REPORT_FOLDER", "app/static/reports"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB max upload
    )

    if test_config:
        app.config.update(test_config)

    # Ensure required static directories exist
    base_dir = Path(__file__).resolve().parent
    (base_dir / "static" / "uploads").mkdir(parents=True, exist_ok=True)
    (base_dir / "static" / "heatmaps").mkdir(parents=True, exist_ok=True)
    (base_dir / "static" / "reports").mkdir(parents=True, exist_ok=True)

    # Register Context Processors
    @app.context_processor
    def inject_user():
        return {
            "current_user": session.get("user"),
            "is_authenticated": "user" in session
        }

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.mri import mri_bp
    from app.routes.cognitive import cognitive_bp
    from app.routes.reports import reports_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="")
    app.register_blueprint(mri_bp, url_prefix="/mri")
    app.register_blueprint(cognitive_bp, url_prefix="/cognitive")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(profile_bp, url_prefix="/profile")

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html", error=str(e)), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template("400.html", message="Uploaded file exceeds 16MB limit."), 413

    return app
