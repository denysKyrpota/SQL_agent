-- Deactivated created customers

SELECT 
    SUM(is_active) AS active_customers,
    SUM(created_customers) AS created_customers,
    SUM(deactivated_customers) AS deactivated_customers
FROM (
    SELECT
        customer_customer.name AS customer,
        customer_customer.created_at,
        customer_customer.deactivated_at AS customer_deactivated_at,
        CASE 
            WHEN created_at IS NOT NULL 
                 AND EXTRACT('month' FROM created_at) = {{month}} 
                 AND EXTRACT('year' FROM created_at) = {{year}} 
            THEN 1 
            ELSE 0 
        END AS created_customers,
        CASE 
            WHEN deactivated_at IS NOT NULL 
                 AND EXTRACT('month' FROM deactivated_at) = {{month}} 
                 AND EXTRACT('year' FROM deactivated_at) = {{year}} 
            THEN 1 
            ELSE 0 
        END AS deactivated_customers,
        CASE 
            WHEN deactivated_at IS NOT NULL AND EXTRACT('year' FROM deactivated_at) = {{year}} AND {{month}} > EXTRACT('month' FROM deactivated_at) THEN 1
            WHEN deactivated_at IS NOT NULL AND EXTRACT('year' FROM deactivated_at) > {{year}} THEN 1
            WHEN deactivated_at IS NULL THEN 1
            ELSE 0
        END AS is_active
    FROM
        customer_customer
) subquery;