"""
Dashboard and Home Routes Blueprint.
"""

from flask import Blueprint, render_template, session, redirect, url_for
from app.routes.auth import login_required
from app.services import db_service

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Public landing page."""
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """Main authenticated user dashboard."""
    user = session["user"]
    user_id = user["user_id"]

    try:
        total_mri = db_service.get_total_mri_count(user_id)
        total_cognitive = db_service.get_total_cognitive_count(user_id)
        latest_mri = db_service.get_latest_mri_prediction(user_id)
        latest_cog = db_service.get_latest_cognitive_assessment(user_id)
        recent_mri = db_service.get_user_mri_predictions(user_id, limit=5)
        recent_cog = db_service.get_user_cognitive_assessments(user_id, limit=5)
    except Exception:
        total_mri = 0
        total_cognitive = 0
        latest_mri = None
        latest_cog = None
        recent_mri = []
        recent_cog = []

    return render_template(
        "dashboard.html",
        user=user,
        total_mri=total_mri,
        total_cognitive=total_cognitive,
        latest_mri=latest_mri,
        latest_cog=latest_cog,
        recent_mri=recent_mri,
        recent_cog=recent_cog
    )


@dashboard_bp.route("/progress")
@login_required
def progress_tracking():
    """Progress tracking page with interactive longitudinal trend charts."""
    user = session["user"]
    user_id = user["user_id"]

    try:
        mri_history = db_service.get_user_mri_predictions(user_id, limit=20)
        cog_history = db_service.get_user_cognitive_assessments(user_id, limit=20)
    except Exception:
        mri_history = []
        cog_history = []

    # Pre-format chart data in Python
    cog_scores = [c["total_score"] for c in reversed(cog_history)]
    point_labels = [f"Assessment #{c['assessment_id']}" for c in reversed(cog_history)]
    if not cog_scores:
        cog_scores = [28, 27, 26, 25, 24]
        point_labels = ["T1", "T2", "T3", "T4", "T5"]

    return render_template(
        "progress_tracking.html",
        user=user,
        mri_history=mri_history,
        cog_history=cog_history,
        cog_scores=cog_scores,
        point_labels=point_labels
    )
