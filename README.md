# HydroMet-ETL

## A Reproducible Hydrometeorological Data Engineering Pipeline for Climate and Agricultural Analytics in Tanzania

HydroMet-ETL is an end-to-end data engineering project developed for
**DSAI 6226 — Data Engineering and Analytics** at the Nelson Mandela
African Institution of Science and Technology (NM-AIST).

The project demonstrates how hydrometeorological data can be acquired,
validated, transformed, modeled, benchmarked, served, prepared for
machine learning, and orchestrated using reproducible data-engineering
practices.

The primary data source is the **NASA POWER Daily API**.

---

## 1. Project Motivation

Climate and agricultural analytics require more than simply
downloading weather data.

A usable data platform must address questions such as:

- Where did the data come from?
- Can ingestion be reproduced?
- Has the data been validated?
- Are repeated runs safe?
- What is the analytical grain?
- Which storage format is appropriate?
- Can analysts query the data easily?
- Can the data be prepared safely for machine learning?
- Can pipeline failures be detected?
- Can another engineer operate the system?

HydroMet-ETL addresses these questions through an integrated data
engineering pipeline.

---

## 2. Study Dataset

The project currently uses daily hydrometeorological observations for
eight configured locations in Tanzania.

The dataset covers:

```text
2001-01-01 to 2025-12-31
```

and contains:

```text
73,048 location-day records
```

across:

```text
8 locations
```

and:

```text
7 meteorological variables
```

The variables are:

| Variable | Description |
|---|---|
| T2M | Temperature at 2 metres |
| T2M_MIN | Minimum temperature at 2 metres |
| T2M_MAX | Maximum temperature at 2 metres |
| RH2M | Relative humidity at 2 metres |
| PRECTOTCORR | Corrected precipitation |
| WS2M | Wind speed at 2 metres |
| ALLSKY_SFC_SW_DWN | All-sky surface shortwave downward irradiance |

---

## 3. Configured Locations

The canonical project configuration contains eight Tanzanian
locations:

- Arusha
- Dodoma
- Dar es Salaam
- Morogoro
- Mbeya
- Mwanza
- Songea
- Tabora

The project is therefore a point-based hydrometeorological pipeline
and should not be interpreted as exhaustive spatial coverage of
Tanzania.

---

## 4. End-to-End Architecture

```text
                    NASA POWER DAILY API
                             |
                             v
                  +----------------------+
                  |   INGESTION LAYER    |
                  +----------------------+
                             |
                Raw JSON / SHA-256 / Manifest
                             |
                             v
                  73,048 location-day rows
                             |
                             v
                  +----------------------+
                  |  DATA QUALITY GATE   |
                  +----------------------+
                             |
              Schema / completeness / integrity
              physical rules / temporal checks
                             |
                             v
              +------------------------------+
              | STORAGE & ANALYTICAL MODEL   |
              +------------------------------+
                 |          |          |
                CSV      Parquet     DuckDB
                                        |
                                        v
                              Dimensional model
                                        |
                                 511,336 facts
                                        |
                                        v
                         +----------------------+
                         |   SERVING LAYER      |
                         +----------------------+
                              |            |
                              v            v
                         Daily mart    Monthly view
                          73,048         2,400
                              |
                              v
                         +----------------------+
                         |   ML PREPARATION     |
                         +----------------------+
                              |
                       Leakage-aware features
                              |
                 +------------+-------------+
                 |            |             |
               Train      Validation        Test
              52,352        8,768         11,680
                              |
                              v
                         +----------------------+
                         |    ORCHESTRATION     |
                         +----------------------+
                              |
                       Fail-fast execution
                       Logs / run summaries
                              |
                              v
                         AUTOMATED TESTS
```

---

## 5. Repository Structure

```text
hydromet-data-pipeline/
|
|-- configs/
|   `-- config.yaml
|
|-- data/
|   |-- external/
|   |-- interim/
|   |-- processed/
|   `-- raw/
|
|-- docs/
|   |-- analytics_serving.md
|   |-- cloud_architecture.md
|   |-- cold_run_checklist.md
|   |-- data_dictionary.md
|   |-- data_lineage.md
|   |-- data_problem_statement.md
|   |-- database_schema.md
|   |-- governance_and_quality.md
|   |-- hydromet_er_diagram.md
|   |-- ingestion_design.md
|   |-- ml_data_preparation.md
|   |-- orchestration_and_handover.md
|   |-- performance_optimization.md
|   |-- pipeline_design_document.md
|   `-- storage_benchmark_report.md
|
|-- metadata/
|   |-- ingestion_manifest.json
|   `-- ml_split_metadata.json
|
|-- notebooks/
|   |-- 01_initial_data_profiling.ipynb
|   `-- 02_advanced_data_profiling.ipynb
|
|-- outputs/
|   |-- benchmarks/
|   |-- cloud/
|   |-- figures/
|   |-- optimization/
|   |-- orchestration/
|   |-- quality/
|   `-- reports/
|
|-- scripts/
|   `-- run_pipeline.ps1
|
|-- sql/
|   |-- 01_create_schema.sql
|   |-- 02_validation_queries.sql
|   |-- 03_create_views.sql
|   |-- 04_bigquery_analysis.sql
|   `-- 05_create_serving_layer.sql
|
|-- src/
|   |-- benchmarking/
|   |-- database/
|   |-- ingestion/
|   |-- ml/
|   |-- optimization/
|   |-- orchestration/
|   |-- quality/
|   `-- serving/
|
|-- tests/
|
|-- requirements.txt
`-- README.md
```

