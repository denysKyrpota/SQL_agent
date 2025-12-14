-- Current year delayed activities more than 3 hours

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