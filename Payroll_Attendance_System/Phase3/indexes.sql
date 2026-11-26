-- =============================================================================
-- PHASE 3: PERFORMANCE INDEXES FOR REPORTING & FILTERING
-- Database: payroll_attendance_db
-- Adds secondary B-Tree composite indexes on high-frequency report columns
-- without altering any Phase 1 tables or columns.
-- =============================================================================

USE payroll_attendance_db;

-- 1. Speeds up daily attendance dashboard counts & date-range monthly summaries
CREATE INDEX idx_attendance_date_status
    ON attendance (attendance_date, status);

-- 2. Speeds up the Late Marks Report (is_late filter + attendance_date range)
CREATE INDEX idx_attendance_late_date
    ON attendance (is_late, attendance_date, employee_id);

-- 3. Speeds up Monthly Payroll Summary & payment status filtering
CREATE INDEX idx_payroll_period_status
    ON payroll (pay_year, pay_month, payment_status);

-- 4. Speeds up Leave Overlap Checks & Employee Leave History queries
CREATE INDEX idx_leave_emp_status_dates
    ON leave_requests (employee_id, status, start_date, end_date);

-- 5. Speeds up Department-filtered employee listings & active employee counts
CREATE INDEX idx_emp_dept_status
    ON employees (department_id, employment_status);

-- 6. Speeds up active salary lookup during payroll generation
CREATE INDEX idx_salary_emp_current
    ON salaries (employee_id, is_current, effective_from);
