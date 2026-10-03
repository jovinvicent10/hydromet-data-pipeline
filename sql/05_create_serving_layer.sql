-- ============================================================
-- HydroMet-ETL
-- Unit 7 / Week 8: Analytics Serving Layer
-- ============================================================
--
-- Purpose:
-- Create a clean analytical mart and a consumer-facing view
-- from the existing observation-level DuckDB star schema.
--
-- Source view:
--     vw_weather_observations
--
-- Output table:
--     mart_weather_daily
--
-- Consumer view:
--     vw_monthly_climate_summary
-- ============================================================


-- ------------------------------------------------------------
-- 1. Daily Weather Mart
-- ------------------------------------------------------------
--
-- Grain:
-- One row per location per observation date.
--
-- The analytical star schema stores one meteorological
-- variable per observation row. This mart pivots those
-- variables back into columns so that analysts and downstream
-- applications can consume daily weather data easily.
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE mart_weather_daily AS

SELECT
    observation_date,
    location_name,
    latitude,
    longitude,
    country,
    source_name,

    MAX(
        CASE
            WHEN variable_code = 'T2M'
            THEN value
        END
    ) AS t2m,

    MAX(
        CASE
            WHEN variable_code = 'T2M_MIN'
            THEN value
        END
    ) AS t2m_min,

    MAX(
        CASE
            WHEN variable_code = 'T2M_MAX'
            THEN value
        END
    ) AS t2m_max,

    MAX(
        CASE
            WHEN variable_code = 'RH2M'
            THEN value
        END
    ) AS rh2m,

    MAX(
        CASE
            WHEN variable_code = 'PRECTOTCORR'
            THEN value
        END
    ) AS prectotcorr,

    MAX(
        CASE
            WHEN variable_code = 'WS2M'
            THEN value
        END
    ) AS ws2m,

    MAX(
        CASE
            WHEN variable_code = 'ALLSKY_SFC_SW_DWN'
            THEN value
        END
    ) AS allsky_sfc_sw_dwn

FROM vw_weather_observations

GROUP BY
    observation_date,
    location_name,
    latitude,
    longitude,
    country,
    source_name;


-- ------------------------------------------------------------
-- 2. Monthly Climate Consumer View
-- ------------------------------------------------------------
--
-- Grain:
-- One row per location per year per month.
--
-- Intended consumers:
-- - analysts
-- - dashboards
-- - climate reporting
-- - agricultural analytics
-- - downstream ML exploration
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_monthly_climate_summary AS

SELECT
    location_name,
    EXTRACT(YEAR FROM observation_date) AS year,
    EXTRACT(MONTH FROM observation_date) AS month,

    AVG(t2m) AS mean_temperature,
    AVG(t2m_min) AS mean_min_temperature,
    AVG(t2m_max) AS mean_max_temperature,
    AVG(rh2m) AS mean_relative_humidity,

    SUM(prectotcorr) AS total_precipitation,

    AVG(ws2m) AS mean_wind_speed,
    AVG(allsky_sfc_sw_dwn) AS mean_solar_radiation,

    COUNT(*) AS daily_observations

FROM mart_weather_daily

GROUP BY
    location_name,
    EXTRACT(YEAR FROM observation_date),
    EXTRACT(MONTH FROM observation_date);