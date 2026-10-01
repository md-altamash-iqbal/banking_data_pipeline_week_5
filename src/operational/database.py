import sqlite3
from pathlib import Path


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Database and schema paths
DATABASE_PATH = BASE_DIR / "database" / "banking.db"
SCHEMA_PATH = BASE_DIR / "src" / "operational" / "schema.sql"


def get_connection():
    """
    Create and return a SQLite connection.

    Foreign-key enforcement is enabled for every connection.
    """
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def create_database():
    """
    Create the operational banking database
    using schema.sql.
    """

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)
        connection.commit()

        print("Banking database created successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    create_database()