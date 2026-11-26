# Phase 1: Normalization Report (UNF → 1NF → 2NF → 3NF / BCNF)

## 1. Unnormalized Form (UNF)

Starting from a flat HR & Payroll workbook capturing employee master data, daily attendance logs, leave applications, salary revisions, and monthly payroll slips:

```text
HR_Payroll_UNF(
  emp_code, full_name, email, phone, dept_code, dept_name, designation, hire_date,
  username, password_hash, role,
  { (attendance_date, check_in_time, check_out_time, att_status, is_late, late_minutes, work_hours) },
  { (leave_type_code, leave_type_name, is_paid, max_days_per_year, start_date, end_date, total_days, leave_status, approved_by) },
  { (basic_salary, hra, da, other_allowances, pf_deduction, professional_tax, effective_from, effective_to, is_current) },
  { (pay_month, pay_year, working_days, present_days, paid_leave_days, unpaid_leave_days, late_count, basic_earned, allowances_earned, gross_salary, income_tax, leave_deduction, total_deductions, net_salary, payment_status) }
)
```

### Problems in UNF
- **Repeating Groups:** Nested sets of attendance, leaves, salary revisions, and payroll entries violate atomicity.
- **Composite Attributes:** `full_name` combines first and last names.
- **Insertion Anomaly:** Cannot define a new department or leave type without creating an employee or leave application.
- **Update Anomaly:** Updating a department name or leave type policy requires modifying every repeated row.
- **Deletion Anomaly:** Removing a single employee's records could erase department or leave policy definitions.

---

## 2. First Normal Form (1NF)

**Rule:** Eliminate repeating groups, split composite attributes into atomic columns, and assign primary keys to every relation.

### Decomposition into 1NF Relations
1. `employees(employee_id PK, emp_code, first_name, last_name, email, phone, dept_code, dept_name, designation, hire_date, employment_status, username, password_hash, role, is_active)`
2. `attendance(attendance_id PK, employee_id, attendance_date, check_in_time, check_out_time, status, is_late, late_minutes, work_hours, remarks)`
3. `leave_requests(leave_id PK, employee_id, type_code, type_name, is_paid, max_days_per_year, start_date, end_date, total_days, reason, status, approved_by, approved_at)`
4. `salaries(salary_id PK, employee_id, basic_salary, hra, da, other_allowances, pf_deduction, professional_tax, effective_from, effective_to, is_current)`
5. `payroll(payroll_id PK, employee_id, salary_id, pay_month, pay_year, working_days, present_days, paid_leave_days, unpaid_leave_days, late_count, basic_earned, allowances_earned, pf_deduction, professional_tax, income_tax, leave_deduction, payment_status, payment_date, generated_by)`

All attributes are now atomic and single-valued, satisfying **1NF**.

---

## 3. Second Normal Form (2NF)

**Rule:** Relation is in 1NF and every non-prime attribute is **fully functionally dependent** on every candidate key (no partial dependencies on a proper subset of any composite candidate key).

### Candidate Keys & Partial Dependency Analysis
- **`employees`:** Candidate keys `{employee_id}`, `{emp_code}`, `{email}`, `{username}` are all single-attribute keys → no partial dependency possible.
- **`attendance`:** Candidate keys `{attendance_id}` and `{employee_id, attendance_date}`.
  - Functional dependency: `(employee_id, attendance_date) → {check_in_time, check_out_time, status, is_late, late_minutes, work_hours, remarks}`.
  - Neither `employee_id` alone nor `attendance_date` alone determines daily attendance attributes → **no partial dependency**.
- **`leave_requests`:** Candidate key `{leave_id}` (single attribute) → **no partial dependency**.
- **`salaries`:** Candidate keys `{salary_id}` and `{employee_id, effective_from}`.
  - All pay components (`basic_salary`, `hra`, `da`, `other_allowances`, `pf_deduction`, `professional_tax`, `effective_to`, `is_current`) depend on the full `(employee_id, effective_from)` salary revision → **no partial dependency**.
- **`payroll`:** Candidate keys `{payroll_id}` and `{employee_id, pay_year, pay_month}`.
  - All monthly figures (`working_days`, `present_days`, `basic_earned`, `income_tax`, `payment_status`, etc.) depend on the full `(employee_id, pay_year, pay_month)` tuple → **no partial dependency**.

All relations satisfy **2NF**.

---

## 4. Third Normal Form (3NF) & BCNF

