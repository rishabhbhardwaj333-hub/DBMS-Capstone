"""Attendance logging, validation, and summary queries."""

from datetime import date
from backend.database import query_all, query_one, transaction


def list_attendance(att_date: str = "", employee_id: str = "", status: str = "", limit: int = 120):
    """List attendance records filtered by date, employee, or status."""
    sql = [
        "SELECT a.attendance_id, a.employee_id, e.emp_code,",
        "       CONCAT(e.first_name, ' ', e.last_name) AS employee_name,",
        "       d.department_name, a.attendance_date, a.check_in_time, a.check_out_time,",
        "       a.status, a.is_late, a.late_minutes, a.work_hours, a.remarks",
        "FROM attendance a",
        "JOIN employees e ON a.employee_id = e.employee_id",
        "JOIN departments d ON e.department_id = d.department_id",
        "WHERE 1=1",
    ]
    params = []

    if att_date:
        sql.append("AND a.attendance_date = %s")
        params.append(att_date)
    if employee_id and str(employee_id).isdigit():
        sql.append("AND a.employee_id = %s")
        params.append(int(employee_id))
    if status:
        sql.append("AND a.status = %s")
        params.append(status)

    sql.append("ORDER BY a.attendance_date DESC, e.emp_code ASC LIMIT %s")
    params.append(int(limit))
    return query_all("\n".join(sql), tuple(params))


def record_attendance(employee_id: int, att_date: str, status: str,
                      check_in: str = "", check_out: str = "", remarks: str = ""):
    """
    Insert a daily attendance record. Database triggers compute is_late,
    late_minutes, and work_hours, and reject invalid dates or approved-leave overlaps.
    """
    cin = check_in.strip() or None
    cout = check_out.strip() or None
    if status in ("ABSENT", "ON_LEAVE"):
        cin = None
        cout = None

    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            INSERT INTO attendance (
                employee_id, attendance_date, check_in_time, check_out_time, status, remarks
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (employee_id, att_date, cin, cout, status, remarks.strip() or None),
        )
        return cursor.lastrowid


def update_attendance(attendance_id: int, status: str, check_in: str = "",
                      check_out: str = "", remarks: str = ""):
    """Update an existing attendance record (re-validated by BEFORE UPDATE trigger)."""
    cin = check_in.strip() or None
    cout = check_out.strip() or None
    if status in ("ABSENT", "ON_LEAVE"):
        cin = None
        cout = None

    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            UPDATE attendance
            SET status = %s,
                check_in_time = %s,
                check_out_time = %s,
                remarks = %s
            WHERE attendance_id = %s
            """,
            (status, cin, cout, remarks.strip() or None, attendance_id),
        )


def get_employee_attendance_history(employee_id: int, month: int = None, year: int = None):
    """Fetch attendance records strictly for the given employee_id."""
    sql = [
        "SELECT attendance_id, attendance_date, check_in_time, check_out_time,",
        "       status, is_late, late_minutes, work_hours, remarks",
        "FROM attendance",
        "WHERE employee_id = %s",
    ]
    params = [employee_id]
    if month and year:
        sql.append("AND MONTH(attendance_date) = %s AND YEAR(attendance_date) = %s")
        params.extend([month, year])
    sql.append("ORDER BY attendance_date DESC LIMIT 90")
    return query_all("\n".join(sql), tuple(params))


def get_employee_attendance_summary(employee_id: int, month: int = None, year: int = None):
    """Summarize attendance metrics for one employee in a given month/year."""
    today = date.today()
    month = month or today.month
    year = year or today.year
    return query_one(
        """
        SELECT
            COUNT(*) AS total_logged_days,
            IFNULL(SUM(CASE
                WHEN status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
                WHEN status = 'HALF_DAY' THEN 0.5
                ELSE 0.0
            END), 0.0) AS present_days,
            IFNULL(SUM(CASE WHEN status = 'ABSENT' THEN 1 ELSE 0 END), 0) AS absent_days,
            IFNULL(SUM(CASE WHEN status = 'ON_LEAVE' THEN 1 ELSE 0 END), 0) AS leave_days,
            IFNULL(SUM(CASE WHEN is_late = TRUE THEN 1 ELSE 0 END), 0) AS late_marks,
            IFNULL(ROUND(AVG(NULLIF(work_hours, 0)), 2), 0.00) AS avg_work_hours
        FROM attendance
        WHERE employee_id = %s
          AND MONTH(attendance_date) = %s
          AND YEAR(attendance_date) = %s
        """,
        (employee_id, month, year),
    )
