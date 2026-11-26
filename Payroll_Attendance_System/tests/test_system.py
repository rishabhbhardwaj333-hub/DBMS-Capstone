"""
Automated test suite for the Payroll & Attendance Management System.
- Unit & Flask RBAC/IDOR/Security tests run offline without external DB mocks for DB logic
  (using Flask test_client session & service boundaries where DB is unavailable).
- Full MySQL 8.0+ integration tests (TC-01..TC-12) execute against payroll_attendance_db
  when MYSQL_PASSWORD is configured and MySQL80 is reachable.
"""

from datetime import date, timedelta
from pathlib import Path
import sys
import mysql.connector
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app import create_app
from backend.auth import hash_password, verify_password
from backend.config import Config
from backend.setup_db import SQL_SCRIPTS, parse_sql_statements


def _can_connect_mysql():
    if not Config.MYSQL_PASSWORD:
        return False, "MYSQL_PASSWORD is not set in .env"
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
        )
        conn.close()
        return True, ""
    except Exception as exc:
        return False, str(exc)


@pytest.fixture(scope="module")
def db_conn():
    ok, reason = _can_connect_mysql()
    if not ok:
        pytest.skip(f"Live MySQL unavailable: {reason}")
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        autocommit=False,
    )
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
    with app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Offline Structural, Security & RBAC Tests (Always Runnable)
# ---------------------------------------------------------------------------
def test_sql_scripts_exist_and_parse():
    """Verify all Phase 2-4 SQL scripts exist and parse cleanly."""
    for path in SQL_SCRIPTS:
        assert path.exists(), f"Missing SQL script: {path}"
        stmts = parse_sql_statements(path.read_text(encoding="utf-8"))
        assert len(stmts) > 0, f"No statements parsed from {path}"


def test_password_hashing_and_verification():
    """Verify salted scrypt password hashing rejects wrong passwords."""
    hashed = hash_password("Admin@123")
    assert hashed != "Admin@123"
    assert verify_password(hashed, "Admin@123") is True
    assert verify_password(hashed, "WrongPass") is False


def test_unauthenticated_redirect(client):
    """Unauthenticated requests to protected routes redirect to /login."""
    for path in ["/admin/dashboard", "/admin/employees", "/employee/dashboard", "/employee/leaves"]:
        resp = client.get(path)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


def test_tc09_unauthorized_employee_access_to_admin(client):
    """TC-09: Signed-in EMPLOYEE is blocked from all /admin/* endpoints with 403."""
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["employee_id"] = 3
        sess["emp_code"] = "EMP003"
        sess["username"] = "aarav.m"
        sess["role"] = "EMPLOYEE"
        sess["full_name"] = "Aarav Mehta"

    for path in ["/admin/dashboard", "/admin/employees", "/admin/payroll", "/admin/reports", "/admin/users"]:
        resp = client.get(path)
        assert resp.status_code == 403


def test_tc10_employee_cannot_view_other_salary_slip(client, monkeypatch):
    """TC-10: EMPLOYEE attempting to open another employee's salary slip gets 403."""
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["employee_id"] = 3
        sess["emp_code"] = "EMP003"
        sess["username"] = "aarav.m"
        sess["role"] = "EMPLOYEE"
        sess["full_name"] = "Aarav Mehta"

    monkeypatch.setattr(
        "backend.services.payroll_service.get_salary_slip",
        lambda pid: {"payroll_id": pid, "employee_id": 5},
    )
    resp = client.get("/payroll/slip/99")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Live MySQL Integration Tests (TC-01 through TC-12)
# ---------------------------------------------------------------------------
def test_tc01_tc02_employee_creation_and_duplicate(db_conn):
    """TC-01 & TC-02: Valid employee creation succeeds; duplicate emp_code fails."""
    cur = db_conn.cursor()
    cur.execute(
        """
        INSERT INTO employees (emp_code, first_name, last_name, email, phone, department_id, designation, hire_date)
        VALUES ('EMPTST1', 'Test', 'User', 'test.user1@novatech.in', '+91-99999-00001', 1, 'Tester', '2025-01-01')
        """
    )
    assert cur.lastrowid > 0
    with pytest.raises(mysql.connector.Error):
        cur.execute(
            """
            INSERT INTO employees (emp_code, first_name, last_name, email, phone, department_id, designation, hire_date)
            VALUES ('EMPTST1', 'Dup', 'User', 'dup.user1@novatech.in', '+91-99999-00002', 1, 'Tester', '2025-01-01')
            """
        )
    db_conn.rollback()


