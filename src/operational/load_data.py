import csv
from pathlib import Path

from database import get_connection


BASE_DIR = Path(__file__).resolve().parents[2]

REFERENCE_DIR = BASE_DIR / "data" / "reference"
VALIDATED_DIR = BASE_DIR / "data" / "validated"


def load_branches(connection):
    file_path = REFERENCE_DIR / "branches.csv"

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        rows = [
            (
                row["branch_id"],
                row["branch_name"],
            )
            for row in reader
        ]

    connection.executemany(
        """
        INSERT INTO branches (
            branch_id,
            branch_name
        )
        VALUES (?, ?)
        """,
        rows,
    )

    print("Branches loaded successfully.")


def load_customers(connection):
    file_path = REFERENCE_DIR / "customers.csv"

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        rows = [
            (
                row["customer_id"],
                row["customer_name"],
            )
            for row in reader
        ]

    connection.executemany(
        """
        INSERT INTO customers (
            customer_id,
            customer_name
        )
        VALUES (?, ?)
        """,
        rows,
    )

    print("Customers loaded successfully.")


def load_accounts(connection):
    file_path = REFERENCE_DIR / "accounts.csv"

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        rows = [
            (
                row["account_id"],
                row["customer_id"],
                row["branch_id"],
                row["account_type"],
            )
            for row in reader
        ]

    connection.executemany(
        """
        INSERT INTO accounts (
            account_id,
            customer_id,
            branch_id,
            account_type
        )
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )

    print("Accounts loaded successfully.")


def load_transactions(connection):
    file_path = VALIDATED_DIR / "valid_transactions.csv"

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        rows = [
            (
                row["transaction_id"],
                row["account_id"],
                row["transaction_date"],
                row["transaction_type"],
                float(row["amount"]),
                row["currency"],
            )
            for row in reader
        ]

    connection.executemany(
        """
        INSERT INTO transactions (
            transaction_id,
            account_id,
            transaction_date,
            transaction_type,
            amount,
            currency
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    print("Transactions loaded successfully.")


def load_all_data():
    connection = get_connection()

    try:
        load_branches(connection)
        load_customers(connection)
        load_accounts(connection)
        load_transactions(connection)

        connection.commit()

        print()
        print("All data loaded successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    load_all_data()