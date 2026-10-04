# HydroMet-ETL: Step-by-Step Record and Learning Guide

This guide explains the work completed in this project session, why each change was made, where to study it and how to inspect its evidence. It separates the original project from my contributions: I inspected and extended an existing NASA POWER pipeline; I did not create its original dataset or every existing component.

Work followed four phases: documentation and read-only inspection; implementation after your approval; a colleague presentation guide; and manual submission guidance. Your initial instruction to leave pipeline code alone was respected during the documentation phase. Code work began in the later authorized implementation phase.

## How to use this guide

Read the steps in order. For each step, open the named file, explain the idea in your own words, and inspect the evidence before running anything. Commands below assume PowerShell in the project root. Read-only examples inspect retained evidence; reproduction commands create outputs and are identified separately.

The project flow is:

```text
NASA POWER → retained raw JSON → checked daily CSV
           → DuckDB dimensions and measurement facts
           → daily serving mart → monthly summary → dashboard
                                → delayed-history ML exports
```

Checks, provenance and evidence accompany the flow. The isolated lab driver exercises failure handling and performance without replacing the established data artifacts.

## Step 1 — Inspect the existing project and protect your work

**What I did:** Read documentation, source modules, saved reports, manifests and repository status. Identified pre-existing edits in the profiling notebook and original quality report and left them untouched. Checked for repository instructions and prepared update packages; none were found in the inspected inventory.

**Why:** A project can contain work that belongs to someone else or evidence from earlier runs. Editing first can destroy that history or make it difficult to tell which result belongs to which change.

**Learn:** A working tree contains local changes; the Git index contains staged changes. Inspect both before changing a shared project.

```powershell
git status --short
git diff --stat
git diff --cached --name-only
```

**Read:** [Phase 1 audit](phase1_evidence_audit.md). Later experiments fingerprinted protected artifacts before and after execution; see [preservation proof](../outputs/evidence/preservation_check.json). A SHA-256 fingerprint detects a file change; it does not prove meteorological accuracy.

## Step 2 — Verify what data already existed

**What I did:** Read the retained CSV, recomputed its fingerprint, checked dates, locations and duplicate keys, inspected DuckDB in read-only mode, and checked all eight raw payload fingerprints against the manifest.

| Representation | Verified size | Meaning |
|---|---:|---|
| Daily CSV | 73,048 rows | Eight points × 9,131 dates |
| Observation facts | 511,336 rows | Seven variable measurements per daily row |
| Daily serving mart | 73,048 rows | One wide daily row per sampled point |
| Monthly summary | 2,400 groups | Eight points × 25 years × 12 months |

The archive covers 2001-01-01 through 2025-12-31. These are requested points in gridded products; city labels do not establish ground-station observations or national coverage.

**Learn:** Always state the *grain*: what one row represents. A larger row count after converting wide rows to long measurement facts is expected when the grain changes.

**Exercise:** Explain why `73,048 × 7 = 511,336` is consistent rather than evidence of duplicated weather days.

## Step 3 — Complete the problem statement without replacing your problems

**What I did:** Retained your three original problems and clarified their consequences, evidence and scope:

1. **Limited spatial coverage:** Eight sampled points cannot describe every locality in Tanzania.
2. **Single-source dependency:** NASA POWER remains the only provider; independent validation and fallback remain future work.
3. **Statistical extremes:** Unusual weather values need interpretation and review; they are not automatically invalid.

**Why:** Technical improvements such as logging or query speed support the project, but they do not replace its research motivation.

**Read:** [Problem statement](data_problem_statement.md) and [concise submission draft](problem_statement_one_page.md).

**Exercise:** For each problem, explain one effect on a researcher and one future improvement. Describe those improvements as proposed until implemented and verified.

## Step 4 — Explain the schema and data dictionary

**What I did:** Completed the schema rationale, documented dimensions and facts, explained keys and relationships, and filled the data dictionary with column meanings, units and constraints.

**Learn:** A dimension describes a date, location, variable or source. A fact stores a measurement linked to those descriptions. The measurement's natural uniqueness rule is date + location + variable + source. A wide daily mart makes the same data easier for analysts to query.

**Why:** The star schema makes measurement identity explicit; the serving mart gives users convenient columns. Both represent the same source measurements at different grains.

**Read:** [Schema](database_schema.md), [dictionary](data_dictionary.md) and [ER diagram](hydromet_er_diagram.md).

