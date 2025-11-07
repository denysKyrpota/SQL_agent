Current year delayed activities more than 3 hours
```sql
SELECT
    activity_activity.id,
    activity_activity.type,
    activity_activity.ordered_arrival_datetime_from,
    activity_activity.actual_arrival_datetime,
    activity_activity.finished_datetime,
    EXTRACT(EPOCH FROM (activity_activity.actual_arrival_datetime - activity_activity.ordered_arrival_datetime_from))/3600 AS hours_delay,
    asset_truck.license_plate
FROM 
    activity_activity
LEFT JOIN asset_assignment 
    ON asset_assignment.id = activity_activity.assignment_id
LEFT JOIN asset_truck 
    ON asset_truck.id = asset_assignment.truck_id
WHERE 
    activity_activity.deleted = 'false'
    AND activity_activity.status = 'finished'
    AND activity_activity.kind = 'activity'
    AND activity_activity.actual_arrival_datetime > activity_activity.ordered_arrival_datetime_from
    AND EXTRACT('year' FROM activity_activity.actual_arrival_datetime) = EXTRACT('year' FROM current_date)
    AND EXTRACT(EPOCH FROM (activity_activity.actual_arrival_datetime - activity_activity.ordered_arrival_datetime_from))/3600 > 3.0;
```
Query Documentation
Purpose
 Retrieve all activities from the current year that were finished and delayed by more than 3 hours compared to the scheduled arrival time, including truck details and delay duration.
Tables and Joins
activity_activity → main table storing activity records.


asset_assignment → links an activity to a truck assignment (activity_activity.assignment_id = asset_assignment.id).


asset_truck → provides the truck’s license plate (asset_truck.id = asset_assignment.truck_id).


LEFT JOINs ensure activities are returned even if no assignment or truck exists.


Filters
activity_activity.deleted = false → excludes deleted activities.


activity_activity.status = 'finished' → only finished activities.


activity_activity.kind = 'activity' → restricts to activities of kind activity.


activity_activity.actual_arrival_datetime > activity_activity.ordered_arrival_datetime_from → ensures only delayed activities are considered.


EXTRACT('year' FROM activity_activity.actual_arrival_datetime) = EXTRACT('year' FROM current_date) → restricts results to the current year.


hours_delay > 3.0 → filters activities delayed more than 3 hours.


Output Columns
id → unique identifier of the activity.


type → type of the activity (e.g., trailer change, driver/truck change).


ordered_arrival_datetime_from → scheduled start of the activity.


actual_arrival_datetime → actual start time of the activity.


finished_datetime → completion time of the activity.


hours_delay → delay in hours, calculated as (actual_arrival - scheduled_arrival).


license_plate → truck associated with the activity.


Result Set
 Each row represents a delayed activity from the current year with details of the delay, type, timing, and associated truck.