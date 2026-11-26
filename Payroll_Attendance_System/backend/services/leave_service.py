"""Leave management service backed by MySQL stored procedure and triggers."""

from datetime import datetime
from backend.database import call_proc, query_all, transaction


def list_leave_types():
    """Return all configured leave types."""
    return query_all(
        "SELECT leave_type_id, type_code, type_name, is_paid, max_days_per_year, description "
        "FROM leave_types ORDER BY leave_type_id"
    )


def list_leave_requests(status: str = "", employee_id: int = None):
    """List leave requests with optional status and employee_id filters."""
    sql = [
        "SELECT lr.leave_id, lr.employee_id, e.emp_code,",
        "       CONCAT(e.first_name, ' ', e.last_name) AS employee_name,",
        "       d.department_name, lt.type_code, lt.type_name, lt.is_paid,",
        "       lr.start_date, lr.end_date, lr.total_days, lr.reason, lr.status,",
        "       CONCAT(app.first_name, ' ', app.last_name) AS approved_by_name,",
        "       lr.approved_at, lr.applied_at",
        "FROM leave_requests lr",
        "JOIN employees e ON lr.employee_id = e.employee_id",
        "JOIN departments d ON e.department_id = d.department_id",
        "JOIN leave_types lt ON lr.leave_type_id = lt.leave_type_id",
        "LEFT JOIN employees app ON lr.approved_by = app.employee_id",
        "WHERE 1=1",
    ]
    params = []

    if status:
        sql.append("AND lr.status = %s")
        params.append(status)
    if employee_id is not None:
        sql.append("AND lr.employee_id = %s")
        params.append(int(employee_id))

    sql.append("ORDER BY FIELD(lr.status, 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'), lr.applied_at DESC")
    return query_all("\n".join(sql), tuple(params))


def get_employee_leave_balances(employee_id: int, year: int = None):
    """Compute annual leave entitlement, used days, and remaining balance per leave type."""
    year = year or datetime.now().year
    return query_all(
        """
        SELECT
            lt.leave_type_id,
            lt.type_code,
            lt.type_name,
            lt.is_paid,
            lt.max_days_per_year,
            IFNULL(SUM(CASE
                WHEN lr.status = 'APPROVED' AND YEAR(lr.start_date) = %s THEN lr.total_days
                ELSE 0.0
            END), 0.0) AS used_days,
            CASE
                WHEN lt.max_days_per_year = 0 THEN NULL
                ELSE GREATEST(
                    lt.max_days_per_year - IFNULL(SUM(CASE
                        WHEN lr.status = 'APPROVED' AND YEAR(lr.start_date) = %s THEN lr.total_days
                        ELSE 0.0
                    END), 0.0),
                    0.0
                )
            END AS remaining_days
        FROM leave_types lt
        LEFT JOIN leave_requests lr
            ON lr.leave_type_id = lt.leave_type_id
           AND lr.employee_id = %s
        GROUP BY lt.leave_type_id, lt.type_code, lt.type_name, lt.is_paid, lt.max_days_per_year
        ORDER BY lt.leave_type_id
        """,
        (year, year, employee_id),
    )


def submit_leave_request(employee_id: int, leave_type_id: int, start_date: str,
                         end_date: str, total_days: float, reason: str):
    """Insert a PENDING leave request for the employee (validated by DB trigger)."""
    if total_days <= 0:
        raise ValueError("Total leave days must be greater than zero.")
    if not reason or not reason.strip():
        raise ValueError("Reason for leave is required.")

    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            INSERT INTO leave_requests (
                employee_id, leave_type_id, start_date, end_date, total_days, reason, status
            ) VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
            """,
            (employee_id, int(leave_type_id), start_date, end_date, float(total_days), reason.strip()),
        )
        return cursor.lastrowid


def process_leave_decision(leave_id: int, approver_id: int, decision: str):
    """Invoke Phase 2 stored procedure approve_leave() to validate overlap & decide."""
    call_proc("approve_leave", (int(leave_id), int(approver_id), decision))
