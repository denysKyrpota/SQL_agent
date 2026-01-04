-- Title: Product sales summary with revenue
-- Description: Aggregate sales data by product including total quantity sold and revenue

SELECT
    products.product_id,
    products.product_name,
    products.category,
    COUNT(order_items.order_item_id) AS total_orders,
    SUM(order_items.quantity) AS total_quantity_sold,
    SUM(order_items.quantity * order_items.unit_price) AS total_revenue
FROM
    products
LEFT JOIN order_items
    ON products.product_id = order_items.product_id
WHERE
    products.active = true
GROUP BY
    products.product_id,
    products.product_name,
    products.category
HAVING
    SUM(order_items.quantity) > 0
ORDER BY
    total_revenue DESC;
