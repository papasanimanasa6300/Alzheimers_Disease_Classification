"""
Cognitive Assessment Blueprint.
Provides interactive educational cognitive testing across 5 domains,
scoring engine, domain breakdown, dynamic alternate test forms, and historical tracking.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.routes.auth import login_required
from app.services import db_service, cognitive_service

cognitive_bp = Blueprint("cognitive", __name__)


@cognitive_bp.route("/test", methods=["GET"])
@login_required
def test():
    """Interactive cognitive assessment questionnaire with dynamic procedural questions."""
    user = session["user"]
    prev_count = db_service.get_total_cognitive_count(user["user_id"])

    # Generate fresh randomized questions every single time
    raw_questions = cognitive_service.generate_dynamic_test()
    session["active_test_raw_questions"] = raw_questions
    questions = cognitive_service.sanitize_questions_for_client(raw_questions)

    return render_template(
        "cognitive_assessment.html",
        questions=questions,
        prev_count=prev_count
    )


@cognitive_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    """Evaluate and store submitted cognitive responses."""
    user = session["user"]

    # Gather answers from form
    answers = {}
    for key, value in request.form.items():
        if key.startswith("q_"):
            qid = key.replace("q_", "")
            answers[qid] = value

    if not answers:
        flash("No answers were submitted. Please complete the assessment.", "danger")
        return redirect(url_for("cognitive.test"))

    try:
        # Score the test using active session questions
        raw_questions = session.get("active_test_raw_questions")
        result = cognitive_service.score_assessment(answers, dynamic_questions=raw_questions)

        # Store in database
        assessment_id = db_service.save_cognitive_assessment(
            user_id=user["user_id"],
            total_score=result["total_score"],
            answers_breakdown=result["detailed_breakdown"]
        )

        session["latest_cognitive"] = {
            "assessment_id": assessment_id,
            "result": result
        }

        # Clear session questions
        session.pop("active_test_raw_questions", None)

        flash("Cognitive assessment completed and scored successfully!", "success")
        return redirect(url_for("cognitive.result", assessment_id=assessment_id))

    except Exception as e:
        flash(f"Error processing assessment: {str(e)}", "danger")
        return redirect(url_for("cognitive.test"))


@cognitive_bp.route("/result/<int:assessment_id>")
@login_required
def result(assessment_id):
    """View detailed score breakdown, progress comparison, and educational interpretation."""
    user = session["user"]
    record = db_service.get_assessment_by_id(assessment_id, user["user_id"])
    if not record:
        flash("Assessment record not found.", "danger")
        return redirect(url_for("cognitive.history"))

    # Convert answers to dict for scoring re-evaluation
    answers_dict = {str(a["question_id"]): a["selected_answer"] for a in record.get("answers", [])}
    scored_info = cognitive_service.score_assessment(answers_dict)

    # Check for previous assessment to calculate progress / improvement
    prev_assessment = db_service.get_previous_cognitive_assessment(user["user_id"], assessment_id)
    progress_comparison = cognitive_service.compare_with_previous(scored_info["total_score"], prev_assessment)

    return render_template(
        "cognitive_result.html",
        record=record,
        result=scored_info,
        progress=progress_comparison,
        prev_record=prev_assessment
    )


@cognitive_bp.route("/history")
@login_required
def history():
    """Display user's historical cognitive assessments."""
    user = session["user"]
    try:
        records = db_service.get_user_cognitive_assessments(user["user_id"])
    except Exception as e:
        records = []
        flash(f"Error loading assessment history: {str(e)}", "danger")

    return render_template("assessment_history.html", records=records)


@cognitive_bp.route("/delete/<int:assessment_id>", methods=["POST"])
@login_required
def delete(assessment_id):
    """Delete a user's cognitive assessment record."""
    user = session["user"]
    success = db_service.delete_cognitive_assessment(assessment_id, user["user_id"])
    if success:
        flash(f"Cognitive Assessment record #{assessment_id} has been permanently deleted.", "success")
    else:
        flash("Record not found or unauthorized.", "danger")

    return redirect(url_for("cognitive.history"))
