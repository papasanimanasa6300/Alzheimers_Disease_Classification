"""
Authentication Blueprint for User Registration, Login, Logout, and Session Security.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.services import db_service

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Decorator ensuring route is accessed only by authenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle new user registration."""
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html", username=username, email=email)

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "danger")
            return render_template("register.html", username=username, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", username=username, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", username=username, email=email)

        try:
            # Check if username or email already exists
            if db_service.get_user_by_username(username):
                flash("Username is already registered. Please choose another.", "danger")
                return render_template("register.html", email=email)

            if db_service.get_user_by_email(email):
                flash("Email is already registered. Please log in.", "danger")
                return render_template("register.html", username=username)

            # Hash password and insert user
            pwd_hash = generate_password_hash(password, method="scrypt")
            user_id = db_service.create_user(username, email, pwd_hash)

            flash("Registration successful! You may now log in.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            flash(f"Database error during registration: {str(e)}", "danger")
            return render_template("register.html", username=username, email=email)

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login and session creation."""
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        login_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not login_id or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("login.html", login_id=login_id)

        try:
            # Support login with either username or email
            user = db_service.get_user_by_username(login_id)
            if not user:
                user = db_service.get_user_by_email(login_id.lower())

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user"] = {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "email": user["email"]
                }
                flash(f"Welcome back, {user['username']}!", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("dashboard.dashboard"))
            else:
                flash("Invalid username or password.", "danger")
                return render_template("login.html", login_id=login_id)

        except Exception as e:
            flash(f"Database connection error: {str(e)}", "danger")
            return render_template("login.html", login_id=login_id)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Clear session and log user out."""
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("dashboard.index"))
