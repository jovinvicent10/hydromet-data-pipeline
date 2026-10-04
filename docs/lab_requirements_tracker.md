# HydroMet-ETL Lab Requirements Tracker

For current completion status, read the **Current Phase 2 status** matrix near the end. The earlier tables retain the Phase 1 audit snapshot.

Audit date: 2026-10-04. Submission date: [SUBMISSION DATE]. Repository: https://github.com/jovinvicent10/hydromet-data-pipeline.

Team: [MEMBER 1], [MEMBER 2], [MEMBER 3], [MEMBER 4]. All unassigned owners remain [OWNER]. No code or dependencies are changed in Phase 1.

**Verified complete** means inspected implementation plus retained execution evidence or a read-only check verifies the requirement. **Partial** means some required elements exist. **Missing** means the required artifact or implementation was not found in the inspected repository. **Not yet verified** means a claim exists but sufficient evidence has not been checked or retained. These statuses apply to individual requirements; a lab is complete only when all its requirements are verified.

## Lab 1 — Problem and dataset (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Selected dataset | Verified complete | `configs/config.yaml`; interim CSV inspected: 73,048 rows, eight points, 9,131 dates | Explain point sampling and seven variables | [OWNER] |
| Four-member team | Partial | Four placeholders above, as requested | Fill names after team review | [OWNER] |
| Three supported problems | Verified complete | `docs/data_problem_statement.md`; `outputs/reports/advanced_data_profiling_report.json` | Present eight points, one provider, 12,529 IQR flags; do not call all flags errors | [OWNER] |
| One-page problem statement | Partial | `docs/problem_statement_one_page.md` is a concise submission draft | Confirm rendered page count in the final submission format | [OWNER] |
| Repository link | Verified complete | Git remote inspected; link above and README | Confirm assessor access separately | [OWNER] |

## Lab 2 — Analytical schema (Verified complete for local implementation)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| DuckDB typed schema and keys | Verified complete | `sql/01_create_schema.sql`; local `data/database/hydromet.duckdb`; `docs/database_schema.md` | Explain fact grain and composite natural key | [OWNER] |
| README rationale and why not one large table | Verified complete | README design section; `docs/database_schema.md` | Explain shared metadata and the useful wide serving interface | [OWNER] |
| Real-data load | Verified complete | Read-only audit counted 511,336 observation facts; `logs/orchestration/database_load.log` | Show reconciliation 73,048 × seven | [OWNER] |
| Meaningful query evidence | Verified complete | `docs/phase1_evidence_audit.md`: Arusha Jan 2001, 65.76 mm total, 31 days | Run the documented SELECT in read-only mode | [OWNER] |

## Lab 3 — Ingestion (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Python ingestion and direct command | Verified complete | `src/ingestion/ingest_nasa_power.py`; README command | Explain request IDs and checksum-verified cache reuse | [OWNER] |
| Two-run idempotency proof | Partial | `docs/ingestion_design.md` historical claim; `logs/ingestion/ingestion_20260819_010111.log` and `ingestion_20260819_013927.log` both report 73,048 rows; current summary and hash | Preserve distinct run summaries and per-run hashes, duplicate counts and unchanged keys; do not overwrite the first proof | [OWNER] |
| Rows read, loaded and rejected with reasons | Partial | Existing ingestion logs show requests/cache reuse and final rows; current summary reports rows | Add explicit read/accepted/rejected counts, reason codes and accounting identities; demonstrate ordinary and bad-row cases in isolation | [OWNER] |
| Proof explanation in README | Verified complete | README Phase 1 evidence section explains existing evidence limits and required paired proof | Future results must be added only after execution | [OWNER] |

## Lab 4 — Required engine benchmark (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Same dataset and aggregate | Partial | `outputs/benchmarks/benchmark_metadata.json`; existing experiment uses monthly mean daily precipitation | Reuse exact dataset hash and aggregate across all three required engines | [OWNER] |
| CSV + pandas | Verified complete | `src/benchmarking/benchmark_storage.py`; `outputs/benchmarks/storage_benchmark_results.csv` | Retain existing historical baseline | [OWNER] |
| PostgreSQL | Missing | No PostgreSQL benchmark code/results found; no CLI on PATH or matching service returned during inventory | Confirm installation/account access; isolated lab DB; load and measure query/storage without touching established data | [OWNER] |
| DuckDB directly querying Parquet | Missing | Current Parquet functions use pandas; DuckDB queries `weather_wide` in a database | Execute SQL over `read_parquet(...)`, rather than copying Parquet into a DuckDB table | [OWNER] |
| Equivalence and comparable timing/storage | Partial | Existing three-format experiment has 2,400 groups and tolerance 1e-9, one warmup/ten repetitions | Extend equivalence and comparable boundaries to required engines; distinguish DB allocated storage, file bytes and caches | [OWNER] |
| Table and three-sentence verdict | Partial | README table and verdict describe existing experiment honestly | Add required-engine measurements and revise verdict after execution | [OWNER] |

