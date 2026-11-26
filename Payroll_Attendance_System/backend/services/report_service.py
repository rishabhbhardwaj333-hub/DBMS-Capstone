"""Reporting and dashboard analytics backed by Phase 3 SQL queries."""

from calendar import monthrange
from datetime import date
from backend.database import query_all, query_one


def get_admin_dashboard_metrics():
    """Return live KPI counts and chart datasets from MySQL for the Admin Dashboard."""
    today = date.today()
    headcount = query_one(
        "SELECT COUNT(*) AS total FROM employees WHERE employment_status IN ('ACTIVE', 'ON_LEAVE')"
    )
    today_att = query_one(
        """
        SELECT
            IFNULL(SUM(CASE WHEN status IN ('PRESENT', 'WORK_FROM_HOME', 'HALF_DAY') THEN 1 ELSE 0 END), 0) AS present_today,
            IFNULL(SUM(CASE WHEN status = 'ABSENT' THEN 1 ELSE 0 END), 0) AS absent_today,
            IFNULL(SUM(CASE WHEN status = 'ON_LEAVE' THEN 1 ELSE 0 END), 0) AS on_leave_today
        FROM attendance
        WHERE attendance_date = CURDATE()
        """
    )
    pending_leaves = query_one(
        "SELECT COUNT(*) AS pending_count FROM leave_requests WHERE status = 'PENDING'"
    )

    latest_period = query_one(
        """
        SELECT pay_year, pay_month,
               IFNULL(SUM(net_salary), 0.00) AS total_net,
               IFNULL(SUM(gross_salary), 0.00) AS total_gross
        FROM payroll
        WHERE payment_status <> 'CANCELLED'
        GROUP BY pay_year, pay_month
        ORDER BY pay_year DESC, pay_month DESC
        LIMIT 1
        """
    )

    month_att_pct = query_one(
        """
        SELECT ROUND(
            (IFNULL(SUM(CASE
                WHEN status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
                WHEN status = 'HALF_DAY' THEN 0.5
                ELSE 0.0
            END), 0.0) / NULLIF(COUNT(*), 0)) * 100.0,
            1
        ) AS pct
        FROM attendance
        WHERE attendance_date BETWEEN DATE_FORMAT(CURDATE(), '%Y-%m-01') AND CURDATE()
        """
    )

    # Chart 1: Payroll expenditure by month
    payroll_trend = query_all(
        """
        SELECT pay_year, pay_month,
               ROUND(SUM(gross_salary), 2) AS gross_total,
               ROUND(SUM(total_deductions), 2) AS deduction_total,
               ROUND(SUM(net_salary), 2) AS net_total
        FROM payroll
        WHERE payment_status <> 'CANCELLED'
        GROUP BY pay_year, pay_month
        ORDER BY pay_year ASC, pay_month ASC
        LIMIT 6
        """
    )

    # Chart 2: Attendance status distribution for current month (or latest month with data)
    att_breakdown = query_all(
        """
        SELECT status, COUNT(*) AS total
        FROM attendance
        WHERE attendance_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY status
        ORDER BY total DESC
        """
    )

    recent_leaves = query_all(
        """
        SELECT lr.leave_id, CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               lt.type_code, lr.start_date, lr.end_date, lr.total_days, lr.status
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.employee_id
        JOIN leave_types lt ON lr.leave_type_id = lt.leave_type_id
        ORDER BY lr.applied_at DESC
        LIMIT 5
        """
    )

    return {
        "total_employees": headcount["total"] if headcount else 0,
        "present_today": int(today_att["present_today"]) if today_att else 0,
        "absent_today": int(today_att["absent_today"]) if today_att else 0,
        "on_leave_today": int(today_att["on_leave_today"]) if today_att else 0,
        "pending_leaves": pending_leaves["pending_count"] if pending_leaves else 0,
        "current_month_payroll": float(latest_period["total_net"]) if latest_period else 0.0,
        "latest_payroll_label": (
            f"{latest_period['pay_month']:02d}/{latest_period['pay_year']}"
            if latest_period else f"{today.month:02d}/{today.year}"
        ),
        "attendance_pct": float(month_att_pct["pct"] or 0.0) if month_att_pct else 0.0,
        "payroll_trend": payroll_trend,
        "att_breakdown": att_breakdown,
        "recent_leaves": recent_leaves,
    }


