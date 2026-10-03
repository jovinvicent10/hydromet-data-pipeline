# HydroMet-ETL Pipeline Design Document

## A Reproducible Hydrometeorological Data Engineering Pipeline for Climate and Agricultural Analytics in Tanzania

**Course:** DSAI 6226 – Data Engineering and Analytics  
**Institution:** The Nelson Mandela African Institution of Science and Technology  
**Programme:** MSc Data Science and Artificial Intelligence  

---

# 1. Introduction

HydroMet-ETL is a reproducible hydrometeorological data engineering
pipeline developed as part of DSAI 6226 – Data Engineering and
Analytics.

The purpose of the project is to demonstrate how external
hydrometeorological data can be systematically acquired, validated,
transformed, stored, tested and prepared for downstream analytics.

The current implementation uses the NASA POWER Daily API as the
primary data source and focuses on selected locations in Tanzania.

Rather than treating data acquisition as a one-time download,
HydroMet-ETL treats the complete process as a reproducible data
engineering pipeline.

The pipeline therefore addresses:

- data acquisition;
- raw-data preservation;
- reproducibility;
- idempotency;
- data validation;
- provenance;
- analytical modelling;
- efficient storage;
- cloud analytics;
- automated testing; and
- data lineage.

---

# 2. Problem Statement

Hydrometeorological information is important for applications such
as:

- agricultural planning;
- climate analysis;
- crop monitoring;
- drought assessment;
- disease-risk modelling;
- environmental monitoring; and
- early-warning systems.

However, obtaining data from an API is only the first step.

A trustworthy analytical system must also ensure that data can be:

1. acquired consistently;
2. reproduced later;
3. validated automatically;
4. traced to its source;
5. stored efficiently;
6. queried easily;
7. rerun without creating duplicates; and
8. extended when additional data sources become available.

HydroMet-ETL therefore addresses the following engineering question:

> How can hydrometeorological observations from external data
> services be transformed into a reproducible, validated, traceable
> and analytically useful data asset?

---

# 3. Project Objectives

## 3.1 Main Objective

To design and implement a reproducible hydrometeorological data
engineering pipeline for acquiring, validating, storing and serving
climate data for analytical and future machine-learning applications.

## 3.2 Specific Objectives

The project aims to:

1. acquire daily meteorological data from NASA POWER;
2. preserve source payloads and acquisition metadata;
3. implement repeatable and idempotent ingestion;
4. validate data using automated quality rules;
5. design an analytical data model using DuckDB;
6. compare CSV, Parquet and DuckDB storage performance;
7. demonstrate cloud analytics using BigQuery;
8. document data provenance and lineage;
9. implement automated tests for important pipeline components; and
10. provide a foundation for future agricultural and climate
    analytics.

---

# 4. Data Source

The current primary data source is the NASA POWER Daily API.

NASA POWER provides meteorological and solar variables that can be
requested programmatically for specified geographic coordinates and
time periods.

The HydroMet-ETL pipeline currently covers the period:

**1 January 2001 to 31 December 2025**

for eight configured Tanzanian locations.

The current validated dataset contains:

- 73,048 location-day records;
- 8 locations;
- 9,131 unique dates; and
- 7 meteorological variables.

---

# 5. Meteorological Variables

The pipeline currently retrieves the following variables:

| Variable | Description |
|---|---|
| T2M | Air temperature at 2 metres |
| T2M_MIN | Minimum air temperature at 2 metres |
| T2M_MAX | Maximum air temperature at 2 metres |
| RH2M | Relative humidity at 2 metres |
| PRECTOTCORR | Corrected precipitation |
| WS2M | Wind speed at 2 metres |
| ALLSKY_SFC_SW_DWN | All-sky surface shortwave radiation |

These variables provide a useful hydrometeorological foundation for
climate and agricultural analysis.

---

# 6. Current Study Locations

The project currently contains eight Tanzanian locations:

- Arusha;
- Dodoma;
- Dar es Salaam;
- Morogoro;
- Mbeya;
- Mwanza;
- Songea; and
- Tabora.

The current dataset represents point-based observations for these
configured locations and should not be interpreted as complete
spatial coverage of Tanzania.

---

# 7. End-to-End Pipeline Architecture

The HydroMet-ETL architecture can be represented as:

NASA POWER Daily API

↓

Configured API Request

↓

Deterministic Request ID

↓

API Ingestion

↓

Serialized Raw JSON Payload

↓

SHA-256 Checksum

↓

Ingestion Manifest

↓

Transformation to Tabular Data

↓

Ingestion Validation

↓

Interim Daily Dataset

↓

Data Quality Validation

↓

Analytical Storage

↓

Parquet / DuckDB

↓

BigQuery Cloud Analytics

↓

Reports / Analytics / Future ML Applications

This architecture separates acquisition, validation, storage and
consumption into clearly defined stages.

---

# 8. Data Acquisition Design

The main ingestion implementation is located in:

`src/ingestion/ingest_nasa_power.py`

The ingestion component is responsible for:

- constructing API requests;
- retrieving NASA POWER observations;
- handling temporary failures;
- preserving serialized API payloads;
- calculating checksums;
- maintaining an ingestion manifest;
- transforming responses into tabular data; and
- producing the combined interim dataset.

