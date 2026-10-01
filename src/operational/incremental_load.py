import csv
import sqlite3
from pathlib import Path

from database import get_connection


BASE_DIR = Path(__file__).resolve().parents[2]
DAILY_DIR = BASE_DIR / "data" / "daily"


def upsert_transaction(connection, row):
    """
    Insert a new transaction or update an existing transaction
    when the transaction_id already exists.
    """

    query = """
        INSERT INTO transactions (
            transaction_id,
            account_id,
            transaction_date,
            transaction_type,
            amount,
            currency
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(transaction_id)
        DO UPDATE SET
            account_id = excluded.account_id,
            transaction_date = excluded.transaction_date,
            transaction_type = excluded.transaction_type,
            amount = excluded.amount,
            currency = excluded.currency
    """

    connection.execute(
        query,
        (
            row["transaction_id"],
            row["account_id"],
            row["transaction_date"],
            row["transaction_type"],
            float(row["amount"]),
            row["currency"],
        ),
    )


def process_daily_file(file_name):
    """
    Process one daily transaction CSV.

    New transaction IDs are inserted.
    Existing transaction IDs are updated.
    """

    file_path = DAILY_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Daily file not found: {file_path}"
        )

    connection = get_connection()

    inserted = 0
    updated = 0

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                transaction_id = row["transaction_id"]

                existing = connection.execute(
                    """
                    SELECT 1
                    FROM transactions
                    WHERE transaction_id = ?
                    """,
                    (transaction_id,),
                ).fetchone()

                upsert_transaction(connection, row)

                if existing:
                    updated += 1
                else:
                    inserted += 1

        connection.commit()

        print(f"\nProcessed: {file_name}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def process_all_daily_files():
    """
    Process all Week 5 daily files in chronological order.
    """

    daily_files = sorted(
        DAILY_DIR.glob("transactions_*.csv")
    )

    if not daily_files:
        print("No daily transaction files found.")
        return

    for file_path in daily_files:
        process_daily_file(file_path.name)


if __name__ == "__main__":
    process_all_daily_files()