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

The saved ingestion summary and the current read-only audit identify this dataset SHA-256 (distinct paired-run hashes remain to be retained):

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

Earlier narrative result (not verified by the retained Phase 1 evidence):

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
## Documentation contracts

The original three problems are limited spatial coverage, single-source dependency and statistical extremes. Their evidence and acceptance criteria are documented in:

- [Problem statement](docs/data_problem_statement.md)
- [Schema rationale and implementation limits](docs/database_schema.md)
- [Artifact lineage](docs/data_lineage.md)
- [Metrics and saved baselines](docs/metrics.md)
- [Data dictionary](docs/data_dictionary.md)
- [Dataset datasheet](docs/dataset_datasheet.md)

The 2026-10-04 documentation review records a solar-unit metadata discrepancy, aggregate-only quality warnings and ML target-time boundary considerations. The metrics document uses saved machine-readable performance evidence where older narrative examples differ. Pipeline code is unchanged by this review.

## Phase 1 audit and lab submission status

**Team:** [MEMBER 1], [MEMBER 2], [MEMBER 3], [MEMBER 4]. **Submission date:** [SUBMISSION DATE]. **Unassigned owners:** [OWNER]. Repository: [HydroMet-ETL on GitHub](https://github.com/jovinvicent10/hydromet-data-pipeline).

The [lab requirements tracker](docs/lab_requirements_tracker.md) is the current requirement-by-requirement assessment. The [Phase 1 evidence audit](docs/phase1_evidence_audit.md) records read-only checks and reconciles historical claims. The retained regression log shows **54 passed in 2.35 s**; the earlier 65-pass narrative above remains unverified. No test suite or pipeline was rerun for this documentation update.

Submission documents: [concise problem statement](docs/problem_statement_one_page.md), [proposed cloud design](docs/cloud_design_one_page.md), [metrics](metrics.md), [DATASHEET](DATASHEET.md). Page counts for the two concise drafts still require final-format review.

### Users, decisions and the three problems

Climate researchers can compare monthly rainfall and temperature at the sampled points; agricultural analysts can investigate seasonal patterns and prepare research features; data engineers can audit acquisition and repeatability. These users receive evidence for exploratory historical analysis, not a validated national forecast or crop prescription. Eight points constrain spatial conclusions, one provider limits independent validation, and statistical extremes require review. Repeated rainfall sequences and cross-point identical values are supporting diagnostics rather than additional replacement problems.

### Why a star schema and a wide table coexist

A fact is one variable, at one point, on one date, from one source. Four dimensions store shared date, location, variable/unit and provider information. Integer primary keys identify dimension rows; foreign keys link facts; the unique date-location-variable-source combination prevents duplicate observations. `fact_quality_flag` can represent multiple findings per observation, but its local count is currently zero because the loader does not populate it.

Why not keep only one large table? A wide source table is convenient for seven fixed variables, but repeats metadata and requires new columns for new variables; the star model centralizes metadata and retains source in each observation's grain. A wide serving table remains useful: `mart_weather_daily` pivots the facts back into familiar columns so consumers can query weather without manually joining and pivoting. This combines extensible engineering storage with a simple analytical interface; it does not automatically implement multi-source harmonization. See [schema rationale](docs/database_schema.md).

### Direct ingestion and honest idempotency proof

From the repository root, with the existing environment activated:

```powershell
python -m src.ingestion.ingest_nasa_power
```

The script reuses checksum-verified raw responses for identical requests and reconstructs a sorted interim output. Retained August logs show 73,048 rows on the initial and repeated run, and cache reuse on repetition. The current CSV fingerprint matches saved ingestion and quality metadata. However, these files do not retain distinct per-run hashes and complete read/loaded/rejected accounting; the [tracker](docs/lab_requirements_tracker.md) therefore marks the required paired-run proof Partial. Phase 2 should retain both summaries, hashes, row/key counts and rejection reasons separately, rather than overwrite the first result. This command is documented here, not executed during Phase 1.

### Existing benchmark and required comparison

The following historical experiment uses the same wide dataset and monthly mean daily precipitation aggregate. Storage values are MiB (1024² bytes), despite the original CSV field name `storage_size_mb`; query times are medians over ten repetitions after one warmup.

| Existing path | Storage (MiB) | Full load (s) | Monthly aggregate (s) |
|---|---:|---:|---:|
| CSV + pandas | 5.976842 | 0.089954 | 0.079378 |
| Parquet + pandas | 0.957728 | 0.004449 | 0.012793 |
| DuckDB wide table | 1.261719 | 0.046459 | 0.018984 |

For this saved workload, Parquet read with pandas has the smallest file and lowest median loading and aggregation times. The existing comparison does not satisfy the required PostgreSQL and DuckDB-directly-over-Parquet paths. Complete those paths with the same dataset, aggregate, equivalent results and comparable measurement boundaries before making a three-engine lab verdict.

The separate optimization snapshot reports 19.16× isolated CSV-to-Parquet loading speedup, while older prose records 17.29×; preserve these as separate historical measurements. The saved downstream pipeline still spends 95.31% of runtime in database loading and excludes ingestion. Neither result establishes a cold full-pipeline speedup.

### Lineage, quality and personal-data assessment

The implemented lineage is NASA POWER → preserved serialized JSON/manifest → interim CSV → quality gate → DuckDB facts → daily mart → monthly view and ML features. BigQuery and storage experiments are separate branches. The [lineage register](docs/data_lineage.md) identifies physical artifacts and gaps, including missing fact-to-request keys and aggregate-only quality diagnostics.

The dataset contains daily environmental values, source labels and configured city-point coordinates, with no names, contact details, household identifiers or other documented fields identifying a person. Based on this schema, the weather dataset does not appear to be personal data under the identifiable-person definition in Tanzania's [Personal Data Protection Act, published by PDPC](https://www.pdpc.go.tz/media/media/THE_PERSONAL_DATA_PROTECTION_ACT.pdf). This dataset-specific assessment must be revisited if person-linked farm/household coordinates, user accounts or individual records are joined; it does not establish general institutional compliance. Credentials and user-identifying operational records are separate from the weather dataset and must stay out of a public submission.

### Refresh and ML limits to explain aloud

Observation coverage ends on 2025-12-31. A successful rebuild in October 2026 says when the archive was refreshed, not that October weather is present. Dedicated refresh metadata, a computed consumer freshness label and a deliberately failed-refresh demonstration remain missing.

NASA's [data FAQ](https://power.larc.nasa.gov/docs/faqs/data/) reports approximately 2–3 days of meteorological and 5–7 days of solar publication latency. Current ML exports include same-day weather and short historical windows, so they are illustrative retrospective preparation, not verified operational next-day predictors. The [ML availability matrix](docs/ml_data_preparation.md) reviews every exported column and the next-day targets that cross the feature-date split boundaries. Proposed predictor exclusions and boundary purges await Phase 2; no predictive model performance is claimed.

Phase 1 changes documentation only. Review it before authorizing Phase 2 technical work; no staging, commit or push has been performed.

## Executed Phase 2 and presentation handover

The [Phase 2 report](docs/phase2_implementation_and_evidence.md) contains measured outcomes and reproduction commands. Start your presentation with the [colleague guide](docs/colleague_presentation_guide.md); use the [current tracker matrix](docs/lab_requirements_tracker.md#current-phase-2-status--supersedes-the-phase-1-snapshot-above) to answer completion questions. [Manual submission guidance](docs/manual_github_submission.md) identifies files to include/exclude and preserves your control over staging, commits and pushes.

Executed results: two cached ingestion runs reproduce the original dataset hash; an isolated 11-row fixture produces four accepted/seven quarantined rows and a failing quality gate; all required benchmark engines return 2,400 equivalent groups. The full cached workflow changed from 589.800996 seconds to 29.499108 seconds with identical ordered measurement values/counts, an observed 19.99× improvement. Both comparison runs passed **69 tests**; historical figures elsewhere remain separate evidence.

New ML exports contain 72,728 rows and exclude unavailable same-day predictors while using conservative delayed histories and target-boundary purges. The lag assumption still needs actual publication-vintage evidence for operational use. Serving refresh now records success/failure and preserves the last good table after failure. The [generated dashboard](outputs/evidence/hydromet_dashboard.html) consumes the curated monthly view; a [failed-refresh snapshot](outputs/evidence/dashboard_failed_refresh.html) retains the demonstration.

The PostgreSQL benchmark ran in an isolated temporary cluster, which was stopped afterward; the original service remains available. Established raw/interim data, historical outputs and unrelated local edits were preserved. No dependencies were installed or changed. No staging, commit or push was performed. True cold API profiling, source-vintage verification, final page layout and completed cloud-job byte statistics remain unresolved; cloud deployment and predictive accuracy are not claimed.

Final handover verification: **70 tests passed in 8.04 seconds**, including refusal to benchmark against a different PostgreSQL cluster. The two profiling snapshots each ran 69 tests before this additional safety test was added; their historical timing/evidence is preserved. See `outputs/evidence/regression_final.txt` and the [changed-file list](outputs/evidence/changed_files.txt).
