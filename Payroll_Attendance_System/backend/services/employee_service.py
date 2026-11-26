"""Employee and department data access & transactional operations."""

from backend.auth import hash_password
from backend.database import query_all, query_one, transaction


def list_departments():
    """Return all departments ordered by name."""
    return query_all(
        "SELECT department_id, department_code, department_name, description "
        "FROM departments ORDER BY department_name"
    )


def list_employees(search: str = "", department_id: str = "", status: str = ""):
    """Return filtered employee records joined with department and current salary."""
    sql = [
        "SELECT e.employee_id, e.emp_code, e.first_name, e.last_name, e.email, e.phone,",
        "       e.department_id, d.department_code, d.department_name,",
        "       e.designation, e.hire_date, e.employment_status,",
        "       s.basic_salary, u.username, u.role",
        "FROM employees e",
        "JOIN departments d ON e.department_id = d.department_id",
        "LEFT JOIN salaries s ON s.employee_id = e.employee_id AND s.is_current = TRUE",
        "LEFT JOIN user_accounts u ON u.employee_id = e.employee_id",
        "WHERE 1=1",
    ]
    params = []

    if search:
        like = f"%{search.strip()}%"
        sql.append(
            "AND (e.emp_code LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s "
            "OR e.email LIKE %s OR e.designation LIKE %s)"
        )
        params.extend([like, like, like, like, like])

    if department_id and department_id.isdigit():
        sql.append("AND e.department_id = %s")
        params.append(int(department_id))

    if status:
        sql.append("AND e.employment_status = %s")
        params.append(status)

    sql.append("ORDER BY e.emp_code")
    return query_all("\n".join(sql), tuple(params))


def get_employee_by_id(employee_id: int):
    """Return detailed employee profile for a single employee."""
    return query_one(
        """
        SELECT e.employee_id, e.emp_code, e.first_name, e.last_name, e.email, e.phone,
               e.department_id, d.department_code, d.department_name,
               e.designation, e.hire_date, e.employment_status,
               u.user_id, u.username, u.role, u.is_active, u.last_login_at
        FROM employees e
        JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN user_accounts u ON u.employee_id = e.employee_id
        WHERE e.employee_id = %s
        """,
        (employee_id,),
    )


def create_employee_with_account(data: dict):
    """
    Create an employee and optionally an initial salary & login account
    inside a single ACID transaction.
    """
    emp_code = (data.get("emp_code") or "").strip().upper()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    department_id = int(data.get("department_id"))
    designation = (data.get("designation") or "").strip()
    hire_date = data.get("hire_date")
    employment_status = data.get("employment_status") or "ACTIVE"

    if not all([emp_code, first_name, last_name, email, phone, designation, hire_date]):
        raise ValueError("All required employee fields must be provided.")

    basic_salary = data.get("basic_salary")
    username = (data.get("username") or "").strip().lower()
    raw_password = data.get("password") or ""
    role = data.get("role") or "EMPLOYEE"

    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            INSERT INTO employees (
                emp_code, first_name, last_name, email, phone,
                department_id, designation, hire_date, employment_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                emp_code, first_name, last_name, email, phone,
                department_id, designation, hire_date, employment_status,
            ),
        )
        new_emp_id = cursor.lastrowid

        if basic_salary not in (None, ""):
            basic_val = float(basic_salary)
            if basic_val <= 0:
                raise ValueError("Basic salary must be strictly positive.")
            cursor.execute(
                """
                INSERT INTO salaries (
                    employee_id, basic_salary, hra, da, other_allowances,
                    pf_deduction, professional_tax, effective_from, effective_to, is_current
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, TRUE)
                """,
                (
                    new_emp_id,
                    basic_val,
                    float(data.get("hra") or 0),
                    float(data.get("da") or 0),
                    float(data.get("other_allowances") or 0),
                    float(data.get("pf_deduction") or 0),
                    float(data.get("professional_tax") or 200),
                    hire_date,
                ),
            )

        if username and raw_password:
            cursor.execute(
                """
                INSERT INTO user_accounts (employee_id, username, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
                """,
                (new_emp_id, username, hash_password(raw_password), role),
            )

        return new_emp_id


def update_employee(employee_id: int, data: dict):
    """Update employee profile fields inside a transaction."""
    with transaction() as (_conn, cursor):
        cursor.execute(
            """
            UPDATE employees
            SET first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                department_id = %s,
                designation = %s,
                hire_date = %s,
                employment_status = %s
            WHERE employee_id = %s
            """,
            (
                data["first_name"].strip(),
                data["last_name"].strip(),
                data["email"].strip().lower(),
                data["phone"].strip(),
                int(data["department_id"]),
                data["designation"].strip(),
                data["hire_date"],
                data["employment_status"],
                employee_id,
            ),
        )
        if data["employment_status"] in ("RESIGNED", "TERMINATED"):
            cursor.execute(
                "UPDATE user_accounts SET is_active = FALSE WHERE employee_id = %s",
                (employee_id,),
            )


def deactivate_employee(employee_id: int):
    """Soft-deactivate an employee and disable login access atomically."""
    with transaction() as (_conn, cursor):
        cursor.execute(
            "UPDATE employees SET employment_status = 'RESIGNED' WHERE employee_id = %s",
            (employee_id,),
        )
        cursor.execute(
            "UPDATE user_accounts SET is_active = FALSE WHERE employee_id = %s",
            (employee_id,),
        )
