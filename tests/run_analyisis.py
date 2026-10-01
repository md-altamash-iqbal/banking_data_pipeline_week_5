import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database" / "analytics.db"


QUERIES = {
    "Query 1 - Total Transaction Amount": """
        SELECT
            SUM(amount) AS total_transaction_amount
        FROM fact_transaction;
    """,

    "Query 2 - Credit vs Debit": """
        SELECT
            transaction_type,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount
        FROM fact_transaction
        GROUP BY transaction_type
        ORDER BY transaction_type;
    """,

    "Query 3 - Branch-wise Analysis": """
        SELECT
            b.branch_id,
            b.branch_name,
            COUNT(f.transaction_id) AS transaction_count,
            SUM(f.amount) AS total_amount
        FROM fact_transaction f
        JOIN dim_branch b
            ON f.branch_id = b.branch_id
        GROUP BY
            b.branch_id,
            b.branch_name
        ORDER BY total_amount DESC;
    """,

    "Query 4 - Customer-wise Analysis": """
        SELECT
            c.customer_id,
            c.customer_name,
            COUNT(f.transaction_id) AS transaction_count,
            SUM(f.amount) AS total_amount,
            AVG(f.amount) AS average_transaction_amount
        FROM fact_transaction f
        JOIN dim_customer c
            ON f.customer_id = c.customer_id
        GROUP BY
            c.customer_id,
            c.customer_name
        ORDER BY total_amount DESC;
    """,

    "Query 5 - Account-wise Analysis": """
        SELECT
            a.account_id,
            a.account_type,
            COUNT(f.transaction_id) AS transaction_count,
            SUM(f.amount) AS total_amount
        FROM fact_transaction f
        JOIN dim_account a
            ON f.account_id = a.account_id
        GROUP BY
            a.account_id,
            a.account_type
        ORDER BY total_amount DESC;
    """,

    "Query 6 - Daily Analysis": """
        SELECT
            d.full_date,
            d.year,
            d.month,
            d.day,
            COUNT(f.transaction_id) AS transaction_count,
            SUM(f.amount) AS total_amount
        FROM fact_transaction f
        JOIN dim_date d
            ON f.date_key = d.date_key
        GROUP BY
            d.date_key,
            d.full_date,
            d.year,
            d.month,
            d.day
        ORDER BY d.full_date;
    """,

    "Query 7 - Transaction Classification": """
        SELECT
            transaction_id,
            amount,
            transaction_type,
            CASE
                WHEN amount >= 500 THEN 'HIGH_VALUE'
                WHEN amount >= 200 THEN 'MEDIUM_VALUE'
                ELSE 'LOW_VALUE'
            END AS transaction_category
        FROM fact_transaction
        ORDER BY amount DESC;
    """,

    "Query 8 - Transaction Category Summary": """
        SELECT
            CASE
                WHEN amount >= 500 THEN 'HIGH_VALUE'
                WHEN amount >= 200 THEN 'MEDIUM_VALUE'
                ELSE 'LOW_VALUE'
            END AS transaction_category,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount
        FROM fact_transaction
        GROUP BY
            CASE
                WHEN amount >= 500 THEN 'HIGH_VALUE'
                WHEN amount >= 200 THEN 'MEDIUM_VALUE'
                ELSE 'LOW_VALUE'
            END
        ORDER BY total_amount DESC;
    """,

    "Query 9 - Customer Summary Using CTE": """
        WITH customer_summary AS (
            SELECT
                customer_id,
                COUNT(*) AS transaction_count,
                SUM(amount) AS total_amount,
                AVG(amount) AS average_amount
            FROM fact_transaction
            GROUP BY customer_id
        )
        SELECT
            c.customer_id,
            c.customer_name,
            cs.transaction_count,
            cs.total_amount,
            cs.average_amount
        FROM customer_summary cs
        JOIN dim_customer c
            ON cs.customer_id = c.customer_id
        ORDER BY cs.total_amount DESC;
    """,

    "Query 10 - Daily Summary Using CTE": """
        WITH daily_summary AS (
            SELECT
                date_key,
                COUNT(*) AS transaction_count,
                SUM(amount) AS total_amount
            FROM fact_transaction
            GROUP BY date_key
        )
        SELECT
            d.full_date,
            ds.transaction_count,
            ds.total_amount
        FROM daily_summary ds
        JOIN dim_date d
            ON ds.date_key = d.date_key
        ORDER BY d.full_date;
    """,

    "Query 11 - Customer Ranking": """
        WITH customer_totals AS (
            SELECT
                customer_id,
                SUM(amount) AS total_amount
            FROM fact_transaction
            GROUP BY customer_id
        )
        SELECT
            c.customer_id,
            c.customer_name,
            ct.total_amount,
            RANK() OVER (
                ORDER BY ct.total_amount DESC
            ) AS customer_rank
        FROM customer_totals ct
        JOIN dim_customer c
            ON ct.customer_id = c.customer_id
        ORDER BY customer_rank;
    """,

    "Query 12 - Running Transaction Total": """
        WITH daily_totals AS (
            SELECT
                date_key,
                SUM(amount) AS daily_amount
            FROM fact_transaction
            GROUP BY date_key
        )
        SELECT
            d.full_date,
            dt.daily_amount,
            SUM(dt.daily_amount) OVER (
                ORDER BY d.full_date
                ROWS BETWEEN UNBOUNDED PRECEDING
                AND CURRENT ROW
            ) AS running_total
        FROM daily_totals dt
        JOIN dim_date d
            ON dt.date_key = d.date_key
        ORDER BY d.full_date;
    """,

    "Query 13 - Transaction Rank Within Branch": """
        SELECT
            f.transaction_id,
            f.branch_id,
            f.amount,
            RANK() OVER (
                PARTITION BY f.branch_id
                ORDER BY f.amount DESC
            ) AS branch_transaction_rank
        FROM fact_transaction f
        ORDER BY
            f.branch_id,
            branch_transaction_rank;
    """,

    "Query 14 - Branches With More Than 5 Transactions": """
        SELECT
            b.branch_id,
            b.branch_name,
            COUNT(f.transaction_id) AS transaction_count,
            SUM(f.amount) AS total_amount
        FROM fact_transaction f
        JOIN dim_branch b
            ON f.branch_id = b.branch_id
        GROUP BY
            b.branch_id,
            b.branch_name
        HAVING COUNT(f.transaction_id) > 5
        ORDER BY transaction_count DESC;
    """,

    "Query 15 - Percentage by Transaction Type": """
        SELECT
            transaction_type,
            SUM(amount) AS total_amount,
            ROUND(
                SUM(amount) * 100.0 /
                (SELECT SUM(amount) FROM fact_transaction),
                2
            ) AS percentage_of_total
        FROM fact_transaction
        GROUP BY transaction_type
        ORDER BY percentage_of_total DESC;
    """
}


def run_analysis():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Analytics database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 70)
        print("WEEK 5 ANALYTICAL SQL RESULTS")
        print("=" * 70)

        for query_name, query in QUERIES.items():

            print()
            print("-" * 70)
            print(query_name)
            print("-" * 70)

            cursor = connection.execute(query)

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            print(columns)

            for row in rows:
                print(row)

            print(f"Rows returned: {len(rows)}")

    finally:
        connection.close()


if __name__ == "__main__":
    run_analysis()