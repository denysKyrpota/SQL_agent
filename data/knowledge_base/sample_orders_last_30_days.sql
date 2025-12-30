-- Recent Orders (Last 30 Days)
-- Description: Get all orders placed in the last 30 days with customer information

SELECT
    o.order_id,
    o.order_date,
    o.status,
    o.total_amount,
    c.customer_id,
    c.customer_name,
    c.email,
    COUNT(oi.order_item_id) AS item_count
FROM
    orders o
INNER JOIN customers c
    ON o.customer_id = c.customer_id
LEFT JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE
    o.order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY
    o.order_id, o.order_date, o.status, o.total_amount,
    c.customer_id, c.customer_name, c.email
ORDER BY
    o.order_date DESC;
