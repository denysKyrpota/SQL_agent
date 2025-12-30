-- Monthly Sales Summary
-- Description: Aggregate sales data by month for the current year

SELECT
    DATE_TRUNC('month', o.order_date) AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    SUM(o.total_amount) AS total_revenue,
    AVG(o.total_amount) AS average_order_value
FROM
    orders o
WHERE
    o.status = 'completed'
    AND EXTRACT(YEAR FROM o.order_date) = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY
    DATE_TRUNC('month', o.order_date)
ORDER BY
    month DESC;
