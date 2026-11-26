"""
Runs EXPLAIN on Phase 3 Report 3 (Late Marks Report) before and after
applying Phase3/indexes.sql against the live MySQL database.
"""

from datetime import date, timedelta
from pathlib import Path
import sys
import mysql.connector

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import Config

EXPLAIN_SQL = """
EXPLAIN
SELECT
    e.emp_code,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    d.department_name,
    a.attendance_date,
    a.check_in_time,
    a.late_minutes,
    COUNT(*) OVER (PARTITION BY a.employee_id) AS total_late_marks
FROM attendance a
JOIN employees e   ON a.employee_id = e.employee_id
JOIN departments d ON e.department_id = d.department_id
WHERE a.is_late = TRUE
  AND a.attendance_date BETWEEN %s AND %s
ORDER BY a.attendance_date DESC, a.late_minutes DESC
"""


def main():
    if not Config.MYSQL_PASSWORD:
        print("ERROR: MYSQL_PASSWORD not configured in .env")
        sys.exit(1)

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
    )
    cur = conn.cursor(dictionary=True)

    today = date.today()
    first_of_this_month = today.replace(day=1)
    prev_end = first_of_this_month - timedelta(days=1)
    prev_start = prev_end.replace(day=1)

    try:
        # Ensure clean before-state by dropping idx_attendance_late_date if present
        cur.execute("SHOW INDEX FROM attendance WHERE Key_name = 'idx_attendance_late_date'")
        if cur.fetchall():
            cur.execute("DROP INDEX idx_attendance_late_date ON attendance")

        print("=== EXPLAIN BEFORE INDEX (idx_attendance_late_date dropped) ===")
        cur.execute(EXPLAIN_SQL, (prev_start.isoformat(), prev_end.isoformat()))
        for row in cur.fetchall():
            print(row)

        # Recreate index
        cur.execute(
            "CREATE INDEX idx_attendance_late_date ON attendance (is_late, attendance_date, employee_id)"
        )

        print("\n=== EXPLAIN AFTER INDEX (idx_attendance_late_date created) ===")
        cur.execute(EXPLAIN_SQL, (prev_start.isoformat(), prev_end.isoformat()))
        for row in cur.fetchall():
            print(row)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
