# Phase 1: Entity-Relationship Diagram & Cardinalities

## 1. Entities Overview

The database `payroll_attendance_db` models a mid-sized IT firm's Payroll and Attendance Management System using **5 mandatory core entities** and **3 normalized supporting entities**:

| # | Entity (SQL Table) | Category | Purpose |
|---|---|---|---|
| 1 | `departments` | Supporting (3NF) | Eliminates transitive dependencies for department details out of `employees`. |
| 2 | `employees` | **Mandatory Core** | Stores employee HR master attributes (`emp_code`, name, contact, designation, hire date, status). |
| 3 | `user_accounts` | Supporting (RBAC) | Separates login credentials and RBAC role (`HR_ADMIN`, `EMPLOYEE`) from HR master records. |
| 4 | `attendance` | **Mandatory Core** | Tracks daily check-in/out times, attendance status, late marks, and computed work hours. |
| 5 | `leave_types` | Supporting (3NF) | Normalizes paid/unpaid rules and annual leave entitlements out of `leave_requests`. |
| 6 | `leave_requests` | **Mandatory Core (Leave)** | Stores multiple leave applications per employee and approval workflow (`leave_requests` avoids the MySQL reserved keyword `LEAVE`). |
| 7 | `salaries` | **Mandatory Core** | Preserves versioned salary revision history (`effective_from`, `effective_to`, `is_current`). |
| 8 | `payroll` | **Mandatory Core** | Stores monthly payroll snapshots, attendance/leave summaries, tax, deductions, and net pay. |

## 2. Mermaid ER Diagram

> Raw Mermaid source is also saved in [ER_Diagram.mmd](ER_Diagram.mmd).

```mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : "employs"
    EMPLOYEES ||--o| USER_ACCOUNTS : "has_account"
    EMPLOYEES ||--o{ ATTENDANCE : "logs"
    EMPLOYEES ||--o{ LEAVE_REQUESTS : "applies_for"
    EMPLOYEES ||--o{ LEAVE_REQUESTS : "approves"
    LEAVE_TYPES ||--o{ LEAVE_REQUESTS : "categorizes"
    EMPLOYEES ||--o{ SALARIES : "assigned"
    EMPLOYEES ||--o{ PAYROLL : "receives"
    EMPLOYEES ||--o{ PAYROLL : "generates"
    SALARIES ||--o{ PAYROLL : "basis_for"

    DEPARTMENTS {
        int department_id PK
        varchar department_code UK
        varchar department_name UK
        varchar description
        timestamp created_at
    }

    EMPLOYEES {
        int employee_id PK
        varchar emp_code UK
        varchar first_name
        varchar last_name
        varchar email UK
        varchar phone
        int department_id FK
        varchar designation
        date hire_date
        enum employment_status
        timestamp created_at
        timestamp updated_at
    }

    USER_ACCOUNTS {
        int user_id PK
        int employee_id FK,UK
        varchar username UK
        varchar password_hash
        enum role
        boolean is_active
        datetime last_login_at
        timestamp created_at
        timestamp updated_at
    }

    ATTENDANCE {
        int attendance_id PK
        int employee_id FK
        date attendance_date
        time check_in_time
        time check_out_time
        enum status
        boolean is_late
        smallint late_minutes
        decimal work_hours
        varchar remarks
        timestamp created_at
        timestamp updated_at
    }

    LEAVE_TYPES {
        int leave_type_id PK
        varchar type_code UK
        varchar type_name UK
        boolean is_paid
        smallint max_days_per_year
        varchar description
    }

    LEAVE_REQUESTS {
        int leave_id PK
        int employee_id FK
        int leave_type_id FK
        date start_date
        date end_date
        decimal total_days
        varchar reason
        enum status
        int approved_by FK
        datetime approved_at
        timestamp applied_at
        timestamp updated_at
    }

    SALARIES {
        int salary_id PK
        int employee_id FK
        decimal basic_salary
        decimal hra
        decimal da
        decimal other_allowances
        decimal pf_deduction
        decimal professional_tax
        date effective_from
        date effective_to
        boolean is_current
        timestamp created_at
        timestamp updated_at
    }

    PAYROLL {
        int payroll_id PK
        int employee_id FK
        int salary_id FK
        tinyint pay_month
        smallint pay_year
        tinyint working_days
        decimal present_days
        decimal paid_leave_days
        decimal unpaid_leave_days
        smallint late_count
        decimal basic_earned
        decimal allowances_earned
        decimal gross_salary
        decimal pf_deduction
        decimal professional_tax
        decimal income_tax
        decimal leave_deduction
        decimal total_deductions
        decimal net_salary
        enum payment_status
        date payment_date
        int generated_by FK
        timestamp generated_at
        timestamp updated_at
    }
```

## 3. Relationships and Cardinalities

| ID | Relationship | Parent (1) | Child (N) | Cardinality | Participation | Business Rule |
|---|---|---|---|---|---|---|
| **R1** | Employs | `departments` | `employees` | **1 : N** | Mandatory on `employees` (1..1), Optional on `departments` (0..N) | Every employee belongs to one department; a department can have many employees. |
| **R2** | Has Account | `employees` | `user_accounts` | **1 : 0..1** | Mandatory on `user_accounts` (1..1), Optional on `employees` (0..1) | Each user account maps 1:1 to a unique employee (`employee_id` is `UNIQUE`). |
| **R3** | Logs | `employees` | `attendance` | **1 : N** | Mandatory on `attendance` (1..1), Optional on `employees` (0..N) | An employee logs at most one attendance row per `(employee_id, attendance_date)`. |
| **R4** | Applies For | `employees` | `leave_requests` | **1 : N** | Mandatory on `leave_requests` (1..1), Optional on `employees` (0..N) | An employee may submit multiple leave requests across time. |
| **R5** | Approves | `employees` | `leave_requests` | **1 : N** | Optional on `leave_requests` (0..1), Optional on `employees` (0..N) | `approved_by` references the HR/Admin employee who reviewed the request (`NULL` while `PENDING`). |
| **R6** | Categorizes | `leave_types` | `leave_requests` | **1 : N** | Mandatory on `leave_requests` (1..1), Optional on `leave_types` (0..N) | Every leave application specifies one leave category (`CL`, `SL`, `EL`, `LWP`). |
| **R7** | Assigned | `employees` | `salaries` | **1 : N** | Mandatory on `salaries` (1..1), Optional on `employees` (0..N) | Preserves salary revision history across `effective_from` dates per employee. |
| **R8** | Receives | `employees` | `payroll` | **1 : N** | Mandatory on `payroll` (1..1), Optional on `employees` (0..N) | Each employee receives at most one payroll record per `(pay_year, pay_month)`. |
| **R9** | Generates | `employees` | `payroll` | **1 : N** | Optional on `payroll` (0..1), Optional on `employees` (0..N) | `generated_by` tracks the HR/Admin employee who executed the payroll run. |
| **R10** | Basis For | `salaries` | `payroll` | **1 : N** | Mandatory on `payroll` (1..1), Optional on `salaries` (0..N) | Links each monthly payroll record to the exact salary structure active for that period. |
