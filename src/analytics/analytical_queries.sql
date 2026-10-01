-- ============================================================
-- WEEK 5 - ANALYTICAL SQL QUERIES
-- Database: analytics.db
-- Grain: One row per transaction
-- ============================================================


-- ============================================================
-- QUERY 1
-- Total transaction amount
-- ============================================================

SELECT
    SUM(amount) AS total_transaction_amount
FROM fact_transaction;


-- ============================================================
-- QUERY 2
-- CREDIT vs DEBIT analysis
-- ============================================================

SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM fact_transaction
GROUP BY transaction_type
ORDER BY transaction_type;


-- ============================================================
-- QUERY 3
-- Branch-wise transaction analysis
-- ============================================================

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


-- ============================================================
-- QUERY 4
-- Customer-wise transaction analysis
-- ============================================================

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


-- ============================================================
-- QUERY 5
-- Account-wise transaction analysis
-- ============================================================

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


-- ============================================================
-- QUERY 6
-- Daily transaction analysis
-- ============================================================

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


-- ============================================================
-- QUERY 7
-- Transaction classification using CASE
-- ============================================================

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


-- ============================================================
-- QUERY 8
-- Transaction category summary using CASE
-- ============================================================

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


-- ============================================================
-- QUERY 9
-- CTE: customer transaction summary
-- ============================================================

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


-- ============================================================
-- QUERY 10
-- CTE: daily transaction summary
-- ============================================================

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


-- ============================================================
-- QUERY 11
-- WINDOW FUNCTION
-- Rank customers by total transaction amount
-- ============================================================

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


-- ============================================================
-- QUERY 12
-- WINDOW FUNCTION
-- Running transaction total by date
-- ============================================================

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


-- ============================================================
-- QUERY 13
-- WINDOW FUNCTION
-- Rank transactions within each branch
-- ============================================================

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


-- ============================================================
-- QUERY 14
-- Business Question:
-- Which branches have more than 5 transactions?
-- ============================================================

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


-- ============================================================
-- QUERY 15
-- Business Question:
-- What percentage of total transaction value
-- comes from each transaction type?
-- ============================================================

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