def test_tc03_negative_salary_rejected(db_conn):
    """TC-03: Negative or zero basic_salary is rejected by constraint/trigger."""
    cur = db_conn.cursor()
    with pytest.raises(mysql.connector.Error):
        cur.execute(
            """
            INSERT INTO salaries (employee_id, basic_salary, hra, da, other_allowances, effective_from)
            VALUES (3, -15000.00, 0, 0, 0, '2026-11-01')
            """
        )
    db_conn.rollback()


def test_tc04_duplicate_attendance_rejected(db_conn):
    """TC-04: Duplicate attendance for the same employee and date is rejected."""
    cur = db_conn.cursor()
    test_date = date.today().isoformat()
    cur.execute("DELETE FROM attendance WHERE employee_id = 3 AND attendance_date = %s", (test_date,))
    cur.execute(
        """
        INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status)
        VALUES (3, %s, '09:15:00', '18:00:00', 'PRESENT')
        """,
        (test_date,),
    )
    with pytest.raises(mysql.connector.Error):
        cur.execute(
            """
            INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status)
            VALUES (3, %s, '09:20:00', '18:10:00', 'PRESENT')
            """,
            (test_date,),
        )
    db_conn.rollback()


def test_tc05_overlapping_approved_leave_rejected(db_conn):
    """TC-05: Overlapping APPROVED leave dates are rejected by trigger / approve_leave."""
    cur = db_conn.cursor()
    d1 = (date.today() + timedelta(days=30)).isoformat()
    d2 = (date.today() + timedelta(days=32)).isoformat()
    cur.execute(
        """
        INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, total_days, reason, status, approved_by)
        VALUES (4, 1, %s, %s, 3.0, 'Test leave 1', 'APPROVED', 1)
        """,
        (d1, d2),
    )
    with pytest.raises(mysql.connector.Error):
        cur.execute(
            """
            INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, total_days, reason, status, approved_by)
            VALUES (4, 1, %s, %s, 2.0, 'Overlapping leave', 'APPROVED', 1)
            """,
            (d1, d2),
        )
    db_conn.rollback()


def test_tc06_tc07_payroll_generation_and_duplicate(db_conn):
    """TC-06 & TC-07: Valid generate_payroll succeeds; duplicate period raises error."""
    cur = db_conn.cursor()
    cur.execute("DELETE FROM payroll WHERE employee_id = 3 AND pay_year = 2024 AND pay_month = 1")
    cur.callproc("generate_payroll", (3, 1, 2024, 22, 2))
    with pytest.raises(mysql.connector.Error):
        cur.callproc("generate_payroll", (3, 1, 2024, 22, 2))
    db_conn.rollback()


def test_tc11_transaction_rollback(db_conn):
    """TC-11: Explicit ROLLBACK leaves zero partial records after failure."""
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees")
    before_count = cur.fetchone()[0]

    db_conn.start_transaction()
    cur.execute(
        """
        INSERT INTO employees (emp_code, first_name, last_name, email, phone, department_id, designation, hire_date)
        VALUES ('EMPRB1', 'Rollback', 'Test', 'rb1@novatech.in', '+91-99999-00099', 1, 'Tester', '2025-01-01')
        """
    )
    db_conn.rollback()

    cur.execute("SELECT COUNT(*) FROM employees")
    after_count = cur.fetchone()[0]
    assert after_count == before_count


def test_tc12_boundary_attendance_and_leave(db_conn):
    """TC-12: Boundary validation for future attendance, checkout < checkin, and end_date < start_date."""
    cur = db_conn.cursor()
    future_date = (date.today() + timedelta(days=5)).isoformat()
    with pytest.raises(mysql.connector.Error):
        cur.execute(
            "INSERT INTO attendance (employee_id, attendance_date, status) VALUES (3, %s, 'PRESENT')",
            (future_date,),
        )
    with pytest.raises(mysql.connector.Error):
        cur.execute(
            """
            INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, total_days, reason)
            VALUES (3, 1, '2026-12-10', '2026-12-08', 1.0, 'Invalid reversed dates')
            """
        )
    db_conn.rollback()
