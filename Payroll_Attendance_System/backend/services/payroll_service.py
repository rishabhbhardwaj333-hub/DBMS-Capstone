"""Salary management and monthly payroll processing services."""

from backend.database import call_proc, query_all, query_one, transaction


def list_salaries(employee_id: int = None, current_only: bool = False):
    """Return salary structures with computed gross via calculate_salary()."""
    sql = [
        "SELECT s.salary_id, s.employee_id, e.emp_code,",
        "       CONCAT(e.first_name, ' ', e.last_name) AS employee_name,",
        "       d.department_name, s.basic_salary, s.hra, s.da, s.other_allowances,",
        "       calculate_salary(s.basic_salary, s.hra, s.da, s.other_allowances) AS gross_salary,",
        "       s.pf_deduction, s.professional_tax,",
        "       s.effective_from, s.effective_to, s.is_current",
        "FROM salaries s",
        "JOIN employees e ON s.employee_id = e.employee_id",
        "JOIN departments d ON e.department_id = d.department_id",
        "WHERE 1=1",
    ]
    params = []
    if employee_id is not None:
        sql.append("AND s.employee_id = %s")
        params.append(int(employee_id))
    if current_only:
        sql.append("AND s.is_current = TRUE")
    sql.append("ORDER BY e.emp_code ASC, s.effective_from DESC")
    return query_all("\n".join(sql), tuple(params))


def revise_salary(employee_id: int, basic_salary: float, hra: float, da: float,
                  other_allowances: float, pf_deduction: float,
                  professional_tax: float, effective_from: str):
    """Invoke Phase 4 transactional salary revision procedure."""
    if basic_salary <= 0:
        raise ValueError("Basic salary must be strictly positive (> 0).")
    if min(hra, da, other_allowances, pf_deduction, professional_tax) < 0:
        raise ValueError("Allowances and deductions cannot be negative.")

    call_proc(
        "sp_revise_salary_transactional",
        (
            int(employee_id),
            float(basic_salary),
            float(hra),
            float(da),
            float(other_allowances),
            float(pf_deduction),
            float(professional_tax),
            effective_from,
        ),
    )


def list_payroll(pay_month: int = None, pay_year: int = None, employee_id: int = None):
    """List generated payroll records filtered by period and/or employee."""
    sql = [
        "SELECT p.payroll_id, p.employee_id, e.emp_code,",
        "       CONCAT(e.first_name, ' ', e.last_name) AS employee_name,",
        "       d.department_name, p.pay_month, p.pay_year, p.working_days,",
        "       p.present_days, p.paid_leave_days, p.unpaid_leave_days, p.late_count,",
        "       p.basic_earned, p.allowances_earned, p.gross_salary,",
        "       p.pf_deduction, p.professional_tax, p.income_tax, p.leave_deduction,",
        "       p.total_deductions, p.net_salary, p.payment_status, p.payment_date",
        "FROM payroll p",
        "JOIN employees e ON p.employee_id = e.employee_id",
        "JOIN departments d ON e.department_id = d.department_id",
        "WHERE 1=1",
    ]
    params = []
    if pay_month:
        sql.append("AND p.pay_month = %s")
        params.append(int(pay_month))
    if pay_year:
        sql.append("AND p.pay_year = %s")
        params.append(int(pay_year))
    if employee_id is not None:
        sql.append("AND p.employee_id = %s")
        params.append(int(employee_id))

    sql.append("ORDER BY p.pay_year DESC, p.pay_month DESC, e.emp_code ASC")
    return query_all("\n".join(sql), tuple(params))


def run_monthly_payroll(pay_month: int, pay_year: int, working_days: int, generated_by: int):
    """Run Phase 2 process_monthly_payroll() stored procedure."""
    if not (1 <= pay_month <= 12):
        raise ValueError("Pay month must be between 1 and 12.")
    if not (1 <= working_days <= 31):
        raise ValueError("Working days must be between 1 and 31.")

    results = call_proc(
        "process_monthly_payroll",
        (int(pay_month), int(pay_year), int(working_days), int(generated_by)),
    )
    return results[0] if results else {"processed_employees": 0, "pay_month": pay_month, "pay_year": pay_year}


def mark_payroll_paid(pay_month: int, pay_year: int):
    """Mark all PROCESSED payroll entries for a month as PAID inside a transaction."""
    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            UPDATE payroll
            SET payment_status = 'PAID',
                payment_date = CURDATE()
            WHERE pay_year = %s AND pay_month = %s AND payment_status = 'PROCESSED'
            """,
            (int(pay_year), int(pay_month)),
        )
        return cursor.rowcount


def mark_single_payroll_paid(payroll_id: int):
    """Mark a single payroll record as PAID inside a transaction."""
    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            UPDATE payroll
            SET payment_status = 'PAID',
                payment_date = CURDATE()
            WHERE payroll_id = %s AND payment_status = 'PROCESSED'
            """,
            (int(payroll_id),),
        )
        return cursor.rowcount


def get_salary_slip(payroll_id: int):
    """Fetch complete individual salary slip details by payroll_id."""
    return query_one(
        """
        SELECT p.payroll_id, p.employee_id, p.pay_month, p.pay_year, p.working_days,
               p.present_days, p.paid_leave_days, p.unpaid_leave_days, p.late_count,
               e.emp_code, CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               e.email, e.phone, e.designation, e.hire_date, d.department_name,
               s.basic_salary, s.hra, s.da, s.other_allowances,
               p.basic_earned, p.allowances_earned, p.gross_salary,
               p.pf_deduction, p.professional_tax, p.income_tax, p.leave_deduction,
               p.total_deductions, p.net_salary, p.payment_status, p.payment_date,
               p.generated_at
        FROM payroll p
        JOIN employees e   ON p.employee_id = e.employee_id
        JOIN departments d ON e.department_id = d.department_id
        JOIN salaries s    ON p.salary_id = s.salary_id
        WHERE p.payroll_id = %s
        """,
        (int(payroll_id),),
    )
