CREATE OR REPLACE VIEW vw_weather_observations AS

SELECT
    d.full_date AS observation_date,

    d.year,
    d.quarter,
    d.month,
    d.month_name,

    l.location_name,
    l.latitude,
    l.longitude,
    l.country,

    v.variable_code,
    v.variable_name,
    v.unit,

    s.source_name,

    f.value,
    f.ingested_at

FROM fact_observation f

JOIN dim_date d
    ON f.date_id =
       d.date_id

JOIN dim_location l
    ON f.location_id =
       l.location_id

JOIN dim_variable v
    ON f.variable_id =
       v.variable_id

JOIN dim_source s
    ON f.source_id =
       s.source_id;