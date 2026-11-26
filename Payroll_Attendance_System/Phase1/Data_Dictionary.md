# Phase 1: Data Dictionary

Database: `payroll_attendance_db` (MySQL 8.0+, `InnoDB`, `utf8mb4_unicode_ci`)

---

## 1. `departments`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `department_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate department identifier |
| `department_code` | `VARCHAR(10)` | `NO` | — | `UNIQUE` | Short code (e.g., `ENG`, `QA`, `OPS`, `HR`, `FIN`) |
| `department_name` | `VARCHAR(100)` | `NO` | — | `UNIQUE` | Full department name |
| `description` | `VARCHAR(255)` | `YES` | `NULL` | — | Department functional overview |
| `created_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Record creation timestamp |

---

## 2. `employees`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `employee_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate employee identifier |
| `emp_code` | `VARCHAR(20)` | `NO` | — | `UNIQUE` | Human-readable employee ID (e.g., `EMP001`) |
| `first_name` | `VARCHAR(50)` | `NO` | — | — | Employee given name |
| `last_name` | `VARCHAR(50)` | `NO` | — | — | Employee family name |
| `email` | `VARCHAR(120)` | `NO` | — | `UNIQUE` | Corporate email address |
| `phone` | `VARCHAR(20)` | `NO` | — | — | Contact phone number |
| `department_id` | `INT` | `NO` | — | `FK → departments(department_id)` | Assigned department |
| `designation` | `VARCHAR(100)` | `NO` | — | — | Job title / role in firm |
| `hire_date` | `DATE` | `NO` | — | — | Official joining date |
| `employment_status` | `ENUM('ACTIVE','ON_LEAVE','RESIGNED','TERMINATED')` | `NO` | `'ACTIVE'` | — | Current employment status |
| `created_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Record creation timestamp |
| `updated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — | Last update timestamp |

---

## 3. `user_accounts`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `user_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate user account identifier |
| `employee_id` | `INT` | `NO` | — | `FK → employees(employee_id)`, `UNIQUE` | 1:1 linked employee record |
| `username` | `VARCHAR(50)` | `NO` | — | `UNIQUE` | Login username |
| `password_hash` | `VARCHAR(255)` | `NO` | — | — | Salted cryptographic password hash (Werkzeug `scrypt`) |
| `role` | `ENUM('HR_ADMIN','EMPLOYEE')` | `NO` | `'EMPLOYEE'` | — | RBAC role controlling application access |
| `is_active` | `BOOLEAN` | `NO` | `TRUE` | — | Login enabled/disabled status |
| `last_login_at` | `DATETIME` | `YES` | `NULL` | — | Timestamp of last successful authentication |
| `created_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Account creation timestamp |
| `updated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — | Last modification timestamp |

---

## 4. `attendance`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `attendance_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate attendance record ID |
| `employee_id` | `INT` | `NO` | — | `FK → employees(employee_id)`, `UNIQUE(employee_id, attendance_date)` | Employee identifier |
| `attendance_date` | `DATE` | `NO` | — | `UNIQUE(employee_id, attendance_date)` | Calendar date of attendance |
| `check_in_time` | `TIME` | `YES` | `NULL` | — | Daily check-in timestamp (`NULL` if `ABSENT`/`ON_LEAVE`) |
| `check_out_time` | `TIME` | `YES` | `NULL` | `CHECK (>= check_in_time)` | Daily check-out timestamp |
| `status` | `ENUM('PRESENT','ABSENT','HALF_DAY','ON_LEAVE','WORK_FROM_HOME')` | `NO` | `'PRESENT'` | — | Daily attendance classification |
| `is_late` | `BOOLEAN` | `NO` | `FALSE` | — | `TRUE` when `PRESENT` check-in > `09:30:00` |
| `late_minutes` | `SMALLINT UNSIGNED` | `NO` | `0` | — | Minutes elapsed after `09:30:00` |
| `work_hours` | `DECIMAL(4,2)` | `NO` | `0.00` | `CHECK (0.00–24.00)` | Computed hours worked on that date |
| `remarks` | `VARCHAR(255)` | `YES` | `NULL` | — | Optional HR/employee note |
| `created_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Entry creation timestamp |
| `updated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — | Entry last update timestamp |

---

## 5. `leave_types`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `leave_type_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate leave type identifier |
| `type_code` | `VARCHAR(10)` | `NO` | — | `UNIQUE` | Leave code (`CL`, `SL`, `EL`, `LWP`) |
| `type_name` | `VARCHAR(50)` | `NO` | — | `UNIQUE` | Display name of leave category |
| `is_paid` | `BOOLEAN` | `NO` | `TRUE` | — | `TRUE` = paid leave; `FALSE` = Loss-of-Pay |
| `max_days_per_year` | `SMALLINT UNSIGNED` | `NO` | `12` | — | Annual paid quota (`0` for unlimited LWP) |
| `description` | `VARCHAR(255)` | `YES` | `NULL` | — | Policy notes |

---

