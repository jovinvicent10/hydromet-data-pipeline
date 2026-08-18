-- =========================================================
-- HydroMet-ETL
-- Analytical Star Schema
-- =========================================================


-- ---------------------------------------------------------
-- LOCATION DIMENSION
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_location (
    location_id INTEGER PRIMARY KEY,
    location_name VARCHAR NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    country VARCHAR DEFAULT 'Tanzania',

    UNIQUE(location_name)
);


-- ---------------------------------------------------------
-- DATE DIMENSION
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,

    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR NOT NULL,
    day INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,

    is_leap_year BOOLEAN,

    UNIQUE(full_date)
);


-- ---------------------------------------------------------
-- VARIABLE DIMENSION
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_variable (
    variable_id INTEGER PRIMARY KEY,

    variable_code VARCHAR NOT NULL,
    variable_name VARCHAR NOT NULL,

    unit VARCHAR,
    description VARCHAR,

    UNIQUE(variable_code)
);


-- ---------------------------------------------------------
-- SOURCE DIMENSION
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_source (
    source_id INTEGER PRIMARY KEY,

    source_name VARCHAR NOT NULL,
    provider VARCHAR,

    temporal_resolution VARCHAR,

    description VARCHAR,

    UNIQUE(source_name)
);


-- ---------------------------------------------------------
-- WEATHER OBSERVATION FACT TABLE
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS fact_observation (

    observation_id BIGINT PRIMARY KEY,

    date_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    variable_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,

    value DOUBLE,

    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(date_id)
        REFERENCES dim_date(date_id),

    FOREIGN KEY(location_id)
        REFERENCES dim_location(location_id),

    FOREIGN KEY(variable_id)
        REFERENCES dim_variable(variable_id),

    FOREIGN KEY(source_id)
        REFERENCES dim_source(source_id),

    UNIQUE(
        date_id,
        location_id,
        variable_id,
        source_id
    )
);


-- ---------------------------------------------------------
-- DATA QUALITY FLAG FACT TABLE
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS fact_quality_flag (

    quality_flag_id BIGINT PRIMARY KEY,

    observation_id BIGINT NOT NULL,

    rule_name VARCHAR NOT NULL,

    flag_type VARCHAR,

    severity VARCHAR,

    flag_value BOOLEAN DEFAULT TRUE,

    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    notes VARCHAR,

    FOREIGN KEY(observation_id)
        REFERENCES fact_observation(observation_id)
);