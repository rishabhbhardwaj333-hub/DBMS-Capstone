-- =============================================================================
-- PHASE 3: QUERY & REPORT DEVELOPMENT
-- Database: payroll_attendance_db
-- All 6 required reports run directly against the Phase 1/2 schema and data.
-- =============================================================================

USE payroll_attendance_db;

-- Default parameters for standalone execution in MySQL CLI / Workbench
SET @target_month       = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH));
SET @target_year        = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH));
SET @target_employee_id = 3;

-- -----------------------------------------------------------------------------
-- REPORT 1: Monthly Attendance Summary
-- Columns: emp_code, employee_name, department_name, working_days,
--          present_days, absent_days, leave_days, late_marks, attendance_percentage
-- -----------------------------------------------------------------------------
SELECT
    e.emp_code,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    d.department_name,
    COUNT(a.attendance_id) AS working_days,
    SUM(CASE
        WHEN a.status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
        WHEN a.status = 'HALF_DAY' THEN 0.5
        ELSE 0.0
    END) AS present_days,
    SUM(CASE WHEN a.status = 'ABSENT' THEN 1 ELSE 0 END) AS absent_days,
    SUM(CASE WHEN a.status = 'ON_LEAVE' THEN 1 ELSE 0 END) AS leave_days,
    SUM(CASE WHEN a.is_late = TRUE THEN 1 ELSE 0 END) AS late_marks,
    ROUND(
        (SUM(CASE
            WHEN a.status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
            WHEN a.status = 'HALF_DAY' THEN 0.5
            ELSE 0.0
        END) / NULLIF(COUNT(a.attendance_id), 0)) * 100.0,
        2
    ) AS attendance_percentage
FROM employees e
JOIN departments d ON e.department_id = d.department_id
LEFT JOIN attendance a
    ON a.employee_id = e.employee_id
   AND YEAR(a.attendance_date) = @target_year
   AND MONTH(a.attendance_date) = @target_month
WHERE e.employment_status IN ('ACTIVE', 'ON_LEAVE')
GROUP BY e.employee_id, e.emp_code, employee_name, d.department_name
ORDER BY e.emp_code;

-- -----------------------------------------------------------------------------
-- REPORT 2: Individual Salary Slip
-- Columns: payroll details, employee details, salary structure breakdown,
--          gross salary, income tax, deductions, and net salary
-- -----------------------------------------------------------------------------
SELECT
    p.payroll_id,
    p.pay_year,
    p.pay_month,
    e.emp_code,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.email,
    d.department_name,
    e.designation,
    p.working_days,
    p.present_days,
    p.paid_leave_days,
    p.unpaid_leave_days,
    p.late_count,
    s.basic_salary,
    s.hra,
    s.da,
    s.other_allowances,
    p.basic_earned,
    p.allowances_earned,
    p.gross_salary,
    p.pf_deduction,
    p.professional_tax,
    p.income_tax,
    p.leave_deduction,
    p.total_deductions,
    p.net_salary,
    p.payment_status,
    p.payment_date
FROM payroll p
JOIN employees e   ON p.employee_id = e.employee_id
JOIN departments d ON e.department_id = d.department_id
JOIN salaries s    ON p.salary_id = s.salary_id
WHERE p.employee_id = @target_employee_id
  AND p.pay_year = @target_year
  AND p.pay_month = @target_month;

-- -----------------------------------------------------------------------------
-- REPORT 3: Late Marks Report
-- Columns: employee_name, department_name, attendance_date, check_in_time,
--          late_minutes, total_late_marks (for the selected month)
-- -----------------------------------------------------------------------------
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
  AND a.attendance_date BETWEEN
      STR_TO_DATE(CONCAT(@target_year, '-', LPAD(@target_month, 2, '0'), '-01'), '%Y-%m-%d')
      AND LAST_DAY(STR_TO_DATE(CONCAT(@target_year, '-', LPAD(@target_month, 2, '0'), '-01'), '%Y-%m-%d'))
ORDER BY a.attendance_date DESC, a.late_minutes DESC;

-- -----------------------------------------------------------------------------
-- REPORT 4: Monthly Payroll Summary
-- Columns: pay_year, pay_month, total_employees_paid, total_gross_salary,
--          total_tax, total_deductions, total_net_payroll
-- -----------------------------------------------------------------------------
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
ORDER BY p.pay_year DESC, p.pay_month DESC;

-- -----------------------------------------------------------------------------
-- REPORT 5: Employee Attendance History
-- -----------------------------------------------------------------------------
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
WHERE a.employee_id = @target_employee_id
ORDER BY a.attendance_date DESC;

-- -----------------------------------------------------------------------------
-- REPORT 6: Leave History Report
-- -----------------------------------------------------------------------------
SELECT
    lr.leave_id,
    e.emp_code,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    d.department_name,
    lt.type_code,
    lt.type_name,
    lt.is_paid,
    lr.start_date,
    lr.end_date,
    lr.total_days,
    lr.reason,
    lr.status,
    CONCAT(app.first_name, ' ', app.last_name) AS approved_by_name,
    lr.approved_at,
    lr.applied_at
FROM leave_requests lr
JOIN employees e      ON lr.employee_id = e.employee_id
JOIN departments d    ON e.department_id = d.department_id
JOIN leave_types lt   ON lr.leave_type_id = lt.leave_type_id
LEFT JOIN employees app ON lr.approved_by = app.employee_id
ORDER BY lr.applied_at DESC, lr.leave_id DESC;
