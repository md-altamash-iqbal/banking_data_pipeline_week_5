
-- QUERY 1 - JOIN
-- Transactions with customer, account, and branch details

SELECT
    t.transaction_id,
    t.transaction_date,
    t.transaction_type,
    t.amount,
    t.currency,
    a.account_id,
    c.customer_id,
    c.customer_name,
    b.branch_id,
    b.branch_name,
    b.city
FROM transactions t
JOIN accounts a
    ON t.account_id = a.account_id
JOIN customers c
    ON a.customer_id = c.customer_id
JOIN branches b
    ON a.branch_id = b.branch_id
ORDER BY t.transaction_id;


-- QUERY 2 - JOIN
-- Accounts by customer


SELECT
    c.customer_id,
    c.customer_name,
    a.account_id,
    a.account_type,
    a.account_status
FROM customers c
JOIN accounts a
    ON c.customer_id = a.customer_id
ORDER BY c.customer_id, a.account_id;


-- QUERY 3 - JOIN
-- Transactions by branch


SELECT
    b.branch_id,
    b.branch_name,
    t.transaction_id,
    t.transaction_type,
    t.amount
FROM branches b
JOIN accounts a
    ON b.branch_id = a.branch_id
JOIN transactions t
    ON a.account_id = t.account_id
ORDER BY b.branch_id, t.transaction_id;


-- QUERY 4 - AGGREGATION
-- Number of transactions by customer


SELECT
    c.customer_id,
    c.customer_name,
    COUNT(t.transaction_id) AS transaction_count
FROM customers c
JOIN accounts a
    ON c.customer_id = a.customer_id
LEFT JOIN transactions t
    ON a.account_id = t.account_id
GROUP BY c.customer_id, c.customer_name
ORDER BY transaction_count DESC, c.customer_id;



-- QUERY 5 - AGGREGATION
-- Total transaction amount by customer


SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(t.amount), 2) AS total_transaction_amount
FROM customers c
JOIN accounts a
    ON c.customer_id = a.customer_id
JOIN transactions t
    ON a.account_id = t.account_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_transaction_amount DESC;



-- QUERY 6 - AGGREGATION
-- Transaction count by branch


SELECT
    b.branch_id,
    b.branch_name,
    COUNT(t.transaction_id) AS transaction_count
FROM branches b
JOIN accounts a
    ON b.branch_id = a.branch_id
LEFT JOIN transactions t
    ON a.account_id = t.account_id
GROUP BY b.branch_id, b.branch_name
ORDER BY transaction_count DESC, b.branch_id;


-- QUERY 7 - AGGREGATION
-- Total amount by transaction type


SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_amount,
    ROUND(AVG(amount), 2) AS average_amount
FROM transactions
GROUP BY transaction_type
ORDER BY total_amount DESC;



-- QUERY 8 - CASE
-- Classify transactions into meaningful amount bands


SELECT
    transaction_id,
    transaction_type,
    amount,
    CASE
        WHEN amount < 100 THEN 'Small (<100)'
        WHEN amount < 500 THEN 'Medium (100-499.99)'
        ELSE 'Large (500+)'
    END AS amount_band
FROM transactions
ORDER BY amount DESC;



-- QUERY 9 - CTE
-- Calculate customer totals and filter the derived result


WITH customer_totals AS (
    SELECT
        c.customer_id,
        c.customer_name,
        SUM(t.amount) AS total_amount
    FROM customers c
    JOIN accounts a
        ON c.customer_id = a.customer_id
    JOIN transactions t
        ON a.account_id = t.account_id
    GROUP BY c.customer_id, c.customer_name
)
SELECT
    customer_id,
    customer_name,
    ROUND(total_amount, 2) AS total_amount
FROM customer_totals
WHERE total_amount >= 500
ORDER BY total_amount DESC;



-- QUERY 10 - WINDOW FUNCTION
-- Rank transactions within each account


SELECT
    c.customer_id,
    c.customer_name,
    t.transaction_id,
    t.transaction_type,
    t.amount,
    RANK() OVER (
        PARTITION BY c.customer_id
        ORDER BY t.amount DESC
    ) AS transaction_rank
FROM customers c
JOIN accounts a
    ON c.customer_id = a.customer_id
JOIN transactions t
    ON a.account_id = t.account_id
ORDER BY c.customer_id, transaction_rank;


-- QUERY 11 - WINDOW FUNCTION
-- Running total for each account


SELECT
    c.customer_id,
    c.customer_name,
    t.transaction_id,
    t.transaction_date,
    t.amount,
    ROUND(
        SUM(t.amount) OVER (
            PARTITION BY c.customer_id
            ORDER BY t.transaction_date, t.transaction_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ),
        2
    ) AS running_total
FROM customers c
JOIN accounts a
    ON c.customer_id = a.customer_id
JOIN transactions t
    ON a.account_id = t.account_id
ORDER BY c.customer_id, t.transaction_date, t.transaction_id;


-- QUERY 12 - WINDOW FUNCTION
-- Rank customers by total transaction value


WITH customer_totals AS (
    SELECT
        c.customer_id,
        c.customer_name,
        SUM(t.amount) AS total_amount
    FROM customers c
    JOIN accounts a
        ON c.customer_id = a.customer_id
    JOIN transactions t
        ON a.account_id = t.account_id
    GROUP BY c.customer_id, c.customer_name
)
SELECT
    customer_id,
    customer_name,
    ROUND(total_amount, 2) AS total_amount,
    RANK() OVER (
        ORDER BY total_amount DESC
    ) AS customer_rank
FROM customer_totals
ORDER BY customer_rank;



-- QUERY 13 - BUSINESS QUESTION
-- Which branch has the highest transaction value?


SELECT
    b.branch_id,
    b.branch_name,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(SUM(t.amount), 2) AS total_transaction_value
FROM branches b
JOIN accounts a
    ON b.branch_id = a.branch_id
JOIN transactions t
    ON a.account_id = t.account_id
GROUP BY b.branch_id, b.branch_name
ORDER BY total_transaction_value DESC;



-- QUERY 14 - BUSINESS QUESTION
-- Which transaction type contributes the most value?


SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_value,
    ROUND(
        SUM(amount) * 100.0 /
        (SELECT SUM(amount) FROM transactions),
        2
    ) AS percentage_of_total
FROM transactions
GROUP BY transaction_type
ORDER BY total_value DESC;