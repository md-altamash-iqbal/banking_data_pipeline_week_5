from database import get_connection


def check_database():
    connection = get_connection()

    try:
        tables = [
            "branches",
            "customers",
            "accounts",
            "transactions",
        ]

        print("\nDatabase row counts:")

        for table in tables:
            cursor = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            )

            count = cursor.fetchone()[0]

            print(f"{table}: {count}")

    finally:
        connection.close()


if __name__ == "__main__":
    check_database()