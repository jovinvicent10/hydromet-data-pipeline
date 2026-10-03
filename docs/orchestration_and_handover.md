# HydroMet-ETL — Orchestration and Handover Guide

## 1. Purpose

This document describes how the HydroMet-ETL pipeline is operated,
monitored, recovered, scheduled, and handed over to another developer
or data engineer.

The objective of Week 11 is to move HydroMet-ETL from a collection of
individually executable components into a reproducible operational
pipeline.

The orchestration workflow coordinates:

1. NASA POWER ingestion
2. Data-quality validation
3. DuckDB schema creation
4. Analytical database loading
5. Analytics serving-layer creation
6. ML-ready data preparation
7. Regression verification

The pipeline follows the principle:

**Orchestrate → Fail Safely → Log → Verify → Schedule → Hand Over**

---

# 2. Pipeline Architecture

The operational workflow is:

```text
NASA POWER API
      |
      v
Idempotent Ingestion
      |
      v
Validated Interim Dataset
      |
      v
Data Quality Gate
      |
      v
DuckDB Schema
      |
      v
Dimensional Data Load
      |
      v
Analytics Serving Layer
      |
      v
ML Data Preparation
      |
      v
Regression Verification
      |
      v
Operational Outputs
```

Each stage must complete successfully before the next stage is
allowed to continue.

---

# 3. Main Pipeline Entry Point

The complete pipeline is orchestrated through:

```powershell
python -m src.orchestration.run_pipeline
```

The orchestrator is implemented in:

```text
src/orchestration/run_pipeline.py
```

The orchestrator reuses the existing tested modules instead of
duplicating their business logic.

---

# 4. Pipeline Stages

## Stage 1 — Ingestion

Command executed:

```powershell
python -m src.ingestion.ingest_nasa_power
```

Responsibilities:

- construct deterministic NASA POWER requests,
- reuse validated cached API responses,
- retry transient failures,
- preserve serialized source payloads,
- calculate checksums,
- maintain ingestion metadata,
- construct the validated interim dataset.

The ingestion stage is designed to be idempotent.

Repeated execution of the same configured ingestion should not create
duplicate location-date records.

---

## Stage 2 — Data Quality

Command:

```powershell
python -m src.quality.validate_hydromet --strict-baseline
```

The quality gate validates:

- required schema,
- missing values,
- duplicate location-date records,
- coordinate bounds,
- relative humidity bounds,
- non-negative precipitation,
- non-negative wind speed,
- non-negative solar radiation,
- temperature consistency,
- date continuity,
- source consistency,
- dataset fingerprint,
- statistical IQR warnings.

Structural or physically invalid conditions are treated separately
from statistical warnings.

IQR flags are therefore not automatically treated as data errors.

---

## Stage 3 — Database Schema

Command:

```powershell
python -m src.database.create_database
```

The analytical DuckDB environment contains dimensional tables,
observation facts, quality information, analytical views, and serving
objects.

Core dimensional tables include:

- `dim_location`
- `dim_date`
- `dim_variable`
- `dim_source`

Core fact tables include:

- `fact_observation`
- `fact_quality_flag`

---

## Stage 4 — Database Loading

Command:

```powershell
python -m src.database.load_duckdb
```

The original wide dataset contains:

- 73,048 location-day rows
- 7 meteorological variables

The analytical fact grain is:

> One meteorological variable observed at one location on one date
> from one source.

This produces:

```text
73,048 × 7 = 511,336
```

fact observations.

The increase from 73,048 to 511,336 records is therefore a change in
analytical grain, not accidental duplication.

---

# 5. Analytics Serving Layer

Command:

```powershell
python -m src.serving.create_serving_layer
```

The serving layer exposes:

```text
mart_weather_daily
```

and:

```text
vw_monthly_climate_summary
```

The daily mart contains:

- 73,048 records
- 8 locations
- unique date × location × source grain

The monthly climate view contains:

- 2,400 location-year-month records

These structures provide cleaner interfaces for analysts,
visualizations, reporting, and downstream ML preparation.

---

# 6. ML Data Preparation

Command:

```powershell
python -m src.ml.prepare_ml_data
```

The ML preparation stage demonstrates leakage-aware time-series
feature engineering.

The illustrative prediction task is:

> Use weather information available up to day t to support prediction
> of precipitation on day t+1.

The target is:

```text
target_precip_next_day
```

The feature engineering process includes:

- calendar variables,
- precipitation lags,
- historical rolling precipitation,
- historical rolling temperature,
- historical rolling relative humidity.

Rolling features are shifted before rolling so future information is
not incorporated into historical windows.

The final ML-ready dataset contains:

```text
72,800 rows
```

with chronological partitions:

