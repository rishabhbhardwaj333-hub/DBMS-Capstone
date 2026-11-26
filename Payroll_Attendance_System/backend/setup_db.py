"""
Database initialization utility.
Executes Phase 2 (schema, functions, triggers, procedures, sample_data),
Phase 3 (indexes), and Phase 4 (transactions) scripts in sequence against MySQL 8.0+.
"""

from pathlib import Path
import re
import mysql.connector
from backend.config import Config

ROOT_DIR = Path(__file__).resolve().parent.parent

SQL_SCRIPTS = [
    ROOT_DIR / "Phase2" / "schema.sql",
    ROOT_DIR / "Phase2" / "functions.sql",
    ROOT_DIR / "Phase2" / "triggers.sql",
    ROOT_DIR / "Phase2" / "procedures.sql",
    ROOT_DIR / "Phase2" / "sample_data.sql",
    ROOT_DIR / "Phase3" / "indexes.sql",
    ROOT_DIR / "Phase4" / "transactions.sql",
]


def parse_sql_statements(sql_text: str):
    """Split a MySQL script containing DELIMITER directives into executable statements."""
    delimiter = ";"
    buffer = []
    statements = []

    for raw_line in sql_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("--"):
            continue

        delim_match = re.match(r"^DELIMITER\s+(\S+)$", stripped, re.IGNORECASE)
        if delim_match:
            if buffer:
                stmt = "\n".join(buffer).strip()
                if stmt:
                    statements.append(stmt)
                buffer = []
            delimiter = delim_match.group(1)
            continue

        buffer.append(raw_line)
        joined = "\n".join(buffer).rstrip()
        if joined.endswith(delimiter):
            stmt = joined[: -len(delimiter)].strip()
            if stmt:
                statements.append(stmt)
            buffer = []

    if buffer:
        stmt = "\n".join(buffer).strip()
        if stmt:
            statements.append(stmt)

    return statements


def run_setup():
    """Connect to MySQL server and run all Phase 2–4 SQL scripts."""
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    cursor = conn.cursor()
    try:
        for script_path in SQL_SCRIPTS:
            print(f"Executing {script_path.relative_to(ROOT_DIR)}...")
            sql_text = script_path.read_text(encoding="utf-8")
            for stmt in parse_sql_statements(sql_text):
                cursor.execute(stmt)
                while cursor.nextset():
                    pass
        print("Database setup completed successfully.")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_setup()
