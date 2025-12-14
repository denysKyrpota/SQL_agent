--	Drivers with expired certificates

SELECT
    "Driver",
    "Driver code",
    "Current driver status",
    date_obtained,
    date_of_expiry,
    document_number,
    "Certificate"
FROM (
    SELECT
        asset_driver.name AS "Driver",
        asset_driver.data_external_id AS "Driver code",
        asset_driverstatuschange.status AS "Current driver status",
        asset_drivercertification.date_obtained,
        asset_drivercertification.date_of_expiry,
        asset_drivercertification.document_number,
        asset_certification.name AS "Certificate",
        asset_drivercertification.certification_id,
        ROW_NUMBER() OVER (
            PARTITION BY asset_driver.id, asset_certification.id
            ORDER BY asset_drivercertification.created_at DESC
        ) AS latest_certificate
    FROM
        asset_drivercertification
    LEFT JOIN asset_driver 
        ON asset_driver.id = asset_drivercertification.driver_id
    LEFT JOIN asset_driverstatuschange 
        ON asset_driverstatuschange.id = asset_driver.current_status_id
    LEFT JOIN asset_certification 
        ON asset_certification.id = asset_drivercertification.certification_id
    WHERE 
        asset_drivercertification.deleted = 'false'
        AND asset_driver.deleted = 'false'
        AND asset_driverstatuschange.status IN ('driver', 'student')
        AND asset_driver.data_external_id > 999
        AND asset_certification.deactivated_at IS NULL
        AND asset_drivercertification.archived = 'false'
        AND NOT (
            asset_driver.name ILIKE ANY (ARRAY[
                '%test%',
                '%tara%',
                '%shift%',
                'Pioter Wisniewski',
                'Cambodia Voditel'
            ])
        )
    ORDER BY asset_driver.name
) x
WHERE latest_certificate = 1
    AND date_of_expiry < current_date;