| Split | Rows | Date Range |
|---|---:|---|
| Train | 52,352 | 2001-01-31 to 2018-12-31 |
| Validation | 8,768 | 2019-01-01 to 2021-12-31 |
| Test | 11,680 | 2022-01-01 to 2025-12-30 |

Random shuffling is not used.

---

# 7. Regression Verification

The final orchestration stage executes:

```powershell
python -m pytest -q
```

This verifies that the integrated pipeline has not broken previously
validated components.

Before Week 11 orchestration tests were added, the established project
regression suite contained 54 passing tests.

Week 11 adds orchestration-specific validation separately.

---

# 8. Verified End-to-End Orchestration Run

A downstream orchestration run was performed using:

```powershell
python -m src.orchestration.run_pipeline --skip-ingestion
```

Ingestion was intentionally skipped because the validated NASA POWER
dataset already existed locally.

The run produced:

| Stage | Status | Duration |
|---|---|---:|
| Data quality | SUCCESS | 1.30 s |
| Database schema | SUCCESS | 1.21 s |
| Database load | SUCCESS | 147.60 s |
| Serving layer | SUCCESS | 0.95 s |
| ML preparation | SUCCESS | 0.87 s |
| Regression tests | SUCCESS | 2.91 s |

Total orchestration duration:

```text
154.86 seconds
```

Pipeline status:

```text
SUCCESS
```

Six stages were executed.

The regression stage reported:

```text
54 passed
```

---

# 9. Operational Performance Observation

The end-to-end run revealed an important operational characteristic.

Database loading required:

```text
147.60 seconds
```

out of:

```text
154.86 seconds
```

for the entire run.

This represents approximately 95% of the measured orchestration
runtime.

This does not invalidate the earlier storage optimization work.

Week 10 optimized repeated analytical loading of the wide dataset,
where Parquet reduced median loading time relative to CSV.

The Week 11 observation concerns a different workload:

> constructing/loading the 511,336-row dimensional fact model.

The database-load stage is therefore a candidate for future pipeline
optimization.

No additional optimization is introduced during Week 11 because the
objective of this stage is orchestration and operational handover.

---

# 10. Failure Handling

The orchestrator uses sequential fail-fast execution.

For example:

```text
Ingestion
   |
 SUCCESS
   |
   v
Data Quality
   |
 FAILED
   X
Database Load
Serving Layer
ML Preparation
```

If a required stage returns a non-zero exit code:

1. the stage is marked `FAILED`,
2. the failure is written to the run summary,
3. downstream stages are not executed,
4. the pipeline exits with a failure code,
5. the operator can inspect the corresponding stage log.

This prevents known invalid upstream states from propagating through
the pipeline.

---

# 11. Logging

Individual orchestration logs are stored under:

```text
logs/orchestration/
```

Typical files include:

```text
data_quality.log
database_schema.log
database_load.log
serving_layer.log
ml_preparation.log
regression_tests.log
```

A complete pipeline execution summary is stored in:

```text
outputs/orchestration/pipeline_run_summary.json
```

The summary records:

- pipeline status,
- start timestamp,
- finish timestamp,
- total duration,
- executed stages,
- stage status,
- return codes,
- stage duration,
- corresponding log paths.

This provides basic operational observability and audit evidence.

---

# 12. Running Without Ingestion

If the validated dataset already exists, run:

```powershell
python -m src.orchestration.run_pipeline --skip-ingestion
```

This is useful for:

- development,
- testing,
- demonstrations,
- analytics rebuilding,
- ML preparation,
- environments without temporary network access.

It also avoids unnecessary external API calls.

---

# 13. Running Without Regression Tests

For selected development situations:

```powershell
python -m src.orchestration.run_pipeline --skip-tests
```

This should not be the preferred command for final validation.

Regression tests provide an important correctness gate.

---

# 14. Environment Setup for Handover

A new developer should first clone the repository.

Example:

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

Install the project's required Python dependencies using the
repository's dependency specification.

The operator should verify that the active Python interpreter belongs
to the virtual environment before running the pipeline.

---

# 15. Pre-Run Checklist

Before running the pipeline, verify:

- Python environment is activated.
- Required Python dependencies are installed.
- Configuration files are available.
- Required source/interim data are available, or network ingestion is
  intended.
- DuckDB storage location is writable.
- Output directories are writable.
- Sufficient local disk space is available.

Then run the regression suite when appropriate:

```powershell
python -m pytest -v
```

---

# 16. Cold-Run Handover Procedure

A cold-run exercise tests whether another team member can operate the
project without relying on undocumented knowledge from the original
developer.

Recommended procedure:

