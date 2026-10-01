import csv
import sqlite3
import sys
from pathlib import Path

import pytest


# Allow importing the production incremental loader
BASE_DIR = Path(__file__).resolve().parents[1]
OPERATIONAL_DIR = BASE_DIR / "src" / "operational"

sys.path.insert(0, str(OPERATIONAL_DIR))

import incremental_load


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    """
    Create a temporary SQLite database so tests never modify
    the real banking.db.
    """

    db_path = tmp_path / "test_banking.db"

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript(
        """
        CREATE TABLE branches (
            branch_id TEXT PRIMARY KEY,
            branch_name TEXT NOT NULL
        );

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL
        );

        CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            branch_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
        );

        CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            currency TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        );

        INSERT INTO branches
        VALUES ('BR001', 'Downtown Branch');

        INSERT INTO customers
        VALUES ('C1001', 'Maya Patel');

        INSERT INTO accounts
        VALUES ('A1001', 'C1001', 'BR001', 'CHECKING');
        """
    )

    connection.commit()
    connection.close()

    # Make production code use the temporary database
    monkeypatch.setattr(
        incremental_load,
        "get_connection",
        lambda: sqlite3.connect(db_path)
    )

    # Make production code read temporary daily files
    monkeypatch.setattr(
        incremental_load,
        "DAILY_DIR",
        tmp_path
    )

    return db_path, tmp_path


def write_daily_file(directory, file_name, rows):
    """
    Create a temporary daily CSV file.
    """

    file_path = directory / file_name

    fieldnames = [
        "transaction_id",
        "account_id",
        "transaction_date",
        "transaction_type",
        "amount",
        "currency",
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return file_path


def test_new_transaction_is_inserted(test_database):
    db_path, daily_dir = test_database

    write_daily_file(
        daily_dir,
        "transactions_20260910.csv",
        [
            {
                "transaction_id": "T9001",
                "account_id": "A1001",
                "transaction_date": "2026-09-10",
                "transaction_type": "CREDIT",
                "amount": "100.00",
                "currency": "USD",
            }
        ],
    )

    incremental_load.process_daily_file("transactions_20260910.csv")

    connection = sqlite3.connect(db_path)

    row = connection.execute(
        """
        SELECT transaction_id, amount
        FROM transactions
        WHERE transaction_id = 'T9001'
        """
    ).fetchone()

    connection.close()

    assert row == ("T9001", 100.0)


def test_existing_transaction_is_updated(test_database):
    db_path, daily_dir = test_database

    connection = sqlite3.connect(db_path)

    connection.execute(
        """
        INSERT INTO transactions
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "T9002",
            "A1001",
            "2026-09-10",
            "DEBIT",
            50.0,
            "USD",
        ),
    )

    connection.commit()
    connection.close()

    write_daily_file(
        daily_dir,
        "transactions_20260911.csv",
        [
            {
                "transaction_id": "T9002",
                "account_id": "A1001",
                "transaction_date": "2026-09-10",
                "transaction_type": "DEBIT",
                "amount": "75.00",
                "currency": "USD",
            }
        ],
    )

    incremental_load.process_daily_file("transactions_20260911.csv")

    connection = sqlite3.connect(db_path)

    row = connection.execute(
        """
        SELECT amount
        FROM transactions
        WHERE transaction_id = 'T9002'
        """
    ).fetchone()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE transaction_id = 'T9002'
        """
    ).fetchone()[0]

    connection.close()

    assert row == (75.0,)
    assert count == 1


def test_rerun_does_not_create_duplicates(test_database):
    db_path, daily_dir = test_database

    write_daily_file(
        daily_dir,
        "transactions_20260912.csv",
        [
            {
                "transaction_id": "T9003",
                "account_id": "A1001",
                "transaction_date": "2026-09-12",
                "transaction_type": "CREDIT",
                "amount": "200.00",
                "currency": "USD",
            }
        ],
    )

    # First run
    incremental_load.process_daily_file("transactions_20260912.csv")

    # Second run
    incremental_load.process_daily_file("transactions_20260912.csv")

    connection = sqlite3.connect(db_path)

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE transaction_id = 'T9003'
        """
    ).fetchone()[0]

    connection.close()

    assert count == 1


def test_transaction_ids_remain_unique(test_database):
    db_path, daily_dir = test_database

    write_daily_file(
        daily_dir,
        "transactions_20260913.csv",
        [
            {
                "transaction_id": "T9004",
                "account_id": "A1001",
                "transaction_date": "2026-09-13",
                "transaction_type": "CREDIT",
                "amount": "300.00",
                "currency": "USD",
            },
            {
                "transaction_id": "T9004",
                "account_id": "A1001",
                "transaction_date": "2026-09-13",
                "transaction_type": "CREDIT",
                "amount": "350.00",
                "currency": "USD",
            },
        ],
    )

    incremental_load.process_daily_file("transactions_20260913.csv")

    connection = sqlite3.connect(db_path)

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE transaction_id = 'T9004'
        """
    ).fetchone()[0]

    connection.close()

    assert count == 1