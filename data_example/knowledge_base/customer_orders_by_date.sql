-- Title: Get customer orders for a specific date range
-- Description: Retrieve all orders with customer information within a date range

SELECT
    customers.customer_id,
    customers.name,
    customers.email,
    orders.order_id,
    orders.order_date,
    orders.total_amount,
    orders.status
FROM
    customers
INNER JOIN orders
    ON customers.customer_id = orders.customer_id
WHERE
    orders.order_date >= '2024-01-01'
    AND orders.order_date < '2024-02-01'
    AND orders.status = 'completed'
ORDER BY
    orders.order_date DESC;
