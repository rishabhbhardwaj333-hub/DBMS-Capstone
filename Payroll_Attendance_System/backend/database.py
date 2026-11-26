"""MySQL Connector/Python pool, parameterized query helpers, and transaction manager."""

from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling
from backend.config import Config

_pool = None


def get_pool():
    """Lazily initialize and return the MySQL connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="payroll_pool",
            pool_size=8,
            pool_reset_session=True,
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=False,
        )
    return _pool


def reset_pool():
    """Reset the cached pool (useful when reloading config in tests)."""
    global _pool
    _pool = None


def get_connection():
    """Borrow a connection from the pool."""
    return get_pool().get_connection()


@contextmanager
def transaction():
    """
    Explicit ACID transaction context manager using START TRANSACTION / COMMIT / ROLLBACK.
    Ensures any database error rolls back all intermediate changes cleanly.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def query_all(sql: str, params=None):
    """Execute a parameterized SELECT and return all rows as dicts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def query_one(sql: str, params=None):
    """Execute a parameterized SELECT and return a single row dict or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_write(sql: str, params=None):
    """Execute a single INSERT/UPDATE/DELETE inside a transaction."""
    with transaction() as (_conn, cursor):
        cursor.execute(sql, params or ())
        return cursor.lastrowid, cursor.rowcount


def call_proc(proc_name: str, args=()):
    """
    Call a MySQL stored procedure safely and collect any result sets.
    Commits if the procedure succeeds; rolls back on error.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    results = []
    try:
        cursor.callproc(proc_name, args)
        for res in cursor.stored_results():
            results.extend(res.fetchall())
        conn.commit()
        return results
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
