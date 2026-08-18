-- =========================================================
-- HydroMet database validation queries
-- =========================================================

-- Count dimensions

SELECT COUNT(*) AS locations
FROM dim_location;

SELECT COUNT(*) AS dates
FROM dim_date;

SELECT COUNT(*) AS variables
FROM dim_variable;

SELECT COUNT(*) AS sources
FROM dim_source;


-- Count fact observations

SELECT COUNT(*) AS observations
FROM fact_observation;


-- Observation counts by variable

SELECT
    v.variable_code,
    v.variable_name,
    COUNT(*) AS observation_count

FROM fact_observation f

JOIN dim_variable v
    ON f.variable_id =
       v.variable_id

GROUP BY
    v.variable_code,
    v.variable_name

ORDER BY
    v.variable_code;


-- Observation counts by location

SELECT
    l.location_name,
    COUNT(*) AS observation_count

FROM fact_observation f

JOIN dim_location l
    ON f.location_id =
       l.location_id

GROUP BY
    l.location_name

ORDER BY
    l.location_name;


-- Date coverage

SELECT
    MIN(d.full_date)
        AS earliest_date,

    MAX(d.full_date)
        AS latest_date

FROM fact_observation f

JOIN dim_date d
    ON f.date_id =
       d.date_id;