"""
Reports Blueprint.
Handles on-demand ReportLab PDF generation, saving, and downloading.
"""

from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app
from app.routes.auth import login_required
from app.services import db_service, report_service, cognitive_service

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    """Generate integrated medical PDF report for user."""
    user = session["user"]
    user_id = user["user_id"]

    mri_id = request.args.get("mri_id") or request.form.get("mri_id")
    cog_id = request.args.get("cog_id") or request.form.get("cog_id")

    # Fetch records
    mri_record = None
    if mri_id:
        mri_record = db_service.get_prediction_by_id(int(mri_id), user_id)
    else:
        mri_record = db_service.get_latest_mri_prediction(user_id)

    cog_record = None
    if cog_id:
        cog_record = db_service.get_assessment_by_id(int(cog_id), user_id)
    else:
        latest_c = db_service.get_latest_cognitive_assessment(user_id)
        if latest_c:
            cog_record = db_service.get_assessment_by_id(latest_c["assessment_id"], user_id)

    if not mri_record and not cog_record:
        flash("Please perform at least one MRI prediction or cognitive assessment before generating a report.", "warning")
        return redirect(url_for("dashboard.dashboard"))

    # Format MRI data
    mri_data = None
    if mri_record:
        base_name = Path(mri_record["image_path"]).stem.replace("mri_", "")
        uuid_part = base_name.split("_")[-1]
        mri_data = {
            "predicted_category": mri_record["predicted_category"],
            "confidence": mri_record["confidence"],
            "image_path": f"app/{mri_record['image_path']}",
            "gradcam_path": f"app/static/heatmaps/sbs_{uuid_part}.png"
        }

    # Format Cognitive data
    cog_data = None
    if cog_record:
        answers_dict = {str(a["question_id"]): a["selected_answer"] for a in cog_record.get("answers", [])}
        cog_data = cognitive_service.score_assessment(answers_dict)

    try:
        report_filename = f"Report_UID{user_id}_{mri_record['prediction_id'] if mri_record else '0'}_{cog_record['assessment_id'] if cog_record else '0'}.pdf"
        output_path = report_service.generate_pdf_report(
            user_info=user,
            mri_result=mri_data,
            cognitive_result=cog_data,
            output_filename=report_filename
        )

        # Save to database
        rel_report_path = f"static/reports/{report_filename}"
        db_service.save_report(user_id, rel_report_path)

        flash("Comprehensive PDF report generated successfully!", "success")
        return redirect(url_for("reports.download", filename=report_filename))

    except Exception as e:
        flash(f"Error generating report: {str(e)}", "danger")
        return redirect(url_for("dashboard.dashboard"))


@reports_bp.route("/download/<filename>")
@login_required
def download(filename):
    """Serve generated PDF report file."""
    reports_dir = Path(current_app.root_path) / "static" / "reports"
    file_path = reports_dir / filename
    if not file_path.exists():
        flash("Requested report file does not exist.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    return send_file(
        str(file_path),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route("/history")
@login_required
def history():
    """List all reports generated for the user."""
    user = session["user"]
    try:
        records = db_service.get_user_reports(user["user_id"])
    except Exception as e:
        records = []
        flash(f"Error loading reports: {str(e)}", "danger")

    return render_template("reports_history.html", reports=records)