**Exercise:** Trace one Arusha rainfall value through its date, location, variable and source references. Explain the difference between a primary key, a foreign key and the natural uniqueness rule.

## Step 5 — Complete lineage, metrics and the datasheet

**What I did:** Documented the path from raw requests through transformations to consumer outputs; distinguished counts, quality indicators and performance measures; created a canonical root datasheet and compatibility links.

**Why:** A reader needs to know where data came from, how it changed, what a reported number means and which uses its limitations support.

**Read:** [Lineage](data_lineage.md), [metrics](metrics.md), [root datasheet](../DATASHEET.md) and [requirements tracker](lab_requirements_tracker.md).

**Learn:** The 12,529 historical IQR flags count variable-values, not distinct daily rows. Several flags can belong to one row. An IQR warning is a statistical review indicator, while a negative rainfall value violates a hard validity rule.

**Exercise:** Find the datasheet's coverage, units, intended uses and limitations. Explain why a monthly rainfall total differs from mean daily rainfall.

## Step 6 — Reconcile historical evidence and source conventions

**What I did:** Compared saved reports with prose claims, preserved historical numbers, checked raw source units and time conventions, and consulted NASA documentation on publication delay and revisions. Distinguished estimated cloud scan bytes from completed-job statistics.

**Findings:** All eight checked raw payloads declare solar radiation in `MJ/m²/day` and daily time convention `LST`. The original loader label used `kWh/m²/day` without conversion. Retained ingestion coordinates also differ from YAML for Morogoro and Songea; the established extract was preserved.

**Learn:** Changing a unit label and converting a value are different operations. A coordinate change can produce a different dataset, so reconciliation needs an explicit dataset-version decision.

**Read:** [Audit](phase1_evidence_audit.md) and [implementation report](phase2_implementation_and_evidence.md), including their source references.

## Step 7 — Build isolated, reproducible experiments

**What I did:** Added `src/labs/complete_labs.py` and `scripts/run_lab_evidence.ps1`. Used separate datasets and database copies under ignored `data/processed/lab_evidence`, retained selected evidence under `outputs/evidence`, and checked protected fingerprints around experiments.

**Why:** Failure tests, deliberately bad records and historical loader comparisons should have controlled inputs and should not replace established artifacts.

**Read:** [Lab driver](../src/labs/complete_labs.py) and [PowerShell wrapper](../scripts/run_lab_evidence.ps1).

**Reproduction command — writes isolated outputs:**

```powershell
.\scripts\run_lab_evidence.ps1
```

This requires the retained raw archive, existing Python environment, PostgreSQL installation and the historical Git object described in the implementation report. It runs cached acquisition, not a fresh NASA API timing experiment. Prefer studying existing evidence before rerunning the whole workflow.

## Step 8 — Make ingestion accounting and repeated-run evidence explicit

**What I did:** Added rows-read, accepted, rejected and reason counts; distinct run summaries; cache/download counts; isolated workspace support; and an offline mode. Executed two cached runs and compared their results.

**Result:** Each run read and published 73,048 rows, with zero rejects and duplicates. The resulting CSV fingerprint matched. Both runs used eight cached responses and no downloads.

**Learn:** Idempotency means repeating an operation does not create unintended extra results. Two distinct summaries and matching fingerprints provide stronger evidence than an overwritten log. Here, `rows_loaded` means accepted rows published to the CSV, not new database inserts.

**Read:** [Ingestion module](../src/ingestion/ingest_nasa_power.py) and [paired proof](../outputs/evidence/idempotency_proof.json).

**Read-only inspection:**

```powershell
Get-Content outputs/evidence/ingestion_run_1.json
Get-Content outputs/evidence/ingestion_run_2.json
```

## Step 9 — Preserve bad rows in quarantine

**What I did:** Added shared row partitioning with original values, CSV row numbers and reason codes. Covered malformed dates, missing or nonnumeric values, nonfinite numbers, provider fill values, invalid bounds, temperature order, source rules and conflicting duplicate keys. All occurrences of a duplicate key are rejected for review.

**Why:** Silent deletion hides what happened. Quarantine lets a reviewer trace and repair rejected data while valid records continue separately.

**Result:** An 11-row demonstration produced four accepted rows and seven quarantined rows. A physically valid rainfall value of 1,000 was retained despite its unusual size. The deliberate bad-input quality gate returned a failure exit status.

**Learn:** Accounting must balance: input = accepted + rejected. Hard-invalid values and statistical extremes need different treatment. Quarantine preserves evidence; it does not automatically repair values.

