"""
User Profile Blueprint.
"""

from flask import Blueprint, render_template, session, flash, redirect, url_for
from app.routes.auth import login_required
from app.services import db_service

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/")
@login_required
def profile():
    """View user profile, statistics, and system metadata."""
    user = session["user"]
    user_id = user["user_id"]

    try:
        user_record = db_service.get_user_by_id(user_id)
        total_mri = db_service.get_total_mri_count(user_id)
        total_cog = db_service.get_total_cognitive_count(user_id)
        reports = db_service.get_user_reports(user_id)
    except Exception:
        user_record = user
        total_mri = 0
        total_cog = 0
        reports = []

    return render_template(
        "profile.html",
        user_record=user_record,
        total_mri=total_mri,
        total_cog=total_cog,
        total_reports=len(reports)
    )
