-- Activities finished today + truck license plate

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