**Read:** [Quarantine module](../src/quality/quarantine.py), [quality gate](../src/quality/validate_hydromet.py) and [proof](../outputs/evidence/quarantine_proof.json).

**Exercise:** Explain why humidity of 120% is rejected while a very large positive rainfall amount is retained for domain review.

## Step 10 — Optimize the measured database-loading bottleneck

**What I did:** Replaced the fact loader's repeated conflict-handling path with a set-based anti-join that selects only missing natural keys before insertion. Corrected solar metadata to the verified native unit without converting measurements.

**Learn:** Conceptually, an anti-join asks: “Which incoming measurements have no matching key in the destination?” Avoiding already-loaded facts reduces unnecessary work.

**Validation:** Compared ordered key/value fingerprints and counts, tested partial completion followed by a full load, and tested repeated loading. The original local database was preserved; the new loader behavior was demonstrated in isolated databases.

**Result:** In one paired cached experiment, loading took 553.438081 seconds before and 4.428124 seconds after. This measures a reload of existing data, not every possible loading workload.

**Read:** [Loader](../src/database/load_duckdb.py) and [performance explanation](performance_optimization.md).

## Step 11 — Make serving refresh atomic and observable

**What I did:** Wrapped serving replacement and validation in a database transaction. Recorded a successful refresh timestamp and logical output hash, plus external attempt status. Added a deliberate failure after replacement to verify rollback.

**Learn:** A transaction commits related changes together or rolls them back. A failed refresh must not leave consumers with a partially replaced table.

**Result:** The failure demonstration preserved the previous good fingerprint and successful timestamp and reported `FAILED_REFRESH`.

**Read:** [Serving module](../src/serving/create_serving_layer.py) and [failure proof](../outputs/evidence/failed_refresh_proof.json).

**Exercise:** Explain why the failed-attempt timestamp and last-success timestamp are separate fields.

## Step 12 — Add a dashboard that reads curated outputs

**What I did:** Added a dashboard builder that queries the monthly serving view, checks refresh metadata consistency, and generates HTML with location/year selection, rainfall charts, temperature values, day counts, refresh status and observation coverage. Added dashboard generation to orchestration.

**Why:** A consumer should use the curated output and communicate its status clearly.

**Learn:** Refresh age tells you when an output was rebuilt. Observation coverage tells you which weather dates it contains. A fresh rebuild of an archive ending in 2025 does not imply observations for today.

**Read/open:** [Builder](../src/serving/build_dashboard.py), [normal snapshot](../outputs/evidence/hydromet_dashboard.html) and [failed-refresh snapshot](../outputs/evidence/dashboard_failed_refresh.html).

**Verification boundary:** Browser observation confirmed rendering, the monthly table, FRESH label and coverage. Browser-session errors prevented automated filter interaction and screenshot proof. The dashboard is a regenerated local snapshot; cloud hosting and live automatic refresh were not deployed.

## Step 13 — Prepare ML inputs with availability and time boundaries

**What I did:** Added an explicit predictor allowlist, excluded same-day raw weather, grouped histories by location and source, required continuous dates, used delayed historical features and removed rows whose target crossed a holdout boundary. Wrote new filenames to preserve original exports.

**Learn:** At a prediction date `t`, a feature must be available by `t`. A recorded observation date does not establish its publication time. The eight-day meteorological delay is a conservative assumption; it is not proof from historical release timestamps.

For example, a seven-day delayed rainfall average uses observations from `t−14` through `t−8`. A training row dated 2018-12-31 with a target on 2019-01-01 crosses into validation and is removed.

**Result:** 72,728 rows: 52,288 training, 8,760 validation and 11,680 test. There were 304 history/target exclusions and 16 boundary purges.

**Read:** [Preparation module](../src/ml/prepare_ml_data.py), [ML rationale](ml_data_preparation.md) and [results](../outputs/evidence/ml_availability_results.json).

**Exercise:** Explain why a random train/test split could be misleading for a future-weather task. No model was trained and no accuracy was measured in this work.

## Step 14 — Compare the required storage/query approaches fairly

**What I did:** Ran identical monthly mean daily precipitation aggregation using CSV+pandas, PostgreSQL and DuckDB SQL directly over Parquet. Used one warmup and five measured repetitions, comparing every result within `1e-9` absolute tolerance.

| Approach | Median client time | Stored size |
|---|---:|---:|
| CSV + pandas | 0.104578 seconds | 5.976842 MiB |
| PostgreSQL | 0.138663 seconds | 13.085938 MiB |
| DuckDB over Parquet | 0.082169 seconds | 0.929847 MiB |

