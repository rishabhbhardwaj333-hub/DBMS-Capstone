"""HR / Admin routes enforcing server-side HR_ADMIN authorization."""

import csv
import io
from datetime import date
from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error as MySQLError

from backend.auth import role_required
from backend.services import (
    attendance_service,
    employee_service,
    leave_service,
    payroll_service,
    report_service,
    user_service,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _clean_db_error(exc: Exception) -> str:
    if isinstance(exc, MySQLError):
        return exc.msg or str(exc)
    return str(exc)


@admin_bp.route("/dashboard")
@role_required("HR_ADMIN")
def dashboard():
    metrics = report_service.get_admin_dashboard_metrics()
    return render_template("admin/dashboard.html", metrics=metrics, active_page="dashboard")


# ---------------------------------------------------------------------------
# Employee Management
# ---------------------------------------------------------------------------
@admin_bp.route("/employees")
@role_required("HR_ADMIN")
def employees():
    search = request.args.get("q", "")
    dept_id = request.args.get("department_id", "")
    status = request.args.get("status", "")
    emp_list = employee_service.list_employees(search=search, department_id=dept_id, status=status)
    departments = employee_service.list_departments()
    return render_template(
        "admin/employees.html",
        employees=emp_list,
        departments=departments,
        filters={"q": search, "department_id": dept_id, "status": status},
        active_page="employees",
    )


@admin_bp.route("/employees/create", methods=["POST"])
@role_required("HR_ADMIN")
def create_employee():
    try:
        employee_service.create_employee_with_account(request.form)
        flash("Employee created successfully.", "success")
    except (ValueError, MySQLError) as exc:
        flash(f"Could not create employee: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.employees"))


@admin_bp.route("/employees/<int:emp_id>/update", methods=["POST"])
@role_required("HR_ADMIN")
def update_employee(emp_id):
    try:
        employee_service.update_employee(emp_id, request.form)
        flash("Employee details updated.", "success")
    except (ValueError, MySQLError) as exc:
        flash(f"Could not update employee: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.employees"))


@admin_bp.route("/employees/<int:emp_id>/deactivate", methods=["POST"])
@role_required("HR_ADMIN")
def deactivate_employee(emp_id):
    if emp_id == session.get("employee_id"):
        flash("You cannot deactivate your own employee record while signed in.", "warning")
        return redirect(url_for("admin.employees"))
    try:
        employee_service.deactivate_employee(emp_id)
        flash("Employee deactivated and login access disabled.", "info")
    except MySQLError as exc:
        flash(f"Deactivation failed: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.employees"))


# ---------------------------------------------------------------------------
# Attendance Management
# ---------------------------------------------------------------------------
@admin_bp.route("/attendance")
@role_required("HR_ADMIN")
def attendance():
    att_date = request.args.get("date", "")
    employee_id = request.args.get("employee_id", "")
    status = request.args.get("status", "")
    records = attendance_service.list_attendance(att_date=att_date, employee_id=employee_id, status=status)
    emp_list = employee_service.list_employees()
    return render_template(
        "admin/attendance.html",
        records=records,
        employees=emp_list,
        today_iso=date.today().isoformat(),
        filters={"date": att_date, "employee_id": employee_id, "status": status},
        active_page="attendance",
    )


