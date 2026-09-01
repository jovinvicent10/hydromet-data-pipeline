# HydroMet-ETL Entity Relationship Diagram

```mermaid
erDiagram

    DIM_LOCATION ||--o{ FACT_OBSERVATION : "has"
    DIM_DATE ||--o{ FACT_OBSERVATION : "occurs on"
    DIM_VARIABLE ||--o{ FACT_OBSERVATION : "describes"
    DIM_SOURCE ||--o{ FACT_OBSERVATION : "provides"

    FACT_OBSERVATION ||--o{ FACT_QUALITY_FLAG : "may have"

    DIM_LOCATION {
        INTEGER location_id PK
        VARCHAR location_name
        DOUBLE latitude
        DOUBLE longitude
        VARCHAR country
    }

    DIM_DATE {
        INTEGER date_id PK
        DATE full_date
        INTEGER year
        INTEGER quarter
        INTEGER month
        VARCHAR month_name
        INTEGER day
        INTEGER day_of_year
        BOOLEAN is_leap_year
    }

    DIM_VARIABLE {
        INTEGER variable_id PK
        VARCHAR variable_code
        VARCHAR variable_name
        VARCHAR unit
        VARCHAR description
    }

    DIM_SOURCE {
        INTEGER source_id PK
        VARCHAR source_name
        VARCHAR provider
        VARCHAR temporal_resolution
        VARCHAR description
    }

    FACT_OBSERVATION {
        BIGINT observation_id PK
        INTEGER date_id FK
        INTEGER location_id FK
        INTEGER variable_id FK
        INTEGER source_id FK
        DOUBLE value
        TIMESTAMP ingested_at
    }

    FACT_QUALITY_FLAG {
        BIGINT quality_flag_id PK
        BIGINT observation_id FK
        VARCHAR rule_name
        VARCHAR flag_type
        VARCHAR severity
        BOOLEAN flag_value
        TIMESTAMP flagged_at
        VARCHAR notes
    }