The ingestion pipeline includes retry behaviour with exponential
backoff to handle temporary request failures.

---

# 9. Idempotent Ingestion

An important design requirement is idempotency.

An idempotent pipeline can be rerun without producing unwanted
duplicate effects.

HydroMet-ETL creates a deterministic request identifier using
information such as:

- data source;
- location;
- coordinates;
- requested date range; and
- requested parameters.

When a previously successful request exists and its raw file passes
checksum validation, the pipeline can reuse the existing validated
raw data rather than unnecessarily downloading the same data again.

Manual rerun validation demonstrated that repeated ingestion produced
the same:

- 73,048 records; and
- SHA-256 dataset fingerprint.

This provides evidence that the current ingestion process is
repeatable.

---

# 10. Raw Data and Provenance

NASA POWER API responses are preserved as serialized JSON files.

The project also maintains an ingestion manifest containing
information such as:

- request ID;
- source;
- location;
- latitude;
- longitude;
- date range;
- requested parameters;
- raw file path;
- checksum;
- request status; and
- verification information.

This metadata provides provenance for the acquired dataset.

---

# 11. Dataset Integrity

HydroMet-ETL uses SHA-256 hashing to detect unexpected file changes.

The current validated interim dataset has the SHA-256 fingerprint:

`fdab2668f283fe9531b39506ebb4325a462d9283ed5434d1cfaa67e8d743a8b9`

A checksum provides evidence that the physical file has not changed.

However, checksum integrity does not automatically prove that the
scientific observations are valid.

Scientific and structural validity are assessed separately using
data-quality rules.

---

# 12. Initial Data Profiling

Initial profiling was performed to understand the structure and
quality of the acquired dataset.

The profiling identified:

- 73,048 records;
- 8 locations;
- date coverage from 2001-01-01 to 2025-12-31;
- no exact duplicate records;
- no duplicate location-date records;
- no missing daily dates;
- no ordinary missing meteorological values;
- no invalid coordinates under the implemented coordinate checks;
- no negative precipitation;
- no negative wind-speed values;
- no negative solar-radiation values;
- no relative-humidity values outside the implemented valid range;
- no temperature-order consistency violations.

The dataset was therefore structurally clean under the implemented
checks.

---

# 13. Statistical Outlier Assessment

Advanced profiling identified 12,529 observations outside
1.5-times-IQR statistical ranges across the meteorological variables.

These observations were not automatically deleted.

This is because:

**statistical outlier does not necessarily mean invalid observation.**

Hydrometeorological datasets may contain genuine extreme events such
as unusually high rainfall or temperature.

HydroMet-ETL therefore distinguishes between:

- invalid observations;
- missing observations;
- statistical outliers;
- extreme environmental events; and
- broader dataset limitations.

Statistical outliers are treated as diagnostic warnings requiring
investigation rather than automatic errors.

---

# 14. Data Modelling

HydroMet-ETL uses DuckDB as the local analytical database.

A dimensional star-schema approach was selected because the primary
workload is analytical.

The model contains:

- `dim_location`
- `dim_date`
- `dim_variable`
- `dim_source`
- `fact_observation`
- `fact_quality_flag`

The central fact table is:

`fact_observation`

---

# 15. Fact Table Grain

The grain of `fact_observation` is:

> One meteorological variable observed at one location on one date
> from one source.

Defining the grain explicitly is important because it determines what
one fact-table row represents.

The original wide dataset contains 73,048 location-day records.

Each record contains seven meteorological variables.

Therefore the long analytical representation contains:

73,048 × 7 = 511,336 observations.

The increase from 73,048 to 511,336 rows is therefore a change in
data grain rather than duplication.

---

# 16. Dimension Tables

## dim_location

Describes where an observation occurred.

Examples of attributes include:

- location name;
- latitude;
- longitude; and
- country.

## dim_date

Describes when an observation occurred.

Attributes include:

- full date;
- year;
- quarter;
- month;
- month name;
- day;
- day of year; and
- leap-year indicator.

## dim_variable

Describes what was measured.

Examples include:

- variable code;
- variable name;
- unit; and
- description.

## dim_source

Describes where the observation originated.

The current implemented source is NASA POWER.

The architecture allows additional sources to be added later.

---

# 17. Quality Flag Architecture

The database also contains:

`fact_quality_flag`

This table is designed to allow observations to be associated with
quality information without deleting the original measurement.

This is useful for environmental data because unusual observations
may still be scientifically meaningful.

---

# 18. Data Quality as Code

Data-quality validation is implemented in:

`src/quality/validate_hydromet.py`

The validator checks areas including:

- required schema;
- missing values;
- duplicate location-date records;
- coordinate validity;
- relative-humidity range;
- negative precipitation;
- negative wind speed;
- negative solar radiation;
- temperature consistency;
- temporal coverage;
- source consistency; and
- IQR statistical diagnostics.

The latest strict-baseline validation produced:

- Overall status: PASS
- Rows: 73,048
- Locations: 8
- Dates: 9,131
- Error failures: 0
- IQR statistical flags: 12,529