@admin_bp.route("/attendance/record", methods=["POST"])
@role_required("HR_ADMIN")
def record_attendance():
    try:
        attendance_service.record_attendance(
            employee_id=int(request.form["employee_id"]),
            att_date=request.form["attendance_date"],
            status=request.form["status"],
            check_in=request.form.get("check_in_time", ""),
            check_out=request.form.get("check_out_time", ""),
            remarks=request.form.get("remarks", ""),
        )
        flash("Attendance recorded successfully.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(f"Attendance validation error: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.attendance"))


@admin_bp.route("/attendance/<int:att_id>/update", methods=["POST"])
@role_required("HR_ADMIN")
def update_attendance(att_id):
    try:
        attendance_service.update_attendance(
            attendance_id=att_id,
            status=request.form["status"],
            check_in=request.form.get("check_in_time", ""),
            check_out=request.form.get("check_out_time", ""),
            remarks=request.form.get("remarks", ""),
        )
        flash("Attendance entry updated.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(f"Could not update attendance: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.attendance"))


# ---------------------------------------------------------------------------
# Leave Management
# ---------------------------------------------------------------------------
@admin_bp.route("/leaves")
@role_required("HR_ADMIN")
def leaves():
    status = request.args.get("status", "")
    leave_rows = leave_service.list_leave_requests(status=status)
    return render_template(
        "admin/leaves.html",
        leaves=leave_rows,
        selected_status=status,
        active_page="leaves",
    )


@admin_bp.route("/leaves/<int:leave_id>/decision", methods=["POST"])
@role_required("HR_ADMIN")
def leave_decision(leave_id):
    decision = request.form.get("decision", "").upper()
    try:
        leave_service.process_leave_decision(
            leave_id=leave_id,
            approver_id=session["employee_id"],
            decision=decision,
        )
        flash(f"Leave request #{leave_id} marked as {decision}.", "success")
    except (ValueError, MySQLError) as exc:
        flash(f"Leave decision blocked: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.leaves"))


# ---------------------------------------------------------------------------
# Salary Management
# ---------------------------------------------------------------------------
@admin_bp.route("/salaries")
@role_required("HR_ADMIN")
def salaries():
    show_all = request.args.get("history") == "1"
    emp_filter = request.args.get("employee_id", "")
    emp_id = int(emp_filter) if emp_filter.isdigit() else None
    salary_rows = payroll_service.list_salaries(employee_id=emp_id, current_only=not show_all)
    emp_list = employee_service.list_employees()
    return render_template(
        "admin/salaries.html",
        salaries=salary_rows,
        employees=emp_list,
        show_all=show_all,
        selected_emp=emp_filter,
        today_iso=date.today().isoformat(),
        active_page="salaries",
    )


@admin_bp.route("/salaries/revise", methods=["POST"])
@role_required("HR_ADMIN")
def revise_salary():
    try:
        payroll_service.revise_salary(
            employee_id=int(request.form["employee_id"]),
            basic_salary=float(request.form["basic_salary"]),
            hra=float(request.form.get("hra") or 0),
            da=float(request.form.get("da") or 0),
            other_allowances=float(request.form.get("other_allowances") or 0),
            pf_deduction=float(request.form.get("pf_deduction") or 0),
            professional_tax=float(request.form.get("professional_tax") or 200),
            effective_from=request.form["effective_from"],
        )
        flash("Salary revision saved atomically (revision history preserved).", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(f"Salary update rejected: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.salaries"))


# ---------------------------------------------------------------------------
# Payroll Processing
# ---------------------------------------------------------------------------
@admin_bp.route("/payroll")
@role_required("HR_ADMIN")
def payroll():
    today = date.today()
    month_str = request.args.get("month", "")
    year_str = request.args.get("year", "")
    pay_month = int(month_str) if month_str.isdigit() else None
    pay_year = int(year_str) if year_str.isdigit() else None
    rows = payroll_service.list_payroll(pay_month=pay_month, pay_year=pay_year)
    return render_template(
        "admin/payroll.html",
        payroll_rows=rows,
        default_month=pay_month or today.month,
        default_year=pay_year or today.year,
        filter_month=month_str,
        filter_year=year_str,
        active_page="payroll",
    )


@admin_bp.route("/payroll/process", methods=["POST"])
@role_required("HR_ADMIN")
def process_payroll():
    try:
        pay_month = int(request.form["pay_month"])
        pay_year = int(request.form["pay_year"])
        working_days = int(request.form.get("working_days") or 22)
        summary = payroll_service.run_monthly_payroll(
            pay_month=pay_month,
            pay_year=pay_year,
            working_days=working_days,
            generated_by=session["employee_id"],
        )
        count = summary.get("processed_employees", 0)
        if count == 0:
            flash(f"No new eligible payroll records to process for {pay_month:02d}/{pay_year}.", "info")
        else:
            flash(f"Processed payroll for {count} employees for {pay_month:02d}/{pay_year}.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(f"Payroll processing rolled back: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.payroll"))


@admin_bp.route("/payroll/mark-paid", methods=["POST"])
@role_required("HR_ADMIN")
def mark_month_paid():
    try:
        pay_month = int(request.form["pay_month"])
        pay_year = int(request.form["pay_year"])
        updated = payroll_service.mark_payroll_paid(pay_month, pay_year)
        flash(f"Marked {updated} payroll records as PAID for {pay_month:02d}/{pay_year}.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(f"Could not mark payroll paid: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.payroll"))


@admin_bp.route("/payroll/<int:payroll_id>/mark-paid", methods=["POST"])
@role_required("HR_ADMIN")
def mark_single_paid(payroll_id):
    try:
        payroll_service.mark_single_payroll_paid(payroll_id)
        flash(f"Payroll #{payroll_id} marked as PAID.", "success")
    except MySQLError as exc:
        flash(f"Update failed: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.payroll"))


# ---------------------------------------------------------------------------
# Reports (Phase 3 Queries)
# ---------------------------------------------------------------------------
def _fetch_report_data(report_type: str, year: int, month: int, emp_id: int = None):
    if report_type == "attendance_summary":
        return report_service.report_monthly_attendance_summary(year, month)
    if report_type == "late_marks":
        return report_service.report_late_marks(year, month)
    if report_type == "payroll_summary":
        return report_service.report_monthly_payroll_summary()
    if report_type == "attendance_history":
        return report_service.report_employee_attendance_history(emp_id or 3)
    if report_type == "leave_history":
        return report_service.report_leave_history(emp_id)
    return []


@admin_bp.route("/reports")
@role_required("HR_ADMIN")
def reports():
    today = date.today()
    prev_month = 12 if today.month == 1 else today.month - 1
    prev_year = today.year - 1 if today.month == 1 else today.year

    report_type = request.args.get("type", "attendance_summary")
    year = int(request.args.get("year") or prev_year)
    month = int(request.args.get("month") or prev_month)
    emp_str = request.args.get("employee_id", "")
    emp_id = int(emp_str) if emp_str.isdigit() else None

    rows = _fetch_report_data(report_type, year, month, emp_id)
    employees = employee_service.list_employees()
    return render_template(
        "admin/reports.html",
        report_type=report_type,
        year=year,
        month=month,
        selected_emp=emp_str,
        rows=rows,
        employees=employees,
        active_page="reports",
    )


@admin_bp.route("/reports/export")
@role_required("HR_ADMIN")
def export_report_csv():
    today = date.today()
    report_type = request.args.get("type", "attendance_summary")
    year = int(request.args.get("year") or today.year)
    month = int(request.args.get("month") or today.month)
    emp_str = request.args.get("employee_id", "")
    emp_id = int(emp_str) if emp_str.isdigit() else None

    rows = _fetch_report_data(report_type, year, month, emp_id)
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        buf.write("No records found\n")

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_{year}_{month:02d}.csv"},
    )


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
@role_required("HR_ADMIN")
def users():
    all_users = user_service.list_users()
    unassigned = user_service.list_employees_without_account()
    return render_template(
        "admin/users.html",
        users=all_users,
        unassigned_employees=unassigned,
        active_page="users",
    )


@admin_bp.route("/users/create", methods=["POST"])
@role_required("HR_ADMIN")
def create_user():
    try:
        user_service.create_user_account(
            employee_id=int(request.form["employee_id"]),
            username=request.form["username"],
            raw_password=request.form["password"],
            role=request.form["role"],
        )
        flash("User account created successfully.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(f"Could not create user account: {_clean_db_error(exc)}", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@role_required("HR_ADMIN")
def toggle_user(user_id):
    try:
        user_service.toggle_user_active(user_id, session["user_id"])
        flash("User account status updated.", "success")
    except (ValueError, MySQLError) as exc:
        flash(_clean_db_error(exc), "warning")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@role_required("HR_ADMIN")
def change_user_role(user_id):
    try:
        user_service.update_user_role(user_id, request.form["role"], session["user_id"])
        flash("User role updated.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(_clean_db_error(exc), "warning")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@role_required("HR_ADMIN")
def reset_password(user_id):
    try:
        user_service.reset_user_password(user_id, request.form["new_password"])
        flash("Password updated securely.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        flash(_clean_db_error(exc), "danger")
    return redirect(url_for("admin.users"))
