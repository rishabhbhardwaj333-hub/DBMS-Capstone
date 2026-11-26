# Phase 3: Query Optimization & Execution Plan Report

## 1. Optimization Target

The Phase 3 reporting workload queries `attendance`, `payroll`, `leave_requests`, `employees`, and `salaries` across date ranges, boolean flags, and period keys. While Phase 1 primary/unique constraints automatically create indexes on `(employee_id, attendance_date)` and `(employee_id, pay_year, pay_month)`, reporting queries that filter first by `attendance_date` across *all* employees, by `is_late = TRUE`, or by `(pay_year, pay_month)` cannot efficiently use leading-`employee_id` composite indexes.

## 2. Indexes Added (`Phase3/indexes.sql`)

| Index Name | Table & Columns | Reports Accelerated |
|---|---|---|
| `idx_attendance_date_status` | `attendance(attendance_date, status)` | Monthly Attendance Summary, Dashboard Present/Absent Today |
| `idx_attendance_late_date` | `attendance(is_late, attendance_date, employee_id)` | Late Marks Report (Report 3) |
| `idx_payroll_period_status` | `payroll(pay_year, pay_month, payment_status)` | Monthly Payroll Summary (Report 4), Period Payslips |
| `idx_leave_emp_status_dates` | `leave_requests(employee_id, status, start_date, end_date)` | Leave Overlap Trigger, Leave History Report (Report 6) |
| `idx_emp_dept_status` | `employees(department_id, employment_status)` | Employee Filtering & Active Headcount |
| `idx_salary_emp_current` | `salaries(employee_id, is_current, effective_from)` | Active Salary Lookup during Payroll Generation |

---

## 3. Target Query for Execution Plan Analysis (Report 3: Late Marks Report)

```sql
EXPLAIN
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
  AND a.attendance_date BETWEEN @period_start AND @period_end
ORDER BY a.attendance_date DESC, a.late_minutes DESC;
```

### Why `idx_attendance_late_date (is_late, attendance_date, employee_id)` Improves the Plan

1. **Before Indexing:**
   - Because `uq_attendance_emp_date` has `employee_id` as its leading column, filtering across *all* employees on `a.is_late = TRUE AND a.attendance_date BETWEEN ...` forces the MySQL optimizer to perform a full table scan (`type = ALL`) or full index scan on `attendance`, examining every attendance row across all months and filtering `is_late` + `attendance_date` via `Using where`.
2. **After Indexing (`idx_attendance_late_date`):**
   - Leading equality predicate `a.is_late = TRUE` narrows the B-Tree immediately to only late rows (~10–12% of records).
   - Second key `a.attendance_date BETWEEN ...` performs a tight B-Tree range scan (`type = range`) restricted strictly to the target month instead of scanning all historical months.
   - Including `employee_id` as the third index key allows the join to `employees` and the `PARTITION BY a.employee_id` window grouping to read `employee_id` directly from the index leaf.
3. **Note on Report 1 (`YEAR(a.attendance_date) = ...` vs SARGable Date Range):**
   - Wrapping `attendance_date` in `YEAR()`/`MONTH()` prevents B-Tree range usage. Both `Phase3/reports.sql` (Report 3) and the Python `report_service.py` use SARGable `BETWEEN period_start AND period_end` bounds so MySQL 8.0 utilizes `idx_attendance_date_status` and `idx_attendance_late_date`.

---

## 4. Live `EXPLAIN` Verification Status

> **Status:** `NOT YET EXECUTED` — Requires running `Phase2` + `Phase3/indexes.sql` against the local `MySQL80` server with configured credentials.  
> Once `MYSQL_PASSWORD` is configured in `.env`, run `python tests/run_explain_comparison.py` to capture actual before-and-after `EXPLAIN` rows and update this section with verbatim output.
