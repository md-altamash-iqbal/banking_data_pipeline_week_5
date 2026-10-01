import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
ANALYTICS_DB = BASE_DIR / "database" / "analytics.db"


def get_connection():
    connection = sqlite3.connect(ANALYTICS_DB)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_analytics_database_exists():
    assert ANALYTICS_DB.exists()


def test_required_tables_exist():
    connection = get_connection()

    try:
        tables = {
            row[0]
            for row in connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """)
        }

        required_tables = {
            "dim_branch",
            "dim_customer",
            "dim_account",
            "dim_date",
            "fact_transaction",
        }

        assert required_tables.issubset(tables)

    finally:
        connection.close()


def test_dimension_row_counts():
    connection = get_connection()

    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM dim_branch"
        ).fetchone()[0] == 3

        assert connection.execute(
            "SELECT COUNT(*) FROM dim_customer"
        ).fetchone()[0] == 6

        assert connection.execute(
            "SELECT COUNT(*) FROM dim_account"
        ).fetchone()[0] == 10

        assert connection.execute(
            "SELECT COUNT(*) FROM dim_date"
        ).fetchone()[0] == 4

    finally:
        connection.close()


def test_fact_transaction_row_count():
    connection = get_connection()

    try:
        count = connection.execute("""
            SELECT COUNT(*)
            FROM fact_transaction
        """).fetchone()[0]

        assert count == 20

    finally:
        connection.close()


def test_fact_transaction_grain():
    connection = get_connection()

    try:
        total_rows = connection.execute("""
            SELECT COUNT(*)
            FROM fact_transaction
        """).fetchone()[0]

        unique_transaction_ids = connection.execute("""
            SELECT COUNT(DISTINCT transaction_id)
            FROM fact_transaction
        """).fetchone()[0]

        assert total_rows == unique_transaction_ids

    finally:
        connection.close()


def test_total_transaction_amount():
    connection = get_connection()

    try:
        total = connection.execute("""
            SELECT SUM(amount)
            FROM fact_transaction
        """).fetchone()[0]

        assert total == 4735.5

    finally:
        connection.close()


def test_fact_dimension_relationships():
    connection = get_connection()

    try:
        invalid_accounts = connection.execute("""
            SELECT COUNT(*)
            FROM fact_transaction f
            LEFT JOIN dim_account a
                ON f.account_id = a.account_id
            WHERE a.account_id IS NULL
        """).fetchone()[0]

        invalid_customers = connection.execute("""
            SELECT COUNT(*)
            FROM fact_transaction f
            LEFT JOIN dim_customer c
                ON f.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """).fetchone()[0]

        invalid_branches = connection.execute("""
            SELECT COUNT(*)
            FROM fact_transaction f
            LEFT JOIN dim_branch b
                ON f.branch_id = b.branch_id
            WHERE b.branch_id IS NULL
        """).fetchone()[0]

        invalid_dates = connection.execute("""
            SELECT COUNT(*)
            FROM fact_transaction f
            LEFT JOIN dim_date d
                ON f.date_key = d.date_key
            WHERE d.date_key IS NULL
        """).fetchone()[0]

        assert invalid_accounts == 0
        assert invalid_customers == 0
        assert invalid_branches == 0
        assert invalid_dates == 0

    finally:
        connection.close()