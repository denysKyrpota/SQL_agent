--	Drivers with current availability

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