---

## 6. Reproducible Ingestion

NASA POWER ingestion is implemented under:

```text
src/ingestion/
```

The ingestion workflow includes:

- deterministic request identifiers,
- raw payload preservation,
- SHA-256 fingerprints,
- ingestion manifests,
- retry handling,
- exponential backoff,
- cache reuse,
- deterministic output construction,
- validation of assembled outputs.

The ingestion design is idempotent: rerunning the same configured
workflow should not create duplicate observations.

A verified repeated ingestion produced the same dataset SHA-256:

```text
fdab2668f283fe9531b39506ebb4325a462d9283ed5434d1cfaa67e8d743a8b9
```

---

## 7. Data Quality

Data-quality validation is implemented in:

```text
src/quality/validate_hydromet.py
```

Checks include:

- required schema,
- missing values,
- duplicate location-date records,
- coordinate bounds,
- relative humidity bounds,
- non-negative precipitation,
- non-negative wind speed,
- non-negative solar radiation,
- temperature consistency,
- continuous dates,
- source consistency,
- dataset fingerprint,
- IQR-based statistical warnings.

Verified baseline:

```text
Rows:           73,048
Locations:      8
Dates:          9,131
Error failures: 0
IQR flags:      12,529
Status:         PASS
```

IQR flags are treated as statistical review indicators rather than
automatic data errors.

---

## 8. Dimensional Data Model

HydroMet-ETL uses a DuckDB analytical star schema.

Dimensions:

```text
dim_location
dim_date
dim_variable
dim_source
```

Fact tables:

```text
fact_observation
fact_quality_flag
```

The fact grain is:

> One meteorological variable observed at one location on one date
> from one source.

The wide dataset contains:

```text
73,048 rows
```

with seven meteorological variables.

After normalization to the observation grain:

```text
73,048 x 7 = 511,336 observations
```

The 511,336 records therefore represent a finer analytical grain, not
duplicate source rows.

---

## 9. Storage Benchmarking

HydroMet-ETL compared CSV, Parquet, and DuckDB using equivalent
representations of the same 73,048-row wide dataset.

Measured median results included:

| Format | Size | Full Load |
|---|---:|---:|
| CSV | 5.977 MB | 0.089954 s |
| Parquet | 0.958 MB | 0.004449 s |
| DuckDB wide | 1.262 MB | 0.046459 s |

Parquet provided substantial storage and analytical-read advantages
for this workload.

The analytical star schema was benchmarked separately because its
observation-level grain differs from the wide physical dataset.

---

## 10. Cloud Analytics

The project also evaluated analytical execution using Google
BigQuery.

A BigQuery table containing:

```text
73,048 rows
```

was used for validation and analytical queries.

Evidence includes:

- validation queries,
- monthly precipitation analysis,
- annual precipitation analysis,
- full-column scan estimates,
- projected-column scan estimates.

For one demonstrated comparison, estimated bytes processed decreased
from approximately:

```text
7.04 MB
```

for a full-column query to:

```text
1.74 MB
```

for a projected-column query.

These values are interpreted as estimated bytes processed rather than
monetary charges.

---

## 11. Governance and Lineage

The project documents lineage from:

```text
NASA POWER
     |
     v
Raw source payloads
     |
     v
Interim analytical dataset
     |
     v
Quality validation
     |
     v
DuckDB analytical model
     |
     v
Serving layer
     |
     v
ML-ready datasets
```

Governance controls include:

- source identification,
- deterministic ingestion,
- checksums,
- quality rules,
- validation evidence,
- metadata,
- documented analytical grain,
- version-controlled code,
- automated tests.

---

## 12. Analytics Serving Layer

The serving layer exposes:

```text
mart_weather_daily
```

and:

```text
vw_monthly_climate_summary
```

Verified outputs:

```text
Daily mart:   73,048 rows
Monthly view: 2,400 rows
```

The serving layer separates consumer-facing analytical structures from
the lower-level dimensional model.

---

## 13. ML Data Preparation

HydroMet-ETL demonstrates reproducible, leakage-aware preparation of
time-series data for machine learning.

The illustrative task is:

> Use weather information available up to day t to support prediction
> of precipitation on day t+1.

Features include:

- calendar features,
- precipitation lags,
- historical precipitation windows,
- historical temperature windows,
- historical humidity windows.