## Lab 5 — Cloud experiment (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Sandbox upload and aggregate results | Verified complete | Visually inspected `outputs/cloud/bigquery_validation.png` (Sandbox, 73,048 rows) and `bigquery_monthly_precipitation.png` (2,400 groups); `sql/04_bigquery_analysis.sql` | Describe this as retained historical evidence, not a fresh cloud run | [OWNER] |
| Screenshot and estimated bytes | Verified complete | `bigquery_select_all_cost.png` 7.04 MB; `bigquery_projected_columns_cost.png` 1.74 MB, visibly pre-run estimates | Explain approximately 75.3% fewer estimated bytes; not monetary charges | [OWNER] |
| Completed-job statistics | Not yet verified | Result screenshots exist but do not display job-information byte statistics | Retain job ID, totalBytesProcessed, totalBytesBilled and cacheHit if required; distinguish these from editor estimates | [OWNER] |
| One-page proposed design and cost drivers | Partial | `docs/cloud_design_one_page.md`; longer `docs/cloud_architecture.md` | Verify final rendered page count; deployment and exact pricing are not claimed | [OWNER] |

## Lab 6 — Quality and governance (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Five executable checks: validity, completeness, uniqueness | Verified complete | `src/quality/validate_hydromet.py`; `tests/test_data_quality.py`; saved report PASS with zero ERROR failures | Explain humidity bounds, temperature order, nonnegative rain, missing fields, duplicate keys and date coverage | [OWNER] |
| Rejected-row quarantine and reason codes | Missing | Validator produces aggregate reports; no quarantine artifact found | Isolated reject output preserving original row and reason code; reconcile accepted + rejected with input | [OWNER] |
| Deliberately bad-row proof | Missing | Existing tests inspect baseline data; no retained isolated bad-row proof found | Inject duplicate, null and invalid weather into a copy; show detection/quarantine without changing baseline | [OWNER] |
| README lineage and dataset-specific PDPA | Verified complete | README lineage and personal-data paragraph; `docs/governance_and_quality.md`; authoritative PDPC Act cited | Reassess if household/person-linked coordinates or user data are introduced | [OWNER] |

## Lab 7 — Curated output and consumer (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Named documented pipeline-refreshed output | Verified complete | `mart_weather_daily`; `sql/05_create_serving_layer.sql`; successful saved serving stage; read-only count 73,048 | Explain curated output as the agreed analyst interface | [OWNER] |
| Metrics with formula, grain, filters and owner | Verified complete | `docs/metrics.md`; owners remain [OWNER] as requested | Assign owners during review | [OWNER] |
| Dashboard/notebook consuming curated output | Missing | Profiling notebooks read interim CSV; ML code consumes mart but is not the requested consumer dashboard/notebook | Add a consumer querying mart/view; prove connection, avoiding a separate stale CSV copy | [OWNER] |
| Computed freshness label | Missing | Run timestamps exist; no computed label attached to consumer output | Compute age from last successful curated refresh, with policy and status; show observation end date separately | [OWNER] |
| Deliberately failed refresh | Missing | Fail-fast code exists; no retained failure demonstration | Isolated failed run; preserve last good output and show failed attempt plus stale/failed label | [OWNER] |

## Lab 8 — ML data readiness (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| ML table and five explained engineered features | Verified complete | Local Parquet files exist; `src/ml/prepare_ml_data.py`; `metadata/ml_split_metadata.json`; feature table in `docs/ml_data_preparation.md` | Explain calendar, lags and shifted means with concrete dates | [OWNER] |
| Written split strategy | Verified complete | ML documentation and metadata: train through 2018; validation 2019–2021; test 2022–2025 | Distinguish feature date from target date | [OWNER] |
| Every-column availability review | Verified complete | Availability matrix in `docs/ml_data_preparation.md`; authoritative NASA latency sources | Review specifies a proposed next-day forecast contract; publication timestamps are not modeled | [OWNER] |
| Exclude unavailable predictors and handle latency | Missing | Current export includes same-day weather and short lags; NASA documents delayed publication | After authorization, implement an allowlist/as-of policy and remove unavailable predictors; test availability | [OWNER] |
| Target-time split boundary control | Partial | Chronological feature dates implemented; train target on 2019-01-01 and validation target on 2022-01-01 cross partitions | Purge boundary rows or split on target date and verify no target crosses holdout boundary | [OWNER] |
| DATASHEET.md | Verified complete | Root `DATASHEET.md`, with origin, intended uses, privacy assessment, partitions and limits | Review placeholders and unresolved rights/stewardship facts | [OWNER] |

## Lab 9 — Profiling and improvement (Partial)