This converts data quality from a manual activity into repeatable
pipeline logic.

---

# 19. Error and Warning Strategy

HydroMet-ETL distinguishes between errors and warnings.

## ERROR

An error represents a structural or physical rule violation.

Examples include:

- duplicate location-date records;
- negative precipitation;
- invalid coordinates;
- relative humidity outside the implemented valid range; or
- inconsistent minimum, mean and maximum temperatures.

## WARNING

A warning represents something unusual that may still be valid.

IQR statistical flags are therefore classified as warnings.

This prevents legitimate extreme environmental observations from
being automatically discarded.

---

# 20. Storage Architecture

HydroMet-ETL evaluates multiple storage approaches.

## CSV

CSV is useful for:

- interoperability;
- portability; and
- human-readable data exchange.

However, CSV requires text parsing and does not provide efficient
columnar analytical storage.

## Parquet

Parquet provides:

- columnar storage;
- compression;
- typed values; and
- efficient analytical column selection.

## DuckDB

DuckDB provides:

- embedded analytical SQL;
- relational modelling;
- local analytical processing; and
- convenient integration with files such as Parquet.

The project therefore treats Parquet and DuckDB as complementary
rather than mutually exclusive technologies.

---

# 21. Storage Benchmark

A controlled benchmark compared equivalent wide representations of
the same 73,048-row dataset.

Median results were:

| Metric | CSV | Parquet | DuckDB Wide |
|---|---:|---:|---:|
| Storage size (MB) | 5.976842 | 0.957728 | 1.261719 |
| Load time (s) | 0.089954 | 0.004449 | 0.046459 |
| Filter time (s) | 0.089598 | 0.005411 | 0.014790 |
| Aggregation time (s) | 0.079378 | 0.012793 | 0.018984 |

Parquet provided substantial storage reduction and fast analytical
performance for this dataset.

The DuckDB star schema was benchmarked separately because its
observation-level representation differs from the original wide
dataset.

This avoids making an unfair comparison between storage formats with
different logical representations.

---

# 22. Why Spark Was Not Selected

The current HydroMet dataset is relatively small and can be processed
comfortably using Pandas, Parquet and DuckDB on a single machine.

Introducing Spark at the current scale would add distributed-system
complexity without a demonstrated requirement.

Spark would become more appropriate if future workloads involved:

- substantially larger data volumes;
- many files;
- distributed transformations;
- large-scale spatial or temporal datasets; or
- workloads that exceed single-machine resources.

The technology decision is therefore based on workload requirements
rather than using distributed technology unnecessarily.

---

# 23. Cloud Data Engineering

The project also demonstrates cloud analytics using Google BigQuery.

The current BigQuery resources are:

Project:

`hydromet-etl`

Dataset:

`hydromet`

Table:

`nasa_power_daily`

Validation in BigQuery confirmed:

- 73,048 rows;
- 8 locations;
- minimum date 2001-01-01;
- maximum date 2025-12-31.

---

# 24. Cost-Aware Cloud Querying

BigQuery demonstrates why analytical query design matters in cloud
systems.

A full-column query over the current table showed an estimated
processing amount of approximately:

7.04 MB.

A query selecting only:

- date;
- location; and
- PRECTOTCORR

showed an estimate of approximately:

1.74 MB.

This represents approximately a 75.3% reduction in estimated bytes
processed.

This illustrates the importance of selecting only the columns
required by an analytical workload.

---

# 25. Proposed Cloud Architecture

The proposed cloud architecture is:

NASA POWER API

↓

Scheduled or Serverless Python Ingestion

↓

Cloud Object Storage Raw Zone

↓

Raw JSON + Manifest + Checksums

↓

Validation and Transformation

↓

Curated Parquet

↓

BigQuery

↓

Dashboards / Reports / Machine Learning

The current project demonstrates the BigQuery analytical component,
while the complete cloud ingestion architecture represents a future
production design.

---

# 26. Data Lineage

Data lineage describes how data moves from its source to downstream
consumers.

HydroMet-ETL lineage is:

NASA POWER API

↓

Request Specification

↓

Deterministic Request ID

↓

Serialized Raw JSON

↓

Manifest + SHA-256

↓

Transformation

↓

Interim CSV

↓

Data Quality Validation

↓

Parquet / DuckDB

↓

BigQuery

↓

Analytics / Future Machine Learning

Detailed lineage documentation is available in:

`docs/data_lineage.md`

---

# 27. Testing Strategy

Automated testing is used to protect important pipeline assumptions.

The current test suite covers:

- ingestion output;
- ingestion invariants;
- database schema;
- database loading; and
- data quality.

The latest complete test execution produced:

**25 passed**

This confirms that the Unit 6 quality implementation did not break
the previously validated ingestion and database components.

---

# 28. Reproducibility

Important pipeline operations can be executed using documented
commands.

Examples include:

```bash
python -m src.ingestion.ingest_nasa_power

python -m src.quality.validate_hydromet --strict-baseline

python -m src.database.create_database

python -m src.database.load_duckdb

python -m src.benchmarking.benchmark_storage

python -m pytest -v