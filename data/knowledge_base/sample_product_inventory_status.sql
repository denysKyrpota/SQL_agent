-- Product Inventory Status
-- Description: Check current inventory levels for all products with low stock alerts

SELECT
    p.product_id,
    p.product_name,
    p.category,
    i.quantity_on_hand,
    i.reorder_level,
    i.last_updated,
    CASE
        WHEN i.quantity_on_hand <= i.reorder_level THEN 'Low Stock'
        WHEN i.quantity_on_hand = 0 THEN 'Out of Stock'
        ELSE 'In Stock'
    END AS stock_status
FROM
    products p
LEFT JOIN inventory i
    ON p.product_id = i.product_id
WHERE
    p.active = true
ORDER BY
    i.quantity_on_hand ASC, p.product_name;
