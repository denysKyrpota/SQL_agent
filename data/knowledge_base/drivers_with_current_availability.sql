	Drivers with current availability
```sql
SELECT
    data_external_id,
    name,
    arrival_datetime,
    departure_datetime,
    asset_driverstatuschange.status AS driver_status
FROM
    asset_driver
LEFT JOIN asset_driveravailability
    ON asset_driveravailability.driver_id = asset_driver.id
LEFT JOIN asset_driverstatuschange
    ON asset_driverstatuschange.id = asset_driver.current_status_id
WHERE
    NOW() BETWEEN arrival_datetime AND departure_datetime
    AND departure_datetime >= NOW()
    AND NOT (
        asset_driver.name ILIKE ANY (ARRAY[
            '%test%',
            '%tara%',
            '%shift%',
            'Pioter Wisniewski',
            'Cambodia Voditel'
        ])
    );
```

Query Documentation
Purpose
 Retrieve all drivers who are currently available, along with their arrival/departure times and current status, while excluding test or placeholder records.
Tables and Joins
asset_driver → main table containing driver details (data_external_id, name).


asset_driveravailability → stores driver availability windows (arrival_datetime, departure_datetime).


asset_driverstatuschange → provides current driver status via current_status_id.


LEFT JOINs ensure drivers are returned even if availability or status records are missing.


Filters
NOW() BETWEEN arrival_datetime AND departure_datetime → includes drivers whose current time falls within their availability window.


departure_datetime >= NOW() → ensures only future or ongoing availability is considered.


NOT asset_driver.name ILIKE ANY (...) → excludes drivers with test, temporary, or placeholder names.


Output Columns
data_external_id → driver’s external ID.


name → driver’s name.


arrival_datetime → start of driver’s availability window.


departure_datetime → end of driver’s availability window.


driver_status → current status of the driver (from asset_driverstatuschange).


Result Set
 Each row represents a currently available driver, including their availability window, status, and identifiers, excluding inactive, test, or placeholder records.