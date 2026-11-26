# Phase 4: Test Execution Results

Executed via:
```powershell
python -m pytest -v -p no:cacheprovider tests\test_system.py
```

Observed Summary: **`5 passed, 7 skipped in 1.29s`**

| Test ID | Description | Execution Mode | Observed Result | Notes |
|---|---|---|---|---|
| **Struct / SQL Parse** | `test_sql_scripts_exist_and_parse` | Offline (`pytest`) | **PASSED** | All 7 scripts (`Phase2/*.sql`, `Phase3/indexes.sql`, `Phase4/transactions.sql`) exist and parse cleanly. |
| **Crypto Hash** | `test_password_hashing_and_verification` | Offline (`pytest`) | **PASSED** | Werkzeug `scrypt` hashing & verification verified. |
| **Auth Redirect** | `test_unauthenticated_redirect` | Flask Test Client | **PASSED** | Unauthenticated `/admin/*` and `/employee/*` redirect (`302`) to `/login`. |
| **TC-09** | `test_tc09_unauthorized_employee_access_to_admin` | Flask Test Client | **PASSED** | Signed-in `EMPLOYEE` receives HTTP `403` on all `/admin/*` endpoints. |
| **TC-10** | `test_tc10_employee_cannot_view_other_salary_slip` | Flask Test Client | **PASSED** | Signed-in `EMPLOYEE` receives HTTP `403` when requesting another employee's `/payroll/slip/<id>`. |
| **TC-01 / TC-02** | `test_tc01_tc02_employee_creation_and_duplicate` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |
| **TC-03** | `test_tc03_negative_salary_rejected` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |
| **TC-04** | `test_tc04_duplicate_attendance_rejected` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |
| **TC-05** | `test_tc05_overlapping_approved_leave_rejected` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |
| **TC-06 / TC-07** | `test_tc06_tc07_payroll_generation_and_duplicate` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |
| **TC-08** | Invalid login against `user_accounts` | Live MySQL (`MySQL80`) | **NOT EXECUTED** | Requires live `user_accounts` table; add credentials to `.env` to execute. |
| **TC-11** | `test_tc11_transaction_rollback` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |
| **TC-12** | `test_tc12_boundary_attendance_and_leave` | Live MySQL (`MySQL80`) | **SKIPPED** | `MYSQL_PASSWORD` is not yet configured in `.env`. |

## How to Run the Full Live-DB Test Suite

1. Create `.env` from `.env.example` and set `MYSQL_PASSWORD`.
2. Initialize the database: `python backend/setup_db.py`
3. Run: `python -m pytest -v -p no:cacheprovider tests/test_system.py`
