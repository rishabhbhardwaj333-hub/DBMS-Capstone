"""Employee self-service routes & strict ownership-checked salary slip route."""

from datetime import date, datetime
from flask import Blueprint, Response, abort, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error as MySQLError

from backend.auth import login_required
from backend.services import (
    attendance_service,
    employee_service,
    leave_service,
    payroll_service,
)

employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/employee/dashboard")
@login_required
def dashboard():
    emp_id = session["employee_id"]
    today = date.today()
    profile = employee_service.get_employee_by_id(emp_id)
    att_summary = attendance_service.get_employee_attendance_summary(emp_id, today.month, today.year)
    recent_att = attendance_service.get_employee_attendance_history(emp_id)[:10]
    balances = leave_service.get_employee_leave_balances(emp_id, today.year)
    leave_rows = leave_service.list_leave_requests(employee_id=emp_id)[:5]
    salaries = payroll_service.list_salaries(employee_id=emp_id)
    payslips = payroll_service.list_payroll(employee_id=emp_id)
    return render_template(
        "employee/dashboard.html",
        profile=profile,
        att_summary=att_summary,
        recent_att=recent_att,
        balances=balances,
        leaves=leave_rows,
        salaries=salaries,
        payslips=payslips,
        active_page="emp_dashboard",
    )


@employee_bp.route("/employee/attendance")
@login_required
def attendance():
    emp_id = session["employee_id"]
    today = date.today()
    month_str = request.args.get("month", "")
    year_str = request.args.get("year", "")
    month = int(month_str) if month_str.isdigit() else None
    year = int(year_str) if year_str.isdigit() else None

    history = attendance_service.get_employee_attendance_history(emp_id, month=month, year=year)
    summary = attendance_service.get_employee_attendance_summary(
        emp_id, month=month or today.month, year=year or today.year
    )
    return render_template(
        "employee/attendance.html",
        history=history,
        summary=summary,
        filter_month=month_str,
        filter_year=year_str,
        active_page="emp_attendance",
    )


@employee_bp.route("/employee/leaves")
@login_required
def leaves():
    emp_id = session["employee_id"]
    balances = leave_service.get_employee_leave_balances(emp_id)
    leave_types = leave_service.list_leave_types()
    leave_rows = leave_service.list_leave_requests(employee_id=emp_id)
    return render_template(
        "employee/leaves.html",
        balances=balances,
        leave_types=leave_types,
        leaves=leave_rows,
        today_iso=date.today().isoformat(),
        active_page="emp_leaves",
    )


@employee_bp.route("/employee/leaves/apply", methods=["POST"])
@login_required
def apply_leave():
    # Strict IDOR defense: always bind to session['employee_id'], ignoring form employee_id
    emp_id = session["employee_id"]
    try:
        start_str = request.form["start_date"]
        end_str = request.form["end_date"]
        start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_d = datetime.strptime(end_str, "%Y-%m-%d").date()
        if end_d < start_d:
            raise ValueError("End date cannot be earlier than start date.")

        span_days = float((end_d - start_d).days + 1)
        is_half = request.form.get("is_half_day") == "1"
        if is_half and span_days != 1.0:
            raise ValueError("Half-day leave must have the same start and end date.")
        total_days = 0.5 if is_half else span_days

        leave_service.submit_leave_request(
            employee_id=emp_id,
            leave_type_id=int(request.form["leave_type_id"]),
            start_date=start_str,
            end_date=end_str,
            total_days=total_days,
            reason=request.form.get("reason", ""),
        )
        flash("Leave application submitted and awaiting HR approval.", "success")
    except (ValueError, KeyError, MySQLError) as exc:
        msg = exc.msg if isinstance(exc, MySQLError) else str(exc)
        flash(f"Could not submit leave request: {msg}", "danger")
    return redirect(url_for("employee.leaves"))


@employee_bp.route("/employee/salary")
@login_required
def salary():
    emp_id = session["employee_id"]
    salaries = payroll_service.list_salaries(employee_id=emp_id)
    payslips = payroll_service.list_payroll(employee_id=emp_id)
    return render_template(
        "employee/salary.html",
        salaries=salaries,
        payslips=payslips,
        active_page="emp_salary",
    )


@employee_bp.route("/payroll/slip/<int:payroll_id>")
@login_required
def salary_slip(payroll_id):
    slip = payroll_service.get_salary_slip(payroll_id)
    if not slip:
        abort(404)

    # Strict server-side authorization: EMPLOYEE can view ONLY their own salary slip
    if session.get("role") != "HR_ADMIN" and slip["employee_id"] != session.get("employee_id"):
        abort(403)

    html = render_template("payroll_slip.html", slip=slip)
    if request.args.get("download") == "1":
        filename = f"Salary_Slip_{slip['emp_code']}_{slip['pay_year']}_{slip['pay_month']:02d}.html"
        return Response(
            html,
            mimetype="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return html
