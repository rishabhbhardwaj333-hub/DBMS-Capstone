# Phase 1: Relational Schema & Constraints

> **Database:** `payroll_attendance_db` (MySQL 8.0+, `InnoDB`, `utf8mb4_unicode_ci`)  
> **Permanence Rule:** This schema is the permanent foundation for Phases 2–5. Table names, column names, types, and integrity constraints remain unchanged across all subsequent phases.

---

## 1. Relational Schema Notation

1. `departments`(**<u>department_id</u>**, *department_code*, *department_name*, description, created_at)
2. `employees`(**<u>employee_id</u>**, *emp_code*, first_name, last_name, *email*, phone, *department_id* → `departments(department_id)`, designation, hire_date, employment_status, created_at, updated_at)
3. `user_accounts`(**<u>user_id</u>**, *employee_id* → `employees(employee_id)`, *username*, password_hash, role, is_active, last_login_at, created_at, updated_at)
4. `attendance`(**<u>attendance_id</u>**, *employee_id* → `employees(employee_id)`, *attendance_date*, check_in_time, check_out_time, status, is_late, late_minutes, work_hours, remarks, created_at, updated_at)  
   - Composite Unique Key: `(employee_id, attendance_date)`
5. `leave_types`(**<u>leave_type_id</u>**, *type_code*, *type_name*, is_paid, max_days_per_year, description)
6. `leave_requests`(**<u>leave_id</u>**, *employee_id* → `employees(employee_id)`, *leave_type_id* → `leave_types(leave_type_id)`, start_date, end_date, total_days, reason, status, *approved_by* → `employees(employee_id)`, approved_at, applied_at, updated_at)
7. `salaries`(**<u>salary_id</u>**, *employee_id* → `employees(employee_id)`, basic_salary, hra, da, other_allowances, pf_deduction, professional_tax, *effective_from*, effective_to, is_current, created_at, updated_at)  
   - Composite Unique Key: `(employee_id, effective_from)`
8. `payroll`(**<u>payroll_id</u>**, *employee_id* → `employees(employee_id)`, *salary_id* → `salaries(salary_id)`, *pay_month*, *pay_year*, working_days, present_days, paid_leave_days, unpaid_leave_days, late_count, basic_earned, allowances_earned, gross_salary *(GENERATED)*, pf_deduction, professional_tax, income_tax, leave_deduction, total_deductions *(GENERATED)*, net_salary *(GENERATED)*, payment_status, payment_date, *generated_by* → `employees(employee_id)`, generated_at, updated_at)  
   - Composite Unique Key: `(employee_id, pay_year, pay_month)`

---

## 2. Keys, Referential Integrity & Constraints

### Primary Keys
All 8 tables use `INT AUTO_INCREMENT` surrogate primary keys (`department_id`, `employee_id`, `user_id`, `attendance_id`, `leave_type_id`, `leave_id`, `salary_id`, `payroll_id`).

### Foreign Keys & Actions
| Child Table | FK Column | Parent Table & Column | `ON DELETE` | `ON UPDATE` |
|---|---|---|---|---|
| `employees` | `department_id` | `departments(department_id)` | `RESTRICT` | `CASCADE` |
| `user_accounts` | `employee_id` | `employees(employee_id)` | `CASCADE` | `CASCADE` |
| `attendance` | `employee_id` | `employees(employee_id)` | `CASCADE` | `CASCADE` |
| `leave_requests` | `employee_id` | `employees(employee_id)` | `CASCADE` | `CASCADE` |
| `leave_requests` | `leave_type_id` | `leave_types(leave_type_id)` | `RESTRICT` | `CASCADE` |
| `leave_requests` | `approved_by` | `employees(employee_id)` | `SET NULL` | `CASCADE` |
| `salaries` | `employee_id` | `employees(employee_id)` | `CASCADE` | `CASCADE` |
| `payroll` | `employee_id` | `employees(employee_id)` | `RESTRICT` | `CASCADE` |
| `payroll` | `salary_id` | `salaries(salary_id)` | `RESTRICT` | `CASCADE` |
| `payroll` | `generated_by` | `employees(employee_id)` | `SET NULL` | `CASCADE` |

### Unique Constraints
- `departments`: `uq_dept_code (department_code)`, `uq_dept_name (department_name)`
- `employees`: `uq_emp_code (emp_code)`, `uq_emp_email (email)`
- `user_accounts`: `uq_user_employee (employee_id)`, `uq_user_username (username)`
- `attendance`: `uq_attendance_emp_date (employee_id, attendance_date)` *(prevents duplicate attendance for an employee on the same date)*
- `leave_types`: `uq_leave_type_code (type_code)`, `uq_leave_type_name (type_name)`
- `salaries`: `uq_salary_emp_effective (employee_id, effective_from)` *(preserves revision history per effective date)*
- `payroll`: `uq_payroll_emp_period (employee_id, pay_year, pay_month)` *(prevents duplicate payroll generation for the same employee and month)*

### Check Constraints
- `attendance`:
  - `chk_attendance_checkout`: `check_out_time IS NULL OR check_in_time IS NULL OR check_out_time >= check_in_time`
  - `chk_attendance_work_hours`: `work_hours >= 0.00 AND work_hours <= 24.00`
- `leave_requests`:
  - `chk_leave_dates`: `end_date >= start_date`
  - `chk_leave_total_days`: `total_days > 0.0`
- `salaries`:
  - `chk_salary_basic`: `basic_salary > 0.00` *(prevents negative or zero salary)*
  - `chk_salary_nonneg`: `hra >= 0.00 AND da >= 0.00 AND other_allowances >= 0.00 AND pf_deduction >= 0.00 AND professional_tax >= 0.00`
  - `chk_salary_dates`: `effective_to IS NULL OR effective_to >= effective_from`
- `payroll`:
  - `chk_payroll_period`: `pay_month BETWEEN 1 AND 12 AND pay_year BETWEEN 2000 AND 2100`
  - `chk_payroll_days`: `working_days BETWEEN 1 AND 31 AND present_days >= 0.0 AND paid_leave_days >= 0.0 AND unpaid_leave_days >= 0.0`
  - `chk_payroll_amounts`: `basic_earned >= 0.00 AND allowances_earned >= 0.00 AND pf_deduction >= 0.00 AND professional_tax >= 0.00 AND income_tax >= 0.00 AND leave_deduction >= 0.00`
  - `chk_payroll_net_nonneg`: `(basic_earned + allowances_earned) >= (pf_deduction + professional_tax + income_tax + leave_deduction)`
