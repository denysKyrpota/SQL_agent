Activities finished today + truck license plate
```sql
SELECT
    activity_activity.id AS activity_id,
    activity_activity.type,
    activity_activity.kind,
    activity_activity.status,
    activity_activity.finished_datetime,
    asset_truck.license_plate
FROM 
    activity_activity
LEFT JOIN asset_assignment 
    ON asset_assignment.id = activity_activity.assignment_id
LEFT JOIN asset_truck 
    ON asset_truck.id = asset_assignment.truck_id
WHERE 
    activity_activity.deleted = 'false'
    AND activity_activity.finished_datetime::date = current_date
ORDER BY 
    finished_datetime ASC;

```
Query Documentation
Purpose
 Retrieve all activities that were finished today, including their details and the related truck’s license plate.
Tables and Joins
activity_activity → main table containing activities.


asset_assignment → links an activity to a truck assignment (activity_activity.assignment_id = asset_assignment.id).


asset_truck → provides the truck’s license plate (asset_truck.id = asset_assignment.truck_id).


LEFT JOINs ensure that activities are returned even if no assignment or truck is linked.





Filters
activity_activity.deleted = false → excludes deleted activities.


activity_activity.finished_datetime::date = current_date → restricts results to activities finished on the current date.


Output Columns
activity_id → unique identifier of the activity.


type → type of the activity (e.g., trailer change, driver/truck change).


kind → category of the activity (e.g., activity, boek stop).


status → current status of the activity (finished).


finished_datetime → timestamp of when the activity was completed.


license_plate → truck’s license plate associated with the activity.


Result Set
 Each row represents one activity finished today with key details and the truck license plate (if assigned).