# Phase 4: Security & Access Control Architecture

## 1. Role-Based Access Control (RBAC) Matrix

Two distinct application roles are enforced via `user_accounts.role`:

| Capability / Resource | `HR_ADMIN` | `EMPLOYEE` |
|---|---|---|
| View / Search All Employees | Allowed | **Denied (`403`)** |
| Add / Update / Deactivate Employees | Allowed | **Denied (`403`)** |
| Manage / Edit Any Attendance Record | Allowed | **Denied (`403`)** |
| View Own Attendance Summary & History | Allowed | Allowed (Read-only, `session['employee_id']` only) |
| Apply for Leave (Own) | Allowed | Allowed (Own `employee_id` only) |
| Approve / Reject Leave Requests | Allowed (`approve_leave` proc) | **Denied (`403`)** |
| View / Revise Any Salary Structure | Allowed | **Denied (`403`)** |
| View Own Salary Structure & History | Allowed | Allowed (Read-only) |
| Generate / Mark Paid Monthly Payroll | Allowed (`process_monthly_payroll`) | **Denied (`403`)** |
| Download / View Salary Slip | Any Employee | **Own `employee_id` Only** (IDOR blocked with `403`) |
| Access Company Reports (Phase 3) | Allowed (All 6 Reports) | **Denied (`403`)** |
| User Account Management | Allowed | **Denied (`403`)** |

---

## 2. Implemented Security Controls

1. **Password Hashing (`werkzeug.security`):**
   - Passwords are stored exclusively as salted `scrypt` hashes (`generate_password_hash` / `check_password_hash`) in `user_accounts.password_hash`. Plaintext passwords are never stored or logged.
2. **Session-Based Authentication & Account Status Check:**
   - Flask `session` stores `user_id`, `employee_id`, `username`, `role`, and `full_name` using a cryptographic `SECRET_KEY`.
   - Every authenticated request checks `session` and verifies `is_active = TRUE`.
   - `HttpOnly` and `SameSite=Lax` cookie flags are enabled on session cookies.
3. **Server-Side Authorization Decorators (`backend/auth.py`):**
   - `@login_required`: Redirects unauthenticated HTML requests to `/login` and returns `401 Unauthorized` for API requests.
   - `@role_required('HR_ADMIN')`: Enforces server-side RBAC on every admin route; UI hiding is never relied upon alone.
4. **Insecure Direct Object Reference (IDOR) Prevention:**
   - Employee endpoints (`/employee/...`, `/payroll/slip/<payroll_id>`) resolve identity strictly from `session['employee_id']`.
   - For `/payroll/slip/<int:payroll_id>`, if `session['role'] == 'EMPLOYEE'`, the backend verifies `payroll.employee_id == session['employee_id']` (and rejects mismatches with HTTP `403 Forbidden`).
   - Employee leave submission ignores any tampered `employee_id` form parameter and binds strictly to `session['employee_id']`.
5. **SQL Injection Prevention:**
   - Every query in `backend/services/` uses `mysql-connector-python` parameterized `%s` placeholders or parameterized `cursor.callproc(...)` calls. User input is never interpolated into SQL strings.
6. **Input Validation & Transaction Safety:**
   - Server-side validation checks positive salary amounts, valid date spans, valid month/year ranges, and CSRF/method guards (`POST` for state mutations, including `/logout`).
   - Multi-step database mutations (salary revisions, employee creation + user account creation, payroll batch processing) use explicit `START TRANSACTION` / `COMMIT` / `ROLLBACK` blocks.
7. **Sanitized Logging:**
   - Error handlers and logs never emit `password`, `password_hash`, `MYSQL_PASSWORD`, or raw salary numbers.