def _month_bounds(year: int, month: int):
    last_day = monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def report_monthly_attendance_summary(year: int, month: int):
    """Phase 3 Report 1: Monthly Attendance Summary."""
    start_d, end_d = _month_bounds(year, month)
    return query_all(
        """
        SELECT
            e.emp_code,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            d.department_name,
            COUNT(a.attendance_id) AS working_days,
            IFNULL(SUM(CASE
                WHEN a.status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
                WHEN a.status = 'HALF_DAY' THEN 0.5
                ELSE 0.0
            END), 0.0) AS present_days,
            IFNULL(SUM(CASE WHEN a.status = 'ABSENT' THEN 1 ELSE 0 END), 0) AS absent_days,
            IFNULL(SUM(CASE WHEN a.status = 'ON_LEAVE' THEN 1 ELSE 0 END), 0) AS leave_days,
            IFNULL(SUM(CASE WHEN a.is_late = TRUE THEN 1 ELSE 0 END), 0) AS late_marks,
            IFNULL(ROUND(
                (SUM(CASE
                    WHEN a.status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
                    WHEN a.status = 'HALF_DAY' THEN 0.5
                    ELSE 0.0
                END) / NULLIF(COUNT(a.attendance_id), 0)) * 100.0,
                2
            ), 0.00) AS attendance_percentage
        FROM employees e
        JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN attendance a
            ON a.employee_id = e.employee_id
           AND a.attendance_date BETWEEN %s AND %s
        WHERE e.employment_status IN ('ACTIVE', 'ON_LEAVE')
        GROUP BY e.employee_id, e.emp_code, employee_name, d.department_name
        ORDER BY e.emp_code
        """,
        (start_d, end_d),
    )


def report_late_marks(year: int, month: int):
    """Phase 3 Report 3: Late Marks Report using SARGable date bounds & idx_attendance_late_date."""
    start_d, end_d = _month_bounds(year, month)
    return query_all(
        """
        SELECT
            e.emp_code,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            d.department_name,
            a.attendance_date,
            a.check_in_time,
            a.late_minutes,
            COUNT(*) OVER (PARTITION BY a.employee_id) AS total_late_marks
        FROM attendance a
        JOIN employees e   ON a.employee_id = e.employee_id
        JOIN departments d ON e.department_id = d.department_id
        WHERE a.is_late = TRUE
          AND a.attendance_date BETWEEN %s AND %s
        ORDER BY a.attendance_date DESC, a.late_minutes DESC
        """,
        (start_d, end_d),
    )


def report_monthly_payroll_summary():
    """Phase 3 Report 4: Monthly Payroll Summary."""
    return query_all(
        """
        SELECT
            p.pay_year,
            p.pay_month,
            COUNT(p.payroll_id) AS total_employees_processed,
            SUM(CASE WHEN p.payment_status = 'PAID' THEN 1 ELSE 0 END) AS total_employees_paid,
            ROUND(SUM(p.gross_salary), 2) AS total_gross_salary,
            ROUND(SUM(p.income_tax), 2) AS total_income_tax,
            ROUND(SUM(p.total_deductions), 2) AS total_deductions,
            ROUND(SUM(p.net_salary), 2) AS total_net_payroll
        FROM payroll p
        WHERE p.payment_status <> 'CANCELLED'
        GROUP BY p.pay_year, p.pay_month
        ORDER BY p.pay_year DESC, p.pay_month DESC
        """
    )


def report_employee_attendance_history(employee_id: int):
    """Phase 3 Report 5: Employee Attendance History."""
    return query_all(
        """
        SELECT
            e.emp_code,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            a.attendance_date,
            a.check_in_time,
            a.check_out_time,
            a.status,
            a.is_late,
            a.late_minutes,
            a.work_hours,
            a.remarks
        FROM attendance a
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE a.employee_id = %s
        ORDER BY a.attendance_date DESC
        LIMIT 120
        """,
        (int(employee_id),),
    )


def report_leave_history(employee_id: int = None):
    """Phase 3 Report 6: Leave History Report."""
    sql = [
        "SELECT lr.leave_id, e.emp_code,",
        "       CONCAT(e.first_name, ' ', e.last_name) AS employee_name,",
        "       d.department_name, lt.type_code, lt.type_name, lt.is_paid,",
        "       lr.start_date, lr.end_date, lr.total_days, lr.reason, lr.status,",
        "       CONCAT(app.first_name, ' ', app.last_name) AS approved_by_name,",
        "       lr.approved_at, lr.applied_at",
        "FROM leave_requests lr",
        "JOIN employees e      ON lr.employee_id = e.employee_id",
        "JOIN departments d    ON e.department_id = d.department_id",
        "JOIN leave_types lt   ON lr.leave_type_id = lt.leave_type_id",
        "LEFT JOIN employees app ON lr.approved_by = app.employee_id",
    ]
    params = []
    if employee_id is not None:
        sql.append("WHERE lr.employee_id = %s")
        params.append(int(employee_id))
    sql.append("ORDER BY lr.applied_at DESC, lr.leave_id DESC")
    return query_all("\n".join(sql), tuple(params))
