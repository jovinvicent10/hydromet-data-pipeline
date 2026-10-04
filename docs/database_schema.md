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

## 13. Schema rationale and tradeoffs

The implemented contract is [01_create_schema.sql](../sql/01_create_schema.sql), with loading in [load_duckdb.py](../src/database/load_duckdb.py).

| Choice | Rationale | Tradeoff or implementation limit |
|---|---|---|
| Long observation fact | A variable can be added without a new fact column; source-specific values remain distinguishable. | Seven values expand 73,048 wide rows to 511,336 facts and require joins or a pivot for daily consumers. Compare storage performance at equivalent grain. |
| Reusable dimensions | Dates, coordinates, units and provider descriptions are defined centrally. | Dimension metadata must remain consistent with the raw response; normalization alone does not verify it. |
| Integer primary keys plus natural-key uniqueness | Foreign keys provide referential integrity; the four-column fact uniqueness rule rejects duplicate observations. | `INSERT OR IGNORE` prevents repeated inserts but does not update a changed source value or preserve revisions. |
| Source in fact grain | Future providers can coexist for the same location, date and variable. | The current loader assigns `NASA_POWER` explicitly; multiple-source loading is not implemented. |
| Separate quality-flag table | One observation can have several rule findings without overwriting the measured value. | The schema defines this table, but the current loader does not populate it; warnings are currently report aggregates. |
| Wide daily serving mart | Simplifies analyst queries and ML preparation after the long-form load. | The daily SQL groups by source, but the monthly view omits source; it must be reviewed before additional sources are loaded. |

Location IDs are generated from sorted names, variable IDs from metadata order, date IDs as `YYYYMMDD`, and observation IDs from ordered row numbers offset by the current maximum. These are implementation keys, not durable source identifiers across arbitrary rebuilds or changing configurations. `ingested_at` is a database insertion timestamp, not the observation time or an API request identifier.

The current SQL permits nullable `value` and unit metadata and does not enforce meteorological bounds through CHECK constraints. Physical rules and completeness are evaluated in Python. Foreign keys and uniqueness therefore complement, rather than replace, the quality gate.

## 14. Connection to the three problems

- **Limited spatial coverage:** `dim_location` retains the configured coordinates and permits more points, but no area polygons, spatial weights or sampling-frame coverage measures are stored.
- **Single-source dependency:** `dim_source` preserves provider identity and supports a future common grain. It does not reconcile provider grids, units, temporal conventions or revisions automatically.
- **Statistical extremes:** `fact_quality_flag` can retain multiple findings per value. Observation-level flag loading, rule versioning and review decisions remain future work; no automatic extreme-value deletion is justified.

## 15. Metadata and provenance limitations

The preserved baseline payload labels `ALLSKY_SFC_SW_DWN` as `MJ/m^2/day`; `VARIABLE_METADATA` in the loader labels it `kWh/m2/day`. The loader melts values without a unit conversion, so the stored unit label is inconsistent with the raw values. Interpret baseline radiation using the raw response unit and resolve this discrepancy before energy calculations. No code is changed by this review.

The fact table has no request ID, raw-file checksum, run ID or source-product version. Traceability currently relies on the external manifest and dataset fingerprints, rather than a direct fact-to-request foreign key. Future provenance extensions should preserve these identifiers and provide stable dimension keys and explicit revision handling. See the [dictionary](data_dictionary.md), [lineage](data_lineage.md) and [datasheet](dataset_datasheet.md).

## Phase 2 implementation update

`load_fact_observation` now filters existing four-column natural keys before inserting. Tests verify existing observation IDs/values remain unchanged across partial completion and repeated loading. New loader runs also correct solar unit metadata to MJ/m²/day without converting the native values. This correction was executed in isolated databases; the historical original database was preserved.

`serving_refresh_metadata` is a new local table keyed by output name, recording a successful refresh timestamp and logical output fingerprint in the same transaction as the refreshed mart. External refresh metadata records failed attempts while retaining the last good timestamp/hash. The `fact_quality_flag` table still has no implemented IQR observation-loading path; row quarantine handles hard failures separately. See [executed evidence](phase2_implementation_and_evidence.md).
