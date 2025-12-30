-- Employees by Department
-- Description: List all employees grouped by department with their job titles

SELECT
    d.department_name,
    e.employee_id,
    e.first_name,
    e.last_name,
    e.email,
    e.job_title,
    e.hire_date
FROM
    employees e
INNER JOIN departments d
    ON e.department_id = d.department_id
WHERE
    e.active = true
ORDER BY
    d.department_name, e.last_name, e.first_name;
