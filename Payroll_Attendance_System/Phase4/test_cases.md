# Phase 4: Test Cases Specification

| Test ID | Scenario | Category | Expected Result |
|---|---|---|---|
| **TC-01** | Valid employee creation + linked user account | Valid | Employee & `user_accounts` rows committed cleanly in a single transaction. |
| **TC-02** | Duplicate employee creation (same `emp_code` or `email`) | Invalid | Rejected by `uq_emp_code` / `uq_emp_email` (`1062` Duplicate Entry); transaction rolls back. |
| **TC-03** | Negative or zero salary (`basic_salary <= 0`) | Invalid | Rejected by `chk_salary_basic` / `trg_salary_before_insert` (`Basic salary must be strictly positive`). |
| **TC-04** | Duplicate attendance entry for same employee & date | Invalid | Rejected by `uq_attendance_emp_date` (`1062` Duplicate Entry). |
| **TC-05** | Overlapping approved leave dates | Invalid / Trigger | `approve_leave` & `trg_leave_before_update` raise `SQLSTATE '45000'` and block approval. |
| **TC-06** | Valid payroll generation (`generate_payroll` / `process_monthly_payroll`) | Valid | Computes gross, tax (`calculate_tax`), LOP, and net pay accurately with `payment_status = 'PROCESSED'`. |
| **TC-07** | Duplicate payroll generation for same employee & month | Invalid | Rejected by `generate_payroll` and `uq_payroll_emp_period`. |
| **TC-08** | Invalid login (wrong password or unknown username) | Security | Authentication fails with generic error; session remains unauthenticated. |
| **TC-09** | Unauthorized employee access to HR/Admin endpoint (`/admin/*`) | Security / RBAC | Server returns HTTP `403 Forbidden`. |
| **TC-10** | Employee attempting to access another employee's salary slip (`/payroll/slip/<other_id>`) | Security / IDOR | Server verifies ownership against `session['employee_id']` and returns HTTP `403 Forbidden`. |
| **TC-11** | Transaction rollback on mid-operation failure | Transaction | Explicit `ROLLBACK` reverts prior inserts/updates in the transaction; zero partial records committed. |
| **TC-12** | Boundary cases for attendance and leave (`check_out < check_in`, `end_date < start_date`, future attendance, attendance on approved leave, single-day leave) | Boundary | Invalid boundaries rejected by triggers/constraints; valid single-day (`start_date = end_date`) and exact `09:30:00` non-late boundary accepted. |
