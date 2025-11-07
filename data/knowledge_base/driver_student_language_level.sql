Driver/student language level
```sql
select
asset_driverlanguage.language , asset_driver.name as "Driver name", asset_driver.data_external_id as "Driver code", asset_driverstatuschange.status as "Current driver status",
CASE 
        WHEN asset_driverlanguage.level = 0 THEN 'A0'
        WHEN asset_driverlanguage.level = 1 THEN 'A0+'
        WHEN asset_driverlanguage.level = 2 THEN 'A1-'
        WHEN asset_driverlanguage.level = 3 THEN 'A1'
        WHEN asset_driverlanguage.level = 4 THEN 'A1+'
        WHEN asset_driverlanguage.level = 5 THEN 'A2-'
        WHEN asset_driverlanguage.level = 6 THEN 'A2'
        WHEN asset_driverlanguage.level = 7 THEN 'A2+'
        WHEN asset_driverlanguage.level = 8 THEN 'B1-'
        WHEN asset_driverlanguage.level = 9 THEN 'B1'
        WHEN asset_driverlanguage.level = 10 THEN 'B1+'
        WHEN asset_driverlanguage.level = 11 THEN 'B2-'
        WHEN asset_driverlanguage.level = 12 THEN 'B2'
        WHEN asset_driverlanguage.level = 13 THEN 'B2+'
        WHEN asset_driverlanguage.level = 14 THEN 'C1-'
        WHEN asset_driverlanguage.level = 15 THEN 'C1'
        WHEN asset_driverlanguage.level = 16 THEN 'C1+'
        WHEN asset_driverlanguage.level = 17 THEN 'C2'
    END AS level
from asset_driverlanguage
left join asset_driver on asset_driver.id = asset_driverlanguage.driver_id 
left join asset_driverstatuschange on asset_driverstatuschange.id = asset_driver.current_status_id
LEFT JOIN boekestijn_payrollcompany ON boekestijn_payrollcompany.id = asset_driver.payroll_company_id

where 
asset_driver.deleted = 'false'
and asset_driverstatuschange.status in ('student', 'driver')
    AND boekestijn_payrollcompany.entity_id <> 20
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
 Retrieve the language skills and proficiency levels of active drivers or students, excluding certain test or irrelevant records and specific payroll entities.
Tables and Joins
asset_driverlanguage → main table containing driver language skills and levels.


asset_driver → provides driver personal details (name and data_external_id).


asset_driverstatuschange → provides current status of the driver (student or driver).


boekestijn_payrollcompany → filters out drivers belonging to payroll company with entity_id = 20.


Filters
asset_driver.deleted = false → includes only active drivers.


asset_driverstatuschange.status IN ('student', 'driver') → limits to students or drivers.


boekestijn_payrollcompany.entity_id <> 20 → excludes specific payroll entity.


NOT asset_driver.name ILIKE ANY (...) → excludes drivers with test or placeholder names.


Output Columns
language → language the driver knows.


Driver name → name of the driver.


Driver code → external driver identifier (data_external_id).


Current driver status → driver’s current status (student or driver).


level → driver’s language proficiency mapped from numeric level to CEFR scale (A0–C2).


Result Set
 Each row represents a driver or student with their language, mapped proficiency level, status, and basic identifiers, excluding inactive or test records.