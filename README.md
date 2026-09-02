# HydroMet-ETL

## A Reproducible Hydrometeorological Data Engineering Pipeline
for Climate and Agricultural Analytics in Tanzania

HydroMet-ETL is a semester project developed for DSAI 6226 –
Data Engineering and Analytics at the Nelson Mandela African
Institution of Science and Technology.

The project demonstrates a reproducible data-engineering workflow
for acquiring, validating, preserving, modelling, storing, and
benchmarking daily hydrometeorological data from NASA POWER.

## Current Project Status

Weeks 1–4 are implemented.

### Week 1 — Data Profiling and Problem Identification

The NASA POWER dataset was profiled for structural, temporal,
statistical, and engineering quality.

Validated baseline:

- 73,048 location-day records
- 8 configured locations
- 9,131 dates
- 2001-01-01 to 2025-12-31
- 7 meteorological variables
- 0 duplicate location-date observations
- 0 missing daily dates
- 0 ordinary missing meteorological values
- 12,529 IQR statistical flags

The three primary engineering limitations identified were:

1. limited point-based spatial representation;
2. single-source dependency;
3. need for systematic extreme-value quality assessment.

IQR flags are diagnostic signals and are not automatically treated
as erroneous observations.

### Week 2 — DuckDB Dimensional Model

A star-schema analytical model was implemented using:

- dim_location
- dim_date
- dim_variable
- dim_source
- fact_observation
- fact_quality_flag

The fact grain is:

One meteorological variable observed at one location on one date
from one source.

The 73,048 wide location-day records therefore produce:

73,048 × 7 = 511,336

observation-level facts.

This is a grain transformation, not duplication.

### Week 3 — Reproducible NASA POWER Ingestion

The ingestion subsystem includes:

- deterministic request identifiers;
- manifest-based provenance;
- serialized raw API payload preservation;
- SHA-256 integrity verification;
- validated raw-cache reuse;
- bounded retries with exponential backoff;
- transformed-data validation;
- deterministic output ordering;
- temporary-file safe writes;
- run-summary metadata.

Under the validated baseline, repeated execution produced the same
73,048-row interim dataset with SHA-256:

FDAB2668F283FE9531B39506EBB4325A462D9283ED5434D1CFAA67E8D743A8B9

### Week 4 — Storage Benchmarking

CSV, Parquet, and DuckDB were benchmarked using equivalent wide
representations of the same 73,048-row dataset.

Final median results:

| Metric | CSV | Parquet | DuckDB Wide |
|---|---:|---:|---:|
| Size MB | 5.976842 | 0.957728 | 1.261719 |
| Load s | 0.089954 | 0.004449 | 0.046459 |
| Filter s | 0.089598 | 0.005411 | 0.014790 |
| Aggregation s | 0.079378 | 0.012793 | 0.018984 |

The analytical DuckDB star schema was benchmarked separately because
it uses a different observation-level grain.

## Architecture

NASA POWER API
    ↓
Reproducible ingestion
    ↓
Serialized raw JSON + manifest + checksums
    ↓
Validated interim dataset
    ↓
Parquet + DuckDB star schema
    ↓
SQL / reporting / visualization / machine learning

## Setup

Create and activate a virtual environment:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

Install dependencies:

    pip install -r requirements.txt

## Run Ingestion

    python -m src.ingestion.ingest_nasa_power

## Verify Interim Dataset

    Get-FileHash data\interim\nasa_power_tanzania_daily.csv -Algorithm SHA256

## Create Database

    python -m src.database.create_database

## Load Database

    python -m src.database.load_duckdb

Expected database counts:

- 8 locations
- 9,131 dates
- 7 variables
- 1 source
- 511,336 observation facts

## Run Tests

    pytest -v

Last validated result:

17 tests passed.

## Run Benchmark

    python -m src.benchmarking.benchmark_storage

Benchmark outputs are written under:

    outputs/benchmarks/

and figures under:

    outputs/figures/

## Important Configuration Note

The intended project configuration and the validated Week 3 ingestion
baseline contain small coordinate differences for Morogoro and Songea.

Because coordinates contribute to deterministic request IDs and may
affect dataset fingerprints, these coordinates should not be silently
changed. A future controlled migration should establish one canonical
configuration, regenerate affected request IDs and raw acquisitions,
rebuild downstream datasets, rerun tests, and establish a new validated
baseline.

## Current Limitations

- Eight point locations do not provide full gridded coverage of Tanzania.
- NASA POWER is currently the only implemented data source.
- Full rerun/hash idempotency evidence has been demonstrated manually
  but should be converted into an automated integration test.
- The current observation ID strategy is appropriate for controlled
  batch loading but should be strengthened for concurrent/incremental
  production workloads.

## Future Development

Priority future work includes:

1. canonical configuration consolidation;
2. CHIRPS integration;
3. multi-source harmonization;
4. automated cross-source QA;
5. incremental ingestion;
6. partitioned Parquet storage at larger scale;
7. orchestration and monitoring when justified;
8. reproducible ML dataset generation.



## Week 5 — Cloud Data Engineering

Week 5 extended HydroMet-ETL into a cloud analytical environment
using the BigQuery Sandbox.

### BigQuery Environment

Project:

`hydromet-etl`

Dataset:

`hydromet`

Table:

`nasa_power_daily`

The uploaded table was validated using SQL and produced:

- 73,048 rows
- 8 locations
- start date: 2001-01-01
- end date: 2025-12-31

These results agree with the validated local dataset.

### Cloud Aggregate Query

Monthly mean daily precipitation was calculated by:

- location
- year
- month

The query produced 2,400 grouped records.

Estimated bytes processed:

`1.74 MB`

### Query Cost Experiment

A full-table query using:

```sql
SELECT *
FROM `hydromet-etl.hydromet.nasa_power_daily`;