	Drivers with expired certificates
```sql
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
```

Query Documentation
Purpose
 Retrieve the most recent certifications for active drivers or students that have already expired.
Tables and Joins
asset_drivercertification → main table storing driver certifications and their dates.


asset_driver → provides driver details (name, data_external_id).


asset_driverstatuschange → provides current driver status (driver or student).


asset_certification → stores certification names and status.


LEFT JOINs ensure drivers and certifications are included even if related records are missing.


Filters
Only non-deleted and non-archived certifications (deleted = false, archived = false).


Only active drivers (asset_driver.deleted = false) with external ID > 999.


Certification is active (asset_certification.deactivated_at IS NULL).


Only drivers or students (status IN ('driver','student')).


Excludes test or placeholder driver names.


latest_certificate = 1 → only the most recent certification per driver per type.


date_of_expiry < current_date → only expired certifications.


Output Columns
Driver → name of the driver.


Driver code → external identifier of the driver.


Current driver status → current status of the driver.


date_obtained → when the certification was obtained.


date_of_expiry → expiration date of the certification.


document_number → certification document number.


Certificate → name of the certification.


Result Set
 Each row represents the latest expired certification for a driver or student, showing driver details, certification info, and expiry date.