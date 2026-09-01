# HydroMet-ETL Database Schema

## 1. Overview

HydroMet-ETL uses a dimensional analytical model for storing
hydrometeorological observations.

The schema is designed to support:

- historical climate analytics
- multi-location analysis
- multi-variable analysis
- multi-source data integration
- quality assurance
- reproducible downstream analytics
- machine-learning dataset generation

The central fact table is `fact_observation`, surrounded by reusable
dimensions describing date, location, meteorological variable and data
source.

---

## 2. Fact Table Grain

The grain of `fact_observation` is:

> One meteorological variable observed at one location on one date
> from one data source.

The source NASA POWER dataset is originally stored in wide format.
Each location-date row contains several meteorological variables.

The ETL pipeline converts this representation into long format before
loading the analytical database.

---

## 3. dim_location

Stores geographic information about observation locations.

### Primary Key

`location_id`

### Attributes

- location_name
- latitude
- longitude
- country

### Purpose

Location metadata are stored once rather than repeated in every
meteorological observation.

---

## 4. dim_date

Stores reusable calendar information.

### Primary Key

`date_id`

### Attributes

- full_date
- year
- quarter
- month
- month_name
- day
- day_of_year
- is_leap_year

### Purpose

The date dimension simplifies temporal aggregation and analysis.

Examples include:

- monthly rainfall
- annual temperature
- quarterly climate statistics
- seasonal analyses

---

## 5. dim_variable

Stores metadata describing meteorological variables.

### Primary Key

`variable_id`

### Attributes

- variable_code
- variable_name
- unit
- description

### Current variables

- T2M
- T2M_MIN
- T2M_MAX
- RH2M
- PRECTOTCORR
- WS2M
- ALLSKY_SFC_SW_DWN

### Purpose

The variable dimension allows additional environmental variables to
be added without altering the fact-table structure.

---

## 6. dim_source

Stores information about data providers and sources.

### Primary Key

`source_id`

### Attributes

- source_name
- provider
- temporal_resolution
- description

### Current source

NASA POWER

### Future sources may include

- CHIRPS
- ERA5-Land
- meteorological station observations

This dimension provides explicit data lineage.

---

## 7. fact_observation

Stores numerical hydrometeorological observations.

### Primary Key

`observation_id`

### Foreign Keys

- date_id
- location_id
- variable_id
- source_id

### Measures

- value

### Metadata

- ingested_at

### Uniqueness Rule

The following combination must be unique:

`date_id + location_id + variable_id + source_id`

This prevents duplicate observations at the defined fact-table grain.

---

## 8. fact_quality_flag

Stores quality-control results associated with individual observations.

### Primary Key

`quality_flag_id`

### Foreign Key

`observation_id`

### Attributes

- rule_name
- flag_type
- severity
- flag_value
- flagged_at
- notes

### Purpose

Potentially suspicious observations are flagged rather than
automatically deleted.

This is particularly important for hydrometeorological data because
extreme rainfall, temperature or wind observations may represent real
events rather than data errors.

---

## 9. Relationship Cardinalities

- dim_location 1:M fact_observation
- dim_date 1:M fact_observation
- dim_variable 1:M fact_observation
- dim_source 1:M fact_observation
- fact_observation 1:M fact_quality_flag

---

## 10. Analytical Design Choice

A dimensional/star-style model was selected because HydroMet-ETL is
primarily an analytical system rather than an online transactional
processing system.

The model provides:

- understandable analytical structure
- reusable dimensions
- reduced metadata duplication
- scalable addition of variables
- scalable addition of data sources
- explicit lineage
- database-level integrity constraints
- convenient aggregation

---

## 11. Current Scale

The current source dataset contains approximately 73,048 location-day
records.

Seven meteorological variables are transformed from wide to long form,
producing approximately 511,336 individual observations in
`fact_observation`.

---

## 12. Future Extension

The architecture is designed to support future integration of
additional hydrometeorological products.

For example:

NASA POWER + CHIRPS + ERA5-Land + station observations

can be harmonized into a common observation model while preserving
source information through `dim_source`.