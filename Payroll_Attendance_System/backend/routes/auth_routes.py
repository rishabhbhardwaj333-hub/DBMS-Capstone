"""Authentication routes: root redirect, login, and logout."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from backend.auth import login_user_session, logout_user_session
from backend.services.user_service import authenticate_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Redirect authenticated users to their role dashboard, else login."""
    role = session.get("role")
    if role == "HR_ADMIN":
        return redirect(url_for("admin.dashboard"))
    if role == "EMPLOYEE":
        return redirect(url_for("employee.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render login form and authenticate against MySQL user_accounts."""
    if "user_id" in session:
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = authenticate_user(username, password)
        if not user:
            flash("Invalid username or password, or account is inactive.", "danger")
            return render_template("login.html"), 401

        login_user_session(user)
        flash(f"Welcome back, {user['first_name']}!", "success")
        if user["role"] == "HR_ADMIN":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("employee.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Terminate the user session securely."""
    logout_user_session()
    flash("You have been signed out securely.", "info")
    return redirect(url_for("auth.login"))
