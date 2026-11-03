"""
MRI Analysis and Explainable AI Blueprint.
Handles MRI scan upload, format verification, CNN classification,
Grad-CAM heatmap rendering, and prediction history.
"""

import os
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from PIL import Image

from app.routes.auth import login_required
from app.services import db_service, interpretation_service

mri_bp = Blueprint("mri", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]

# Lazy-loaded GradCAM explainer
_explainer = None


def get_explainer():
    """Singleton getter for the GradCAMExplainer."""
    global _explainer
    if _explainer is None:
        from ml.gradcam import GradCAMExplainer
        model_path = Path(current_app.root_path).parent / "models" / "saved_models" / "alzheimer_cnn_best.keras"
        if model_path.exists():
            _explainer = GradCAMExplainer(model_path=str(model_path), target_layer_name="last_conv_layer")
        else:
            return None
    return _explainer


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@mri_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Handle MRI scan upload and launch classification."""
    user = session["user"]

    if request.method == "POST":
        if "mri_file" not in request.files:
            flash("No file part provided in the request.", "danger")
            return redirect(request.url)

        file = request.files["mri_file"]
        if file.filename == "":
            flash("No image selected for upload.", "danger")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file format. Please upload a valid brain MRI in JPG, JPEG, or PNG format.", "danger")
            return redirect(request.url)

        # Secure file naming
        ext = file.filename.rsplit(".", 1)[1].lower()
        file_uuid = uuid.uuid4().hex
        filename = f"mri_u{user['user_id']}_{file_uuid}.{ext}"

        upload_dir = Path(current_app.root_path) / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        file.save(str(file_path))

        # Verify image integrity
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception:
            if file_path.exists():
                file_path.unlink()
            flash("Corrupted image file rejected. Please upload an intact neuroimaging scan.", "danger")
            return redirect(request.url)

        # Check if trained model is available
        explainer = get_explainer()
        if explainer is None:
            flash("Trained CNN model is not loaded yet. Please train the model first.", "warning")
            return redirect(url_for("mri.history"))

        try:
            # Generate Grad-CAM and side-by-side
            heatmaps_dir = Path(current_app.root_path) / "static" / "heatmaps"
            heatmaps_dir.mkdir(parents=True, exist_ok=True)

            overlay_filename = f"overlay_{file_uuid}.png"
            side_by_side_filename = f"sbs_{file_uuid}.png"
            heatmap_filename = f"heatmap_{file_uuid}.png"

            overlay_path = heatmaps_dir / overlay_filename
            sbs_path = heatmaps_dir / side_by_side_filename
            heatmap_path = heatmaps_dir / heatmap_filename

            result = explainer.explain(
                img_input=str(file_path),
                output_overlay_path=str(overlay_path),
                output_side_by_side_path=str(sbs_path),
                output_heatmap_path=str(heatmap_path)
            )

            # Relative paths for database and web display
            db_img_rel = f"static/uploads/{filename}"
            predicted_class = result["predicted_class"]
            confidence = result["confidence"]

            # Save to MySQL
            prediction_id = db_service.save_mri_prediction(
                user_id=user["user_id"],
                image_path=db_img_rel,
                predicted_category=predicted_class,
                confidence=confidence
            )

            # Store recent result in session for display
            session["latest_prediction"] = {
                "prediction_id": prediction_id,
                "image_rel": db_img_rel,
                "overlay_rel": f"static/heatmaps/{overlay_filename}",
                "sbs_rel": f"static/heatmaps/{side_by_side_filename}",
                "heatmap_rel": f"static/heatmaps/{heatmap_filename}",
                "predicted_category": predicted_class,
                "confidence": confidence,
                "all_probabilities": result["all_probabilities"]
            }

            flash("MRI successfully analyzed and classified!", "success")
            return redirect(url_for("mri.result", prediction_id=prediction_id))

        except Exception as e:
            flash(f"Inference error during MRI analysis: {str(e)}", "danger")
            return redirect(request.url)

    # Check for sample images available for quick testing
    samples_dir = Path(current_app.root_path).parent / "data" / "samples"
    sample_images = []
    if samples_dir.exists():
        sample_images = [f.name for f in samples_dir.glob("*.png")]

    return render_template("mri_upload.html", sample_images=sample_images)


def get_prediction_probabilities(record, session_probs=None):
    """Retrieve or dynamically calculate 4-class probability distribution."""
    if session_probs and isinstance(session_probs, dict):
        return session_probs

    img_path = Path(current_app.root_path) / record["image_path"]
    if img_path.exists():
        explainer = get_explainer()
        if explainer:
            try:
                img_tensor, _ = explainer.preprocess_image(str(img_path))
                _, _, _, all_probs = explainer.compute_gradcam(img_tensor)
                return {cls: float(all_probs[i]) for i, cls in enumerate(TARGET_CLASSES)}
            except Exception:
                pass

    # Calibrated fallback based on recorded confidence
    conf = float(record["confidence"])
    rem = max(0.001, (1.0 - conf) / 3.0)
    return {
        cls: (conf if cls == record["predicted_category"] else rem)
        for cls in TARGET_CLASSES
    }


@mri_bp.route("/result/<int:prediction_id>")
@login_required
def result(prediction_id):
    """Display comprehensive prediction result and confidence metrics."""
    user = session["user"]
    record = db_service.get_prediction_by_id(prediction_id, user["user_id"])
    if not record:
        flash("Prediction record not found or unauthorized.", "danger")
        return redirect(url_for("mri.history"))

    latest_session = session.get("latest_prediction", {})
    if latest_session.get("prediction_id") == prediction_id:
        overlay_rel = latest_session.get("overlay_rel")
        sbs_rel = latest_session.get("sbs_rel")
        probs = latest_session.get("all_probabilities")
    else:
        # Determine from image path
        base_name = Path(record["image_path"]).stem.replace("mri_", "")
        uuid_part = base_name.split("_")[-1]
        overlay_rel = f"static/heatmaps/overlay_{uuid_part}.png"
        sbs_rel = f"static/heatmaps/sbs_{uuid_part}.png"
        probs = None

    # Calculate probabilities and rich stage information
    probabilities = get_prediction_probabilities(record, probs)
    stage_info = interpretation_service.get_stage_info(record["predicted_category"])
    prob_breakdown = interpretation_service.format_probability_breakdown(probabilities, record["predicted_category"])

    return render_template(
        "mri_result.html",
        record=record,
        overlay_rel=overlay_rel,
        sbs_rel=sbs_rel,
        probabilities=probabilities,
        stage_info=stage_info,
        prob_breakdown=prob_breakdown
    )


@mri_bp.route("/gradcam/<int:prediction_id>")
@login_required
def gradcam(prediction_id):
    """Dedicated Explainable AI (Grad-CAM) exploration page."""
    user = session["user"]
    record = db_service.get_prediction_by_id(prediction_id, user["user_id"])
    if not record:
        flash("Prediction record not found.", "danger")
        return redirect(url_for("mri.history"))

    base_name = Path(record["image_path"]).stem.replace("mri_", "")
    uuid_part = base_name.split("_")[-1]

    orig_rel = record["image_path"]
    overlay_rel = f"static/heatmaps/overlay_{uuid_part}.png"
    sbs_rel = f"static/heatmaps/sbs_{uuid_part}.png"
    heatmap_rel = f"static/heatmaps/heatmap_{uuid_part}.png"

    # Ensure full files exist on disk with latest clean formatting
    sbs_full = Path(current_app.root_path) / sbs_rel
    heatmap_full = Path(current_app.root_path) / heatmap_rel
    overlay_full = Path(current_app.root_path) / overlay_rel
    orig_full = Path(current_app.root_path) / orig_rel

    if not sbs_full.exists() or not heatmap_full.exists() or not overlay_full.exists():
        explainer = get_explainer()
        if explainer and orig_full.exists():
            explainer.explain(
                img_input=str(orig_full),
                output_overlay_path=str(overlay_full),
                output_side_by_side_path=str(sbs_full),
                output_heatmap_path=str(heatmap_full)
            )

    stage_info = interpretation_service.get_stage_info(record["predicted_category"])

    return render_template(
        "gradcam.html",
        record=record,
        orig_rel=orig_rel,
        overlay_rel=overlay_rel,
        heatmap_rel=heatmap_rel,
        sbs_rel=sbs_rel,
        stage_info=stage_info
    )


@mri_bp.route("/history")
@login_required
def history():
    """Display user's MRI prediction records."""
    user = session["user"]
    try:
        records = db_service.get_user_mri_predictions(user["user_id"])
    except Exception as e:
        records = []
        flash(f"Error loading records: {str(e)}", "danger")

    return render_template("prediction_history.html", records=records)


@mri_bp.route("/delete/<int:prediction_id>", methods=["POST"])
@login_required
def delete(prediction_id):
    """Delete an MRI prediction record belonging to user."""
    user = session["user"]
    success, record = db_service.delete_mri_prediction(prediction_id, user["user_id"])
    if success:
        # Clean up files from storage if present
        try:
            if record and record.get("image_path"):
                p = Path(current_app.root_path) / record["image_path"]
                if p.exists():
                    p.unlink()

                base_name = p.stem.replace("mri_", "")
                uuid_part = base_name.split("_")[-1]
                heatmaps_dir = Path(current_app.root_path) / "static" / "heatmaps"
                for prefix in ["overlay_", "sbs_", "heatmap_"]:
                    hm_file = heatmaps_dir / f"{prefix}{uuid_part}.png"
                    if hm_file.exists():
                        hm_file.unlink()
        except Exception:
            pass

        flash(f"MRI Prediction record #{prediction_id} has been permanently deleted.", "success")
    else:
        flash("Record not found or unauthorized.", "danger")

    return redirect(url_for("mri.history"))
