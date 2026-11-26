"""Session authentication and Role-Based Access Control (RBAC) helpers."""

from functools import wraps
from flask import session, redirect, url_for, flash, abort, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(raw_password: str) -> str:
    """Hash a plaintext password using Werkzeug's salted scrypt algorithm."""
    return generate_password_hash(raw_password)


def verify_password(password_hash: str, raw_password: str) -> bool:
    """Verify a plaintext password against a stored cryptographic hash."""
    if not password_hash or not raw_password:
        return False
    return check_password_hash(password_hash, raw_password)


def current_user():
    """Return the authenticated user dict from the Flask session, or None."""
    if "user_id" not in session:
        return None
    return {
        "user_id": session.get("user_id"),
        "employee_id": session.get("employee_id"),
        "emp_code": session.get("emp_code"),
        "username": session.get("username"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
    }


def login_user_session(user_row: dict):
    """Populate session state cleanly after successful authentication."""
    session.clear()
    session.permanent = True
    session["user_id"] = user_row["user_id"]
    session["employee_id"] = user_row["employee_id"]
    session["emp_code"] = user_row["emp_code"]
    session["username"] = user_row["username"]
    session["role"] = user_row["role"]
    session["full_name"] = f"{user_row['first_name']} {user_row['last_name']}"


def logout_user_session():
    """Clear all session keys on logout."""
    session.clear()


def login_required(view_func):
    """Require an authenticated session for a route."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            flash("Please sign in to access the system.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(*allowed_roles):
    """Enforce server-side RBAC role checks on routes."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                flash("Please sign in to access the system.", "warning")
                return redirect(url_for("auth.login"))
            if session.get("role") not in allowed_roles:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden: insufficient permissions"}), 403
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