## 6. `leave_requests`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `leave_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate leave application ID |
| `employee_id` | `INT` | `NO` | — | `FK → employees(employee_id)` | Applicant employee |
| `leave_type_id` | `INT` | `NO` | — | `FK → leave_types(leave_type_id)` | Requested leave category |
| `start_date` | `DATE` | `NO` | — | — | Leave start date |
| `end_date` | `DATE` | `NO` | — | `CHECK (end_date >= start_date)` | Leave end date |
| `total_days` | `DECIMAL(4,1)` | `NO` | — | `CHECK (total_days > 0)` | Leave duration in days (supports `0.5`) |
| `reason` | `VARCHAR(255)` | `NO` | — | — | Reason for leave |
| `status` | `ENUM('PENDING','APPROVED','REJECTED','CANCELLED')` | `NO` | `'PENDING'` | — | Approval workflow status |
| `approved_by` | `INT` | `YES` | `NULL` | `FK → employees(employee_id)` | HR/Admin who approved/rejected |
| `approved_at` | `DATETIME` | `YES` | `NULL` | — | Approval/rejection timestamp |
| `applied_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Submission timestamp |
| `updated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — | Last update timestamp |

---

## 7. `salaries`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `salary_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate salary revision ID |
| `employee_id` | `INT` | `NO` | — | `FK → employees(employee_id)`, `UNIQUE(employee_id, effective_from)` | Employee reference |
| `basic_salary` | `DECIMAL(12,2)` | `NO` | — | `CHECK (basic_salary > 0.00)` | Monthly basic salary |
| `hra` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | House Rent Allowance |
| `da` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Dearness / Special Allowance |
| `other_allowances` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Conveyance, medical & tech allowances |
| `pf_deduction` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Monthly Provident Fund contribution |
| `professional_tax` | `DECIMAL(10,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Monthly statutory professional tax |
| `effective_from` | `DATE` | `NO` | — | `UNIQUE(employee_id, effective_from)` | Effective start date of this revision |
| `effective_to` | `DATE` | `YES` | `NULL` | `CHECK (effective_to IS NULL OR effective_to >= effective_from)` | End date (`NULL` while active) |
| `is_current` | `BOOLEAN` | `NO` | `TRUE` | — | Active structure indicator |
| `created_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Record creation timestamp |
| `updated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — | Last modification timestamp |

---

## 8. `payroll`

| Column | Data Type | Null | Default | Key / Constraint | Description |
|---|---|---|---|---|---|
| `payroll_id` | `INT` | `NO` | `AUTO_INCREMENT` | `PK` | Surrogate monthly payroll ID |
| `employee_id` | `INT` | `NO` | — | `FK → employees(employee_id)`, `UNIQUE(employee_id, pay_year, pay_month)` | Payee employee |
| `salary_id` | `INT` | `NO` | — | `FK → salaries(salary_id)` | Salary revision used for calculation |
| `pay_month` | `TINYINT UNSIGNED` | `NO` | — | `CHECK (1–12)`, `UNIQUE(employee_id, pay_year, pay_month)` | Calendar month (`1`–`12`) |
| `pay_year` | `SMALLINT UNSIGNED` | `NO` | — | `CHECK (2000–2100)`, `UNIQUE(employee_id, pay_year, pay_month)` | Calendar year |
| `working_days` | `TINYINT UNSIGNED` | `NO` | — | `CHECK (1–31)` | Scheduled working days in pay period |
| `present_days` | `DECIMAL(4,1)` | `NO` | `0.0` | `CHECK (>= 0.0)` | Present + WFH + half-day equivalents |
| `paid_leave_days` | `DECIMAL(4,1)` | `NO` | `0.0` | `CHECK (>= 0.0)` | Approved paid leave days in period |
| `unpaid_leave_days` | `DECIMAL(4,1)` | `NO` | `0.0` | `CHECK (>= 0.0)` | Unpaid leave & unexcused absent days |
| `late_count` | `SMALLINT UNSIGNED` | `NO` | `0` | — | Count of late check-ins in period |
| `basic_earned` | `DECIMAL(12,2)` | `NO` | — | `CHECK (>= 0.00)` | Monthly basic earned |
| `allowances_earned` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Monthly allowances earned (`HRA + DA + Other`) |
| `gross_salary` | `DECIMAL(12,2)` | `NO` | `GENERATED` | `STORED` | `basic_earned + allowances_earned` |
| `pf_deduction` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Provident fund deducted |
| `professional_tax` | `DECIMAL(10,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Professional tax deducted |
| `income_tax` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Monthly TDS computed by `calculate_tax` |
| `leave_deduction` | `DECIMAL(12,2)` | `NO` | `0.00` | `CHECK (>= 0.00)` | Loss-of-Pay deduction for unpaid days |
| `total_deductions` | `DECIMAL(12,2)` | `NO` | `GENERATED` | `STORED` | `pf_deduction + professional_tax + income_tax + leave_deduction` |
| `net_salary` | `DECIMAL(12,2)` | `NO` | `GENERATED` | `STORED`, `CHECK (>= 0)` | `gross_salary - total_deductions` |
| `payment_status` | `ENUM('DRAFT','PROCESSED','PAID','CANCELLED')` | `NO` | `'DRAFT'` | — | Payroll lifecycle state |
| `payment_date` | `DATE` | `YES` | `NULL` | — | Date disbursed (`NULL` until `PAID`) |
| `generated_by` | `INT` | `YES` | `NULL` | `FK → employees(employee_id)` | HR/Admin who ran payroll |
| `generated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP` | — | Generation timestamp |
| `updated_at` | `TIMESTAMP` | `NO` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — | Last modification timestamp |
