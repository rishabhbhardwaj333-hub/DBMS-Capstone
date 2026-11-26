"""User authentication and HR user management service."""

from backend.auth import hash_password, verify_password
from backend.database import query_all, query_one, transaction


def authenticate_user(username: str, raw_password: str):
    """
    Validate username and password against user_accounts.
    Returns user + employee dict if valid and active, else None.
    """
    if not username or not raw_password:
        return None

    user = query_one(
        """
        SELECT u.user_id, u.employee_id, u.username, u.password_hash, u.role, u.is_active,
               e.emp_code, e.first_name, e.last_name, e.employment_status
        FROM user_accounts u
        JOIN employees e ON u.employee_id = e.employee_id
        WHERE u.username = %s
        LIMIT 1
        """,
        (username.strip(),),
    )
    if not user:
        return None
    if not user["is_active"] or user["employment_status"] in ("RESIGNED", "TERMINATED"):
        return None
    if not verify_password(user["password_hash"], raw_password):
        return None

    with transaction() as (_conn, cursor):
        cursor.execute(
            "UPDATE user_accounts SET last_login_at = NOW() WHERE user_id = %s",
            (user["user_id"],),
        )
    return user


def list_users():
    """Return all system user accounts with linked employee details."""
    return query_all(
        """
        SELECT u.user_id, u.employee_id, u.username, u.role, u.is_active, u.last_login_at,
               e.emp_code, CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               d.department_name, e.employment_status
        FROM user_accounts u
        JOIN employees e ON u.employee_id = e.employee_id
        JOIN departments d ON e.department_id = d.department_id
        ORDER BY u.role ASC, e.emp_code ASC
        """
    )


def list_employees_without_account():
    """Return employees who do not yet have a row in user_accounts."""
    return query_all(
        """
        SELECT e.employee_id, e.emp_code, CONCAT(e.first_name, ' ', e.last_name) AS employee_name
        FROM employees e
        LEFT JOIN user_accounts u ON u.employee_id = e.employee_id
        WHERE u.user_id IS NULL
        ORDER BY e.emp_code
        """
    )


def create_user_account(employee_id: int, username: str, raw_password: str, role: str):
    """Create a new login account for an existing employee."""
    if not username or len(raw_password) < 6:
        raise ValueError("Username is required and password must be at least 6 characters.")
    if role not in ("HR_ADMIN", "EMPLOYEE"):
        raise ValueError("Invalid role.")

    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            INSERT INTO user_accounts (employee_id, username, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (int(employee_id), username.strip().lower(), hash_password(raw_password), role),
        )
        return cursor.lastrowid


def toggle_user_active(user_id: int, current_user_id: int):
    """Enable or disable a user account (preventing self-lockout)."""
    if int(user_id) == int(current_user_id):
        raise ValueError("You cannot deactivate your own active admin account.")
    with transaction() as (_conn, cursor):
        cursor.execute(
            "UPDATE user_accounts SET is_active = NOT is_active WHERE user_id = %s",
            (int(user_id),),
        )


def update_user_role(user_id: int, role: str, current_user_id: int):
    """Update a user's RBAC role."""
    if role not in ("HR_ADMIN", "EMPLOYEE"):
        raise ValueError("Invalid role.")
    if int(user_id) == int(current_user_id) and role != "HR_ADMIN":
        raise ValueError("You cannot downgrade your own HR_ADMIN role while logged in.")
    with transaction() as (_conn, cursor):
        cursor.execute(
            "UPDATE user_accounts SET role = %s WHERE user_id = %s",
            (role, int(user_id)),
        )


def reset_user_password(user_id: int, new_password: str):
    """Reset a user's password hash safely."""
    if len(new_password) < 6:
        raise ValueError("New password must be at least 6 characters.")
    with transaction() as (_conn, cursor):
        cursor.execute(
            "UPDATE user_accounts SET password_hash = %s WHERE user_id = %s",
            (hash_password(new_password), int(user_id)),
        )