All approaches returned 2,400 matching groups. PostgreSQL ran in a separate local cluster on port 55433, which was stopped afterward; the existing port-5432 service was preserved. Added a guard against targeting a different cluster.

**Learn:** These are warm cached client measurements. PostgreSQL timing includes command startup, connection and materialization; its storage includes indexes. CSV timing includes parsing, and DuckDB timing includes connection and fetch. The table supports this local workload comparison rather than universal engine rankings.

**Read:** [Benchmark evidence](../outputs/evidence/required_engine_benchmark.json).

## Step 15 — Profile the whole workflow and check result equivalence

**What I did:** Timed eight stages: cached ingestion, quality, schema, loading, serving, ML preparation, dashboard and regression checks. Started each run from a separate copy of the same database. Both runs used updated downstream stages; the loader implementation differed.

**Result:** Total time changed from 589.800996 to 29.499108 seconds: approximately 19.99× faster, or a 95.00% reduction. Ordered fact keys and values matched.

**Learn:** Profiling identifies where time is spent. Optimizing a small stage cannot substantially improve a workflow dominated by another stage. Correctness evidence must accompany a performance result.

**Read:** [Stage timings before](../outputs/evidence/pipeline_before.json), [after](../outputs/evidence/pipeline_after.json) and [comparison](../outputs/evidence/pipeline_improvement.json).

**Boundary:** One cached pair does not establish a timing distribution, a cold API profile or production scalability. Database-copy setup and final comparison-hash generation are outside the timed workflow.

## Step 16 — Test behavior and preserve the evidence trail

**What I did:** Added meaningful safeguards for quarantine, duplicate handling, malformed inputs, retained extremes, delayed features, temporal boundaries, continuous histories, refresh failure/rollback, partial/repeated loading and PostgreSQL target protection. Updated orchestration tests to test behavior rather than hardcoded historical summaries.

**Result:** Final verification passed **70 tests in 8.04 seconds**. Earlier profiling runs passed 69 tests each; the additional cluster-target test was added afterward. Documentation links/fences and whitespace were also checked. No dependencies were changed.

**Read:** [Safeguard tests](../tests/test_phase2_safeguards.py), [orchestration tests](../tests/test_orchestration.py) and [final test output](../outputs/evidence/regression_final.txt).

**Learn:** Tests establish the behavior they exercise. They do not prove national representativeness, independent source accuracy, deployed cloud operations or trained-model quality.

**Re-run command — executes tests and may create test artifacts:**

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Dataset-dependent tests require the retained project data. A clean code checkout alone is insufficient for all local evidence checks.

## Step 17 — Prepare presentation and manual handover

**What I did:** Wrote plain-language stage explanations, a demonstration sequence, lab mappings, likely questions and honest answers. Prepared a 62-file candidate submission list and exact manual Git commands excluding the two pre-existing unrelated edits.

**Read:** [Colleague presentation guide](colleague_presentation_guide.md), [manual submission guide](manual_github_submission.md) and [candidate file list](../outputs/evidence/changed_files.txt).

No files were staged, committed or pushed by me. Team names, owners, submission date and final submission page layout still need your review. This learning guide was added after the 62-file list was prepared; include it separately if you want it submitted.

## What remains unresolved

- The original spatial, single-source and statistical-extreme limitations remain.
- Exact historical publication timestamps and revisions are not reconstructed.
- Coordinate differences between retained requests and YAML need a deliberate version decision.
- Cold API timing and repeated full-workflow timing distributions were not measured.
- Live cloud deployment, scheduling and completed-job byte statistics were not verified.
- No model training or predictive accuracy is claimed.
- Dashboard filter interaction and screenshot automation remain unverified.

## Suggested learning sessions

| Session | Steps | What you should be able to explain afterward |
|---|---|---|
| 1 | 1–6 | Dataset scope, original problems, grains, provenance and units |
| 2 | 7–9 | Isolation, idempotency, accounting and quarantine |
| 3 | 10–12 | Anti-join loading, transactions, freshness and serving |
| 4 | 13–15 | Availability-aware features, holdouts and fair performance measurement |
| 5 | 16–17 | What tests prove, how to demonstrate evidence and how to submit manually |

For each session, write a short explanation without looking at the guide, then check it against the linked source and evidence. Use the retained demonstrations first; run the full reproduction only when you are ready to inspect newly generated results.
