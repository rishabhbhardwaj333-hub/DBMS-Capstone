# Final Project Report: Payroll & Attendance Management System

## 1. Executive Summary

The **Payroll & Attendance Management System** for NovaTech IT Solutions is a full-lifecycle relational database and web application designed across five sequential engineering phases. It unifies employee master records, daily attendance logging, leave approval workflows, salary revision tracking, tax-aware monthly payroll processing, analytical reporting, and role-based access control into a single connected MySQL 8.0+ and Python/Flask system.

## 2. Phase-Wise Implementation Summary

### Phase 1: Data Modeling & Schema Design
- Designed an 8-table relational model (`departments`, `employees`, `user_accounts`, `attendance`, `leave_types`, `leave_requests`, `salaries`, `payroll`) normalized to **3NF / BCNF**.
- Preserved salary revision history (`salaries(employee_id, effective_from)`), prevented duplicate daily attendance (`uq_attendance_emp_date`), prevented duplicate monthly payroll (`uq_payroll_emp_period`), and enforced positive compensation (`basic_salary > 0`) via SQL `CHECK` constraints.
- Artifacts: `Phase1/ER_Diagram.md`, `Phase1/ER_Diagram.mmd`, `Phase1/Normalization_Report.md`, `Phase1/Relational_Schema.md`, `Phase1/Data_Dictionary.md`.

### Phase 2: Procedural SQL Implementation
- Implemented the exact Phase 1 schema in `Phase2/schema.sql`.
- Implemented stored functions (`calculate_salary`, `calculate_tax`), stored procedures (`approve_leave`, `generate_payroll`, `process_monthly_payroll`), and 7 validation/auto-calculation triggers in `Phase2/functions.sql`, `Phase2/procedures.sql`, and `Phase2/triggers.sql`.
- Seeded 12 IT firm employees across 5 departments, 4 leave types, salary revision history, 3+ months of weekday attendance, and 3 months of generated payroll in `Phase2/sample_data.sql`.

### Phase 3: Query & Report Development
- Authored 6 analytical SQL reports in `Phase3/reports.sql` (Monthly Attendance Summary, Individual Salary Slip, Late Marks Report, Monthly Payroll Summary, Attendance History, Leave History).
- Added 6 composite B-Tree indexes in `Phase3/indexes.sql` and documented execution plan mechanics in `Phase3/optimization_report.md`.

### Phase 4: Security, Access Control & Testing
- Enforced server-side RBAC (`HR_ADMIN` vs `EMPLOYEE`), salted `scrypt` password hashing, parameterized SQL queries, IDOR ownership checks, and `START TRANSACTION` / `COMMIT` / `ROLLBACK` ACID boundaries (`Phase4/transactions.sql`, `Phase4/security.md`).
- Documented 12 test cases (`Phase4/test_cases.md`) backed by automated `pytest` tests (`tests/test_system.py`).

### Phase 5: Integration & Web Application
- Built a clean enterprise HR dashboard using Flask, MySQL Connector/Python, Bootstrap 5, and Chart.js (`backend/` & `frontend/`), connecting every form, filter, report, and salary slip directly to MySQL 8.0+.

## 3. Real-World Use Cases & Scalability

1. **Multi-Branch IT Enterprises:** Extending `departments` with a `branch_offices` reference supports location-specific statutory Professional Tax and regional holiday calendars.
2. **Audit & Compliance:** Preserving `salaries` history and immutable `payroll` snapshots ensures historical payslips remain auditable even after promotions or tax slab changes.
3. **High-Volume Optimization:** Range partitioning on `attendance(attendance_date)` combined with the Phase 3 composite indexes keeps monthly summaries and late-marks queries fast as headcount grows from 50 to 10,000+ employees.