Historical rolling features are shifted before rolling to avoid
future-information leakage.

Final ML-ready observations:

```text
72,800
```

Chronological splits:

| Dataset | Rows | Period |
|---|---:|---|
| Train | 52,352 | 2001-01-31 to 2018-12-31 |
| Validation | 8,768 | 2019-01-01 to 2021-12-31 |
| Test | 11,680 | 2022-01-01 to 2025-12-30 |

No random train-test shuffling is used.

---

## 14. Performance Optimization

Performance profiling identified CSV loading as the slowest measured
operation in the Week 10 benchmark workload.

A controlled optimization converted the same 73,048-row,
12-column dataset to Parquet and verified logical equivalence.

Measured median loading time changed from:

```text
CSV:     0.085139 seconds
Parquet: 0.004924 seconds
```

This represented:

```text
17.29x load speedup
94.22% reduction in loading time
```

Storage changed from:

```text
CSV:     5.977 MB
Parquet: 0.958 MB
```

representing:

```text
83.98% storage reduction
```

These results apply to the controlled dataset-loading workload and
should not be interpreted as a 17.29x speedup of the entire pipeline.

---

## 15. Pipeline Orchestration

The operational pipeline can be executed through:

```powershell
python -m src.orchestration.run_pipeline
```

For an existing validated local dataset:

```powershell
python -m src.orchestration.run_pipeline --skip-ingestion
```

The orchestrator provides:

- ordered execution,
- fail-fast behavior,
- per-stage logging,
- return-code tracking,
- execution timing,
- machine-readable run summaries.

A verified downstream orchestration run completed successfully in:

```text
154.86 seconds
```

with six stages executed.

The database-load stage required:

```text
147.60 seconds
```

and therefore dominated the measured end-to-end runtime.

This has been retained as a candidate for future optimization.

---

## 16. Automated Testing

Run:

```powershell
python -m pytest -q
```

Current verified result:

```text
65 passed in 5.51s
```

Tests cover areas including:

- environment,
- ingestion,
- ingestion idempotency,
- database schema,
- database loading,
- data quality,
- analytics serving,
- ML preparation,
- optimization,
- orchestration.

---

## 17. Installation

Clone the repository:

```powershell
git clone https://github.com/jovinvicent10/hydromet-data-pipeline.git
cd hydromet-data-pipeline
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## 18. Running the Pipeline

### Full pipeline

```powershell
python -m src.orchestration.run_pipeline
```

### Use an existing ingested dataset

```powershell
python -m src.orchestration.run_pipeline --skip-ingestion
```

### Run automated tests

```powershell
python -m pytest -q
```

---

## 19. Scheduling

A Windows PowerShell launcher is provided:

```text
scripts/run_pipeline.ps1
```

It can be invoked manually:

```powershell
.\scripts\run_pipeline.ps1
```

or configured with Windows Task Scheduler.

The repository is scheduler-ready, but the presence of this script
does not by itself imply that an automatic schedule has been deployed.

---

## 20. Handover

Operational documentation is available in:

```text
docs/orchestration_and_handover.md
```

A cold-run checklist is available in:

```text
docs/cold_run_checklist.md
```

The cold-run procedure is intended to determine whether another team
member can operate the repository without undocumented assistance from
the original developer.

---

## 21. Key Engineering Lessons

HydroMet-ETL demonstrates that a data engineering project is more than
data collection.

The project integrates:

```text
Source acquisition
        +
Reproducibility
        +
Data quality
        +
Storage design
        +
Analytical modeling
        +
Performance
        +
Cloud analytics
        +
Governance
        +
Serving
        +
ML preparation
        +
Testing
        +
Orchestration
        +
Handover
```

The result is a reproducible analytical data pipeline rather than a
collection of disconnected scripts.

---

## 22. Known Limitations

Current limitations include:

1. The dataset represents eight configured point locations rather than
   complete spatial coverage of Tanzania.

2. The pipeline currently depends primarily on NASA POWER as its
   meteorological source.

3. Statistical extremes require contextual interpretation rather than
   automatic removal.

4. Fresh source ingestion depends on external API availability and
   network access.

5. The dimensional database-load stage dominates the observed
   downstream orchestration runtime.

6. Scheduling support has been prepared, but deployment frequency
   depends on operational requirements.

---

## 23. Future Work

Potential extensions include:

- incremental ingestion,
- changed-data detection,
- incremental DuckDB loading,
- additional meteorological sources,
- CHIRPS precipitation integration,
- gridded spatial datasets,
- automated cloud ingestion,
- workflow monitoring and alerting,
- CI/CD,
- containerization,
- richer metadata/catalog integration,
- expanded agricultural analytics,
- production ML pipelines.

---

## 24. Course Context

This project was developed as part of:

**DSAI 6226 — Data Engineering and Analytics**

MSc Data Science and Artificial Intelligence

The Nelson Mandela African Institution of Science and Technology (NM-AIST)

The project demonstrates the progressive application of data engineering concepts across the semester.