1. Clone the repository into a fresh directory.
2. Create a new virtual environment.
3. Install project dependencies.
4. Review the README and this handover guide.
5. Confirm configuration.
6. Obtain or regenerate required data assets.
7. Run automated tests.
8. Run the orchestrator.
9. Inspect the run summary.
10. Inspect stage logs.
11. Confirm analytical serving outputs.
12. Confirm ML-ready outputs.

A successful cold run demonstrates that operational knowledge has been
transferred from the developer into code and documentation.

---

# 17. Scheduling

The orchestrator provides a single command suitable for external
scheduling:

```powershell
python -m src.orchestration.run_pipeline
```

On Windows, this command can be invoked through Windows Task Scheduler.

A scheduled task should:

1. use the Python interpreter inside the project virtual environment,
2. use the repository root as the working directory,
3. invoke the orchestration module,
4. run under an account with appropriate file/network permissions,
5. retain orchestration logs for troubleshooting.

An example program path is conceptually:

```text
<project>\.venv\Scripts\python.exe
```

with arguments:

```text
-m src.orchestration.run_pipeline
```

and working directory:

```text
<project-root>
```

Scheduling frequency should reflect the actual data-refresh
requirement rather than being selected arbitrarily.

---

# 18. Recovery Procedure

If the pipeline fails:

### Step 1

Inspect:

```text
outputs/orchestration/pipeline_run_summary.json
```

Identify the failed stage.

### Step 2

Open its log under:

```text
logs/orchestration/
```

### Step 3

Resolve the underlying problem.

Examples include:

- unavailable source data,
- corrupted input,
- validation failure,
- missing dependency,
- file permission issue,
- unavailable database,
- schema inconsistency.

### Step 4

Run the failing component independently if debugging is required.

For example:

```powershell
python -m src.quality.validate_hydromet --strict-baseline
```

### Step 5

Once corrected, rerun the orchestrator.

Because the ingestion design is idempotent and database loading
protects its analytical grain, rerunning is safer than manually
editing intermediate outputs.

---

# 19. Scheduling vs Orchestration

Scheduling and orchestration solve different problems.

**Orchestration answers:**

> In what order should pipeline components execute, and what happens
> when one fails?

**Scheduling answers:**

> When should the orchestrated pipeline execute?

HydroMet-ETL therefore separates these concerns.

```text
Scheduler
   |
   v
Orchestrator
   |
   +-- Ingestion
   +-- Quality
   +-- Database
   +-- Serving
   +-- ML preparation
   +-- Tests
```

---

# 20. Reproducibility

The project combines several reproducibility controls:

- Git version control,
- deterministic ingestion request identifiers,
- source checksums,
- ingestion manifests,
- idempotent ingestion,
- validation rules as code,
- deterministic database grain,
- chronological ML splits,
- automated tests,
- performance benchmark metadata,
- orchestration logs,
- machine-readable run summaries.

Together these controls make the pipeline easier to reproduce,
inspect, audit, and hand over.

---

# 21. Known Operational Considerations

## Database load time

The dimensional database-loading stage currently dominates the
observed full-pipeline runtime.

Future work could investigate:

- bulk-loading strategies,
- direct DuckDB transformations,
- Parquet-to-DuckDB loading,
- avoiding unnecessary reconstruction,
- incremental loading,
- changed-data detection.

Any future optimization should use the same principle applied during
Week 10:

**Measure → Optimize → Re-measure → Verify correctness.**

## External API dependency

A fresh NASA POWER ingestion requires network access and depends on
the availability of the external API.

Cached validated raw payloads reduce unnecessary repeated requests.

## Point-based spatial representation

The current dataset represents eight configured Tanzanian locations.

It should not be interpreted as exhaustive spatial coverage of the
country.

---

# 22. Handover Acceptance Checklist

The receiving team member should be able to explain:

- where the source data originate,
- why raw data are preserved,
- why checksums are used,
- what idempotency means,
- what the star-schema grain represents,
- why 73,048 rows become 511,336 observations,
- why IQR flags are not automatically errors,
- why Parquet is used for analytical efficiency,
- what the serving layer provides,
- how ML leakage is controlled,
- why temporal splitting is used,
- how pipeline failures are handled,
- where logs are stored,
- how the orchestrator is executed,
- how scheduling differs from orchestration.

The receiving team member should also be able to run the project
without requiring undocumented commands from the original developer.

---

# 23. Week 11 Outcome

Week 11 transformed HydroMet-ETL from individually executable modules
into an operationally coordinated pipeline.

The project now provides:

- ordered pipeline execution,
- fail-fast behavior,
- per-stage logs,
- machine-readable execution summaries,
- selective execution options,
- regression verification,
- scheduling guidance,
- recovery instructions,
- cold-run procedures,
- handover documentation.

The verified downstream orchestration run completed successfully in
154.86 seconds and preserved all previously validated outputs.

This completes the orchestration and handover stage of the
HydroMet-ETL project.