import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[2]

OPERATIONAL_DB = BASE_DIR / "database" / "banking.db"
ANALYTICAL_DB = BASE_DIR / "database" / "analytics.db"


def normalize_date(date_value):
    """Convert supported date formats to YYYY-MM-DD."""

    if "/" in date_value:
        return datetime.strptime(
            date_value,
            "%m/%d/%Y"
        ).strftime("%Y-%m-%d")

    return datetime.strptime(
        date_value,
        "%Y-%m-%d"
    ).strftime("%Y-%m-%d")


def create_analytics_database():

    operational_connection = sqlite3.connect(OPERATIONAL_DB)

    try:

        analytics_connection = sqlite3.connect(ANALYTICAL_DB)

        try:

            analytics_connection.executescript("""
                DROP TABLE IF EXISTS fact_transaction;
                DROP TABLE IF EXISTS dim_date;
                DROP TABLE IF EXISTS dim_account;
                DROP TABLE IF EXISTS dim_customer;
                DROP TABLE IF EXISTS dim_branch;

                CREATE TABLE dim_branch (
                    branch_id TEXT PRIMARY KEY,
                    branch_name TEXT NOT NULL
                );

                CREATE TABLE dim_customer (
                    customer_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL
                );

                CREATE TABLE dim_account (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    account_type TEXT NOT NULL
                );

                CREATE TABLE dim_date (
                    date_key INTEGER PRIMARY KEY,
                    full_date TEXT NOT NULL UNIQUE,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    day INTEGER NOT NULL
                );

                CREATE TABLE fact_transaction (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    date_key INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL
                );
            """)

            # -------------------------
            # Load branches
            # -------------------------

            branches = operational_connection.execute("""
                SELECT
                    branch_id,
                    branch_name
                FROM branches
            """).fetchall()

            analytics_connection.executemany("""
                INSERT INTO dim_branch (
                    branch_id,
                    branch_name
                )
                VALUES (?, ?)
            """, branches)

            # -------------------------
            # Load customers
            # -------------------------

            customers = operational_connection.execute("""
                SELECT
                    customer_id,
                    customer_name
                FROM customers
            """).fetchall()

            analytics_connection.executemany("""
                INSERT INTO dim_customer (
                    customer_id,
                    customer_name
                )
                VALUES (?, ?)
            """, customers)

            # -------------------------
            # Load accounts
            # -------------------------

            accounts = operational_connection.execute("""
                SELECT
                    account_id,
                    customer_id,
                    branch_id,
                    account_type
                FROM accounts
            """).fetchall()

            analytics_connection.executemany("""
                INSERT INTO dim_account (
                    account_id,
                    customer_id,
                    branch_id,
                    account_type
                )
                VALUES (?, ?, ?, ?)
            """, accounts)

            # -------------------------
            # Load transactions
            # -------------------------

            transactions = operational_connection.execute("""
                SELECT
                    t.transaction_id,
                    t.account_id,
                    a.customer_id,
                    a.branch_id,
                    t.transaction_date,
                    t.transaction_type,
                    t.amount,
                    t.currency
                FROM transactions t
                JOIN accounts a
                    ON t.account_id = a.account_id
            """).fetchall()

            # -------------------------
            # Build unique date dimension
            # -------------------------

            normalized_dates = set()

            for row in transactions:

                transaction_date = row[4]

                normalized_date = normalize_date(
                    transaction_date
                )

                normalized_dates.add(normalized_date)

            date_rows = []

            for normalized_date in sorted(normalized_dates):

                date_object = datetime.strptime(
                    normalized_date,
                    "%Y-%m-%d"
                )

                year = date_object.year
                month = date_object.month
                day = date_object.day

                date_key = int(
                    date_object.strftime("%Y%m%d")
                )

                date_rows.append(
                    (
                        date_key,
                        normalized_date,
                        year,
                        month,
                        day
                    )
                )

            analytics_connection.executemany("""
                INSERT INTO dim_date (
                    date_key,
                    full_date,
                    year,
                    month,
                    day
                )
                VALUES (?, ?, ?, ?, ?)
            """, date_rows)

            # -------------------------
            # Build fact table
            # -------------------------

            fact_rows = []

            for row in transactions:

                (
                    transaction_id,
                    account_id,
                    customer_id,
                    branch_id,
                    transaction_date,
                    transaction_type,
                    amount,
                    currency
                ) = row

                normalized_date = normalize_date(
                    transaction_date
                )

                date_object = datetime.strptime(
                    normalized_date,
                    "%Y-%m-%d"
                )

                date_key = int(
                    date_object.strftime("%Y%m%d")
                )

                fact_rows.append(
                    (
                        transaction_id,
                        account_id,
                        customer_id,
                        branch_id,
                        date_key,
                        transaction_type,
                        amount,
                        currency
                    )
                )

            analytics_connection.executemany("""
                INSERT INTO fact_transaction (
                    transaction_id,
                    account_id,
                    customer_id,
                    branch_id,
                    date_key,
                    transaction_type,
                    amount,
                    currency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, fact_rows)

            analytics_connection.commit()

            print("Analytics database created successfully.")
            print(f"dim_branch: {len(branches)} rows")
            print(f"dim_customer: {len(customers)} rows")
            print(f"dim_account: {len(accounts)} rows")
            print(f"dim_date: {len(date_rows)} rows")
            print(f"fact_transaction: {len(fact_rows)} rows")

        finally:
            analytics_connection.close()

    finally:
        operational_connection.close()


if __name__ == "__main__":
    create_analytics_database()