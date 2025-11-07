Deactivated created customers
```sql
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
```
Query Documentation
Purpose
 Calculate customer metrics for a given month and year: the total number of active customers, newly created customers, and deactivated customers.
Tables
customer_customer → contains customer details including creation and deactivation dates.


Logic and Filters
created_customers → counts customers whose created_at falls within the specified {{month}} and {{year}}.


deactivated_customers → counts customers whose deactivated_at falls within the specified {{month}} and {{year}}.


is_active → flags a customer as active if:


deactivated_at is null (still active), or


deactivated_at is after the given month/year, or


deactivated in the same year but after the given month.


Output Columns
active_customers → sum of all currently active customers in the period.


created_customers → sum of customers created in the specified month/year.


deactivated_customers → sum of customers deactivated in the specified month/year.


Result Set
 Returns a single row with the aggregated counts of active, created, and deactivated customers for the given month/year.