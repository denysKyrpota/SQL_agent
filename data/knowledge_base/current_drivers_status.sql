-- Current driver’s status

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