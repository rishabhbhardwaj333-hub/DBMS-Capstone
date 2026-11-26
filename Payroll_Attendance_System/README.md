# Payroll & Attendance Management System

A complete, integrated **Payroll & Attendance Management System** for a mid-sized IT firm (`NovaTech IT Solutions`), built across five sequential DBMS engineering phases into one unified full-stack web application.

## Technology Stack

- **Database:** MySQL 8.0+ (`InnoDB`, `utf8mb4_unicode_ci`)
- **Backend:** Python 3, Flask, MySQL Connector/Python, Werkzeug (`scrypt` password hashing)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js

---

## Project Architecture & Folder Structure

```text
Payroll_Attendance_System/
├── Phase1/                     # ER Diagram (.md & .mmd), Normalization (UNF->3NF/BCNF), Relational Schema, Data Dictionary
├── Phase2/                     # MySQL DDL (schema.sql), Functions, Triggers, Procedures, 3-month Sample Data
├── Phase3/                     # 6 Reporting Queries (reports.sql), Composite Indexes (indexes.sql), Optimization Report
├── Phase4/                     # RBAC Security Architecture, Transactional SQL, Test Cases & Test Results
├── backend/                    # Flask App Factory, Config, DB Pool, Auth/RBAC, Routes, Services, DB Setup CLI
├── frontend/                   # Jinja2 Bootstrap 5 Templates (Admin & Employee Portals) + Static CSS/JS
├── docs/                       # Final Project Report & Screenshots folder
├── tests/                      # Automated Pytest Suite & EXPLAIN Comparison Script
├── requirements.txt
├── .env.example
└── README.md
```

---

## Database Design Summary

The permanent Phase 1 schema (`payroll_attendance_db`) consists of **8 normalized (3NF / BCNF) tables**:
1. `departments` — IT firm departments (`ENG`, `QA`, `OPS`, `HR`, `FIN`)
2. `employees` — Employee HR master data
3. `user_accounts` — Role-based authentication (`HR_ADMIN`, `EMPLOYEE`) linked 1:1 to `employees`
4. `attendance` — Daily attendance logs (`UNIQUE(employee_id, attendance_date)`), auto-computed late marks and work hours
5. `leave_types` — Leave policy lookup (`CL`, `SL`, `EL`, `LWP`)
6. `leave_requests` — Employee leave applications & approval audit trail
7. `salaries` — Versioned salary structures (`effective_from`, `effective_to`, `is_current`) with `basic_salary > 0` check
8. `payroll` — Monthly payroll snapshots (`UNIQUE(employee_id, pay_year, pay_month)`) with MySQL 8.0 `GENERATED ALWAYS AS (...) STORED` totals (`gross_salary`, `total_deductions`, `net_salary`)

---

## Prerequisites

1. **MySQL Server 8.0+** (running on `127.0.0.1:3306`)
2. **Python 3.10+** (tested with Python 3.14.5)
3. **pip** package manager

---

## Setup & Installation

### 1. Configure Environment Variables
Copy `.env.example` to `.env` in the project root and set your MySQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
SECRET_KEY=replace-with-random-secret-key
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_MYSQL_ROOT_PASSWORD
MYSQL_DATABASE=payroll_attendance_db
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the MySQL Database (Schema, Functions, Triggers, Procedures, Sample Data, Indexes)

Run the automated setup script (uses `.env` credentials):
```bash
python backend/setup_db.py
```

*(Alternatively, execute in MySQL CLI / Workbench in order: `Phase2/schema.sql`, `Phase2/functions.sql`, `Phase2/triggers.sql`, `Phase2/procedures.sql`, `Phase2/sample_data.sql`, `Phase3/indexes.sql`, `Phase4/transactions.sql`.)*

### 4. Run the Application

```bash
python backend/app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Demo Login Credentials (Seeded in `Phase2/sample_data.sql`)

| Role | Username | Password | Access Scope |
|---|---|---|---|
| **HR / Admin** | `admin` | `Admin@123` | Full HR, Attendance, Leave Approval, Salary, Payroll, Reports & User Management |
| **HR / Admin** | `payroll.admin` | `Admin@123` | Full HR & Payroll Portal |
| **Employee** | `aarav.m` | `Employee@123` | Read-only own profile, attendance, leave balance/apply, salary slips |
| **Employee** | `priya.n` *(or any seeded employee)* | `Employee@123` | Self-service employee portal |

---

## Features & Modules

### HR / Admin Modules
1. **Dashboard:** Live KPI cards (total active employees, present/absent today, pending leaves, latest payroll total, monthly attendance %) + Chart.js Payroll Expenditure & Attendance Overview charts.
2. **Employee Management:** Search & filter by department/status, add employee with optional salary & user account in one ACID transaction, edit details, deactivate employee.
3. **Attendance Management:** Filter by date/employee/status, mark/update attendance with trigger-enforced late marks (`> 09:30:00`), work hours, and approved-leave conflict prevention.
4. **Leave Management:** Filter by status, approve/reject requests via `approve_leave()` stored procedure with overlapping-approved-leave protection.
5. **Salary Management:** View active or full revision history, revise salaries atomically via `sp_revise_salary_transactional`.
6. **Payroll Processing:** Run monthly payroll via `process_monthly_payroll()` (which invokes `generate_payroll()`, `calculate_salary()`, `calculate_tax()`), mark paid, view/print salary slips.
7. **Reports:** Interactive viewer + CSV export + print for Monthly Attendance Summary, Late Marks Report, Monthly Payroll Summary, Attendance History, and Leave History.
8. **User Management:** Create accounts, switch roles, enable/disable logins, and reset passwords safely.
9. **Logout:** Secure session termination.

### Employee Self-Service Modules
- **My Dashboard:** Profile summary, monthly attendance KPIs, leave balances, and recent payslips.
- **My Attendance:** Filterable personal attendance history.
- **My Leaves:** Leave balances, leave application form (full or half-day), and approval status tracking.
- **Salary & Slips:** Read-only salary revision history and printable/downloadable monthly salary slips.

---

## Running Tests & Optimization Verification

```bash
pytest -v
python tests/run_explain_comparison.py
```

---

## Future Scalability

- **Horizontal Read Replicas:** Route heavy Phase 3 analytical reports to MySQL read replicas while keeping transactional payroll writes on the primary node.
- **Table Partitioning:** Partition `attendance` and `payroll` by `YEAR(attendance_date)` / `pay_year` when scaling beyond millions of rows across multi-thousand-employee enterprises.
- **Async Background Payroll Workers:** Offload batch payroll runs for 5,000+ employees to Celery/Redis job queues with progress tracking.
- **Multi-Tenant / Multi-Branch Support:** Add a `company_locations` or `tenants` parent entity with `location_id` scoping for geographically distributed IT offices.
