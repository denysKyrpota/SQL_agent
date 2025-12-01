Current driver’s status
```sql
SELECT
    asset_driver.name,
    asset_driver.data_external_id AS driver_code,
    asset_driverstatuschange.status
FROM 
    asset_driver
LEFT JOIN asset_driverstatuschange 
    ON asset_driverstatuschange.id = asset_driver.current_status_id
WHERE 
    asset_driver.deleted = 'false'
    AND asset_driver.data_external_id > 999;

```

Query Documentation
Purpose
 Retrieve a list of drivers with their name, external driver code, and current status.
Tables and Joins
asset_driver → main table containing driver details.


asset_driverstatuschange → joined with asset_driver.current_status_id = asset_driverstatuschange.id to fetch the driver’s current status.


LEFT JOIN ensures all drivers are included, even if no matching status record exists.


Filters
asset_driver.deleted = false → excludes deleted drivers.


asset_driver.data_external_id > 999 → only includes drivers with an external ID above 999.


Output Columns
name → driver’s name.


driver_code → alias for data_external_id (external driver code).


status → current driver status from asset_driverstatuschange.


Result Set
 Each row represents one active (non-deleted) driver with a valid external ID (>999), optionally enriched with their current status.

