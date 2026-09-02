-- ============================================================
-- HydroMet-ETL
-- DSAI 6226 - Unit 5: Cloud Data Engineering
-- BigQuery Sandbox Analysis
-- ============================================================

-- Project:
-- hydromet-etl
--
-- Dataset:
-- hydromet
--
-- Table:
-- nasa_power_daily
--
-- Purpose:
-- Demonstrate cloud-based analytical querying, result validation,
-- aggregation, and awareness of bytes processed in BigQuery.
-- ============================================================


-- ------------------------------------------------------------
-- QUERY 1: Validate the uploaded HydroMet dataset
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT location) AS locations,
    MIN(date) AS start_date,
    MAX(date) AS end_date
FROM `hydromet-etl.hydromet.nasa_power_daily`;

-- Expected validated result:
-- total_rows = 73,048
-- locations  = 8
-- start_date = 2001-01-01
-- end_date   = 2025-12-31
--
-- BigQuery estimated bytes processed:
-- 1.18 MB


-- ------------------------------------------------------------
-- QUERY 2: Monthly mean daily precipitation by location
-- ------------------------------------------------------------

SELECT
    location,
    EXTRACT(YEAR FROM date) AS year,
    EXTRACT(MONTH FROM date) AS month,
    AVG(PRECTOTCORR) AS mean_daily_precipitation
FROM `hydromet-etl.hydromet.nasa_power_daily`
GROUP BY
    location,
    year,
    month
ORDER BY
    location,
    year,
    month;

-- Result:
-- 2,400 grouped rows
--
-- BigQuery estimated bytes processed:
-- 1.74 MB


-- ------------------------------------------------------------
-- QUERY 3: Full table scan
-- Demonstrates the cost implication of SELECT *
-- ------------------------------------------------------------

SELECT *
FROM `hydromet-etl.hydromet.nasa_power_daily`;

-- BigQuery estimated bytes processed:
-- 7.04 MB


-- ------------------------------------------------------------
-- QUERY 4: Select only required analytical columns
-- ------------------------------------------------------------

SELECT
    date,
    location,
    PRECTOTCORR
FROM `hydromet-etl.hydromet.nasa_power_daily`
WHERE date BETWEEN '2020-01-01' AND '2025-12-31';

-- BigQuery estimated bytes processed:
-- 1.74 MB
--
-- Compared with SELECT *:
--
-- 7.04 MB -> 1.74 MB
--
-- Reduction:
-- approximately 75.3%
--
-- Important:
-- This table was not demonstrated here as a date-partitioned
-- production table. Therefore, most of the reduction should be
-- attributed to column projection rather than automatically
-- attributed to partition pruning.


-- ------------------------------------------------------------
-- QUERY 5: Annual precipitation by location
-- ------------------------------------------------------------

SELECT
    location,
    EXTRACT(YEAR FROM date) AS year,
    SUM(PRECTOTCORR) AS annual_precipitation
FROM `hydromet-etl.hydromet.nasa_power_daily`
WHERE date BETWEEN '2020-01-01' AND '2025-12-31'
GROUP BY
    location,
    year
ORDER BY
    location,
    year;

-- BigQuery estimated bytes processed:
-- 1.74 MB