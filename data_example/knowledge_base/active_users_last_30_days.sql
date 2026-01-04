-- Title: Active users in the last 30 days
-- Description: Find all users who have logged in within the past 30 days

SELECT
    users.user_id,
    users.username,
    users.email,
    users.created_at,
    MAX(login_history.login_timestamp) AS last_login,
    COUNT(login_history.login_id) AS login_count
FROM
    users
INNER JOIN login_history
    ON users.user_id = login_history.user_id
WHERE
    login_history.login_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    AND users.status = 'active'
GROUP BY
    users.user_id,
    users.username,
    users.email,
    users.created_at
ORDER BY
    last_login DESC;