| Requirement | Status | Evidence | Missing work / demonstration | Owner |
|---|---|---|---|---|
| Time every stage including ingestion | Partial | `outputs/orchestration/pipeline_run_summary.json`: six stages, ingestion skipped | Measure all seven stages; label cached acquisition and cold acquisition separately | [OWNER] |
| Measured slowest stage | Partial | Database load 147.597132 / 154.858648 s = 95.31% of saved downstream run | Do not call it the full-pipeline bottleneck until ingestion is included | [OWNER] |
| Justified improvement and before/after correctness | Verified complete | `outputs/optimization/optimization_summary.json`: equivalent CSV/Parquet, ten repetitions, 19.16× isolated load speedup | Applies only to loading experiment; older 17.29× narrative is retained as historical, not new evidence | [OWNER] |
| Full-pipeline improvement and cached/cold separation | Missing | Isolated loading benchmark and downstream summary are separate workloads | Profile full workload; target measured bottleneck; retain before/after full-stage timings and correctness evidence | [OWNER] |

## Phase boundary and unresolved facts

No prepared update archive, patch, diff or named update package was found by repository inventory excluding `.git` and `.venv`; none was integrated. A package outside the inspected repository remains not yet verified.

PostgreSQL absence is not proven system-wide: PATH/service discovery returned no matches. Names, submission date and owners remain placeholders. New paired-run hashes, quarantine/bad-row proof, required-engine benchmarks, consumer refresh metadata, availability-safe ML exports and full-pipeline profiles require Phase 2 authorization. Runtime, page count, deployment, live cloud access and scheduler execution must never be inferred from documentation alone.

## Current Phase 2 status — supersedes the Phase 1 snapshot above

Phase 2 was authorized by the user's “proceed”. The preceding tables preserve the original audit; this matrix and retained new evidence define the current technical status. Owners remain [OWNER].

| Lab / requirement | Current status | New evidence and remaining boundary |
|---|---|---|
| Lab 1 dataset, three problems, repository link | Verified complete | Original evidence preserved; concise draft exists |
| Lab 1 team details and one-page layout | Partial | Four member placeholders retained; rendered final page count pending |
| Lab 2 schema, rationale, real load and meaningful query | Verified complete | Existing and isolated counts match; loader safeguards and solar-unit correction tested |
| Lab 3 paired ingestion and read/loaded/rejected logging | Verified complete | `outputs/evidence/ingestion_run_1.json`, `ingestion_run_2.json`, paired logs and `idempotency_proof.json`; bad-row accounting records reasons; acquisition is cached/offline |
| Lab 4 required engines, equivalence, timing/storage table and verdict | Verified complete | `outputs/evidence/required_engine_benchmark.json` and `.csv`; PostgreSQL isolated; DuckDB uses read_parquet directly; results agree within 1e-9; table/verdict in Phase 2 report |
| Lab 5 historical sandbox and bytes estimates | Verified complete | Existing screenshots inspected and preserved |
| Lab 5 completed-job byte statistics | Not yet verified | No new cloud job-statistics access; editor estimates remain labeled estimates |
| Lab 5 one-page proposed design | Partial | Connections/cost drivers documented; final rendered page count pending |
| Lab 6 checks, quarantine, deliberate bad-row proof, lineage and PDPA paragraph | Verified complete | `src/quality/quarantine.py`; quality CLI blocks invalid rows; `outputs/evidence/quarantine_proof.json`, `bad_row_quality_gate.txt`; physically valid extremes retained |
| Lab 7 curated output, metric contracts, consumer, freshness and failed refresh | Verified complete | `src/serving/create_serving_layer.py`, `build_dashboard.py`; `outputs/evidence/hydromet_dashboard.html`, `dashboard_failed_refresh.html`, `failed_refresh_proof.json`; browser rendered default view, automated filter/screenshot check unverified |
| Lab 8 five features, written split, every-column review and DATASHEET | Verified complete | Updated ML implementation/docs, predictor allowlist, new Parquet outputs and `outputs/evidence/ml_availability_results.json` |
| Lab 8 implemented exclusion and target-boundary control | Verified complete | Same-day/unavailable columns excluded; eight-day delayed histories; 16 boundary rows purged; new split counts verified |
| Lab 8 actual publication-vintage availability | Not yet verified | Conservative delay implemented; actual publication timestamps and later revisions absent; operational next-day readiness remains conditional |
| Lab 9 timing every stage, measured bottleneck, justified improvement and correctness | Verified complete | `outputs/evidence/pipeline_before.json`, `pipeline_after.json`, `pipeline_improvement.json`; eight stages including cached ingestion and tests; same values/counts |
| Lab 9 cold API timing and repeated full-run distribution | Not yet verified | One paired cached workflow measured; cold network acquisition and repeated full-run variance are explicitly unmeasured |
| Phase 3 colleague guide | Verified complete | `docs/colleague_presentation_guide.md`; concrete examples, demo, questions and honest boundaries |
| Phase 4 manual submission preparation | Verified complete | `docs/manual_github_submission.md`; include/exclude guidance, branch/remote and suggested commit; agent performed no staging, commit or push |

PostgreSQL inventory during Phase 2 found PostgreSQL 18 installed and the original service running. Existing server authentication required credentials, so a separate loopback cluster/database was used without requesting secrets or changing the service. It was stopped after the benchmark. The main archive, original metadata/report and unrelated notebook were preserved by fingerprint checks.