**Rule:** Relation is in 2NF and has **no transitive dependencies** ($X \to Y \to Z$ where $Y$ is not a superkey and $Z$ is non-prime). For BCNF, every determinant of a non-trivial functional dependency must be a superkey.

### Transitive Dependencies Identified & Eliminated

1. **Department attributes inside `employees`:**
   - Transitive FD: `employee_id → dept_code → dept_name` (where `dept_code` is not a superkey of `employees`).
   - **Resolution:** Extracted `departments(department_id PK, department_code UK, department_name UK, description)` and replaced `dept_code`/`dept_name` in `employees` with `department_id FK`.

2. **Authentication / RBAC separation from `employees`:**
   - Coupling security attributes (`username`, `password_hash`, `role`, `is_active`, `last_login_at`) with HR master data mixes two distinct lifecycles (HR record vs system login).
   - **Resolution:** Extracted `user_accounts(user_id PK, employee_id FK UK, username UK, password_hash, role, is_active, last_login_at)`.

3. **Leave policy attributes inside `leave_requests`:**
   - Transitive FD: `leave_id → type_code → {type_name, is_paid, max_days_per_year}`.
   - **Resolution:** Extracted `leave_types(leave_type_id PK, type_code UK, type_name UK, is_paid, max_days_per_year, description)` and replaced repeating policy columns in `leave_requests` with `leave_type_id FK`.

4. **Derived totals in `salaries` and `payroll`:**
   - In `salaries`: `gross_salary` is **not** stored as an independent column because `{basic_salary, hra, da, other_allowances} → gross_salary` would create a derived dependency. It is computed dynamically by the Phase 2 stored function `calculate_salary`.
   - In `payroll`: Base snapshot fields (`basic_earned`, `allowances_earned`, `pf_deduction`, `professional_tax`, `income_tax`, `leave_deduction`) capture historical monthly facts that depend on `(employee_id, pay_year, pay_month)` (since salaries may change in subsequent months and earned pay may be prorated). Derived totals (`gross_salary`, `total_deductions`, `net_salary`) are implemented as MySQL 8.0 `GENERATED ALWAYS AS (...) STORED` columns so the database engine guarantees zero update anomalies.

---

## 5. Final Functional Dependencies & Candidate Keys Summary

| Table | Candidate Keys | Primary Key | Non-Trivial Functional Dependencies | Normal Form |
|---|---|---|---|---|
| `departments` | `{department_id}`, `{department_code}`, `{department_name}` | `department_id` | `CK → {description, created_at}` | **3NF / BCNF** |
| `employees` | `{employee_id}`, `{emp_code}`, `{email}` | `employee_id` | `CK → {first_name, last_name, phone, department_id, designation, hire_date, employment_status, created_at, updated_at}` | **3NF / BCNF** |
| `user_accounts` | `{user_id}`, `{employee_id}`, `{username}` | `user_id` | `CK → {password_hash, role, is_active, last_login_at, created_at, updated_at}` | **3NF / BCNF** |
| `attendance` | `{attendance_id}`, `{employee_id, attendance_date}` | `attendance_id` | `CK → {check_in_time, check_out_time, status, is_late, late_minutes, work_hours, remarks, created_at, updated_at}` | **3NF / BCNF** |
| `leave_types` | `{leave_type_id}`, `{type_code}`, `{type_name}` | `leave_type_id` | `CK → {is_paid, max_days_per_year, description}` | **3NF / BCNF** |
| `leave_requests` | `{leave_id}` | `leave_id` | `leave_id → {employee_id, leave_type_id, start_date, end_date, total_days, reason, status, approved_by, approved_at, applied_at, updated_at}` | **3NF / BCNF** |
| `salaries` | `{salary_id}`, `{employee_id, effective_from}` | `salary_id` | `CK → {basic_salary, hra, da, other_allowances, pf_deduction, professional_tax, effective_to, is_current, created_at, updated_at}` | **3NF / BCNF** |
| `payroll` | `{payroll_id}`, `{employee_id, pay_year, pay_month}` | `payroll_id` | `CK → {salary_id, working_days, present_days, paid_leave_days, unpaid_leave_days, late_count, basic_earned, allowances_earned, pf_deduction, professional_tax, income_tax, leave_deduction, payment_status, payment_date, generated_by, generated_at, updated_at}` (+ DBMS-generated totals) | **3NF / BCNF** |
