# HydroMet-ETL Data Lineage

## 1. Purpose

Data lineage describes where data comes from, what happens to it,
where it is stored, and which downstream systems consume it.

HydroMet-ETL documents lineage so that every analytical result can
be traced back to its original source and transformation process.

---

## 2. End-to-End Lineage

NASA POWER Daily API
        |
        v
API Request Specification
        |
        | location
        | coordinates
        | date range
        | parameters
        v
Deterministic Request ID
        |
        v
Serialized NASA POWER JSON Payload
        |
        | SHA-256 checksum
        v
Ingestion Manifest
        |
        v
Transformation to Tabular Records
        |
        v
Validation at Ingestion
        |
        v
data/interim/nasa_power_tanzania_daily.csv
        |
        +------------------------------+
        |                              |
        v                              v
Data Profiling                  Data Quality as Code
        |                              |
        |                              v
        |                   outputs/quality/
        |                              |
        +---------------+--------------+
                        |
                        v
               Analytical Storage
                        |
             +----------+----------+
             |                     |
             v                     v
          Parquet               DuckDB
                                   |
                                   v
                           Star Schema / SQL
                                   |
                                   v
                               BigQuery
                                   |
                                   v
                         Analytics / Reports
                                   |
                                   v
                          Future ML Features

---

## 3. Source

Primary source:

NASA POWER Daily API

Current source identifier:

`NASA_POWER`

The pipeline retrieves daily meteorological observations for
configured Tanzanian locations.

---

## 4. Raw Layer

Raw NASA POWER payloads are stored as serialized JSON.

The ingestion manifest records metadata including:

- request ID;
- location;
- coordinates;
- requested date range;
- parameters;
- raw file path;
- checksum;
- status.

The SHA-256 fingerprint provides evidence that the preserved file has
not changed unexpectedly.

---

## 5. Interim Layer

Transformed observations are combined into:

`data/interim/nasa_power_tanzania_daily.csv`

Current validated baseline:

- 73,048 location-day records;
- 8 locations;
- 9,131 dates;
- 2001-01-01 to 2025-12-31;
- 7 meteorological variables.

---

## 6. Quality Layer

Quality checks are implemented in:

`src/quality/validate_hydromet.py`

Outputs are written to:

`outputs/quality/data_quality_report.json`

and:

`outputs/quality/data_quality_summary.csv`

Quality rules cover:

- schema;
- completeness;
- uniqueness;
- coordinates;
- meteorological physical validity;
- temperature consistency;
- temporal coverage;
- source consistency;
- statistical diagnostics.

IQR statistical flags are warnings rather than automatic errors.

---

## 7. Analytical Database

The interim wide dataset is transformed into a DuckDB dimensional
model.

The observation fact grain is:

one meteorological variable
observed at one location
on one date
from one source.

The validated 73,048 wide rows therefore produce:

73,048 × 7 = 511,336

observation facts.

This is a change in grain, not duplication.

---

## 8. Cloud Analytical Layer

For Unit 5, the HydroMet dataset was also loaded into BigQuery.

Project:

`hydromet-etl`

Dataset:

`hydromet`

Table:

`nasa_power_daily`

BigQuery validation confirmed:

- 73,048 rows;
- 8 locations;
- 2001-01-01 to 2025-12-31.

---

## 9. Downstream Consumers

Current and future consumers include:

- SQL analytics;
- climate summaries;
- reports;
- dashboards;
- machine-learning feature tables;
- agricultural decision-support applications.

Downstream consumers should use validated analytical datasets rather
than directly reading raw API payloads.

---

## 10. Lineage Principle

Every important output should answer:

1. Where did this data originate?
2. Which request produced it?
3. Which transformations were applied?
4. Which validation rules were executed?
5. Which physical dataset was used?
6. Which analytical table was queried?
7. Which downstream output consumed it?

This makes HydroMet-ETL auditable, reproducible, and easier to debug.