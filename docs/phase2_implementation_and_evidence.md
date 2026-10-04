# HydroMet-ETL Phase 2 Implementation and Evidence

Phase 2 is authorized. Code changes are executed through isolated experiments under `data/processed/lab_evidence`; retained measurements and sanitized proof summaries are under `outputs/evidence`. Established data, manifest, original ML splits, the locally modified notebook and original quality report are fingerprinted before and after every experiment. Old reports are preserved as historical evidence.

## Reproduction

With the retained raw data, existing environment and PostgreSQL 18 installed:

```powershell
.\scripts\run_lab_evidence.ps1
```

This creates or reuses a separate local PostgreSQL cluster and lab database on `127.0.0.1:55433`, runs all isolated proofs and stops that cluster. It never uses credentials for, or changes, the existing service on port 5432. The temporary cluster uses local trust authentication and is not a deployment. The driver can also execute a single section with `python -m src.labs.complete_labs --section pair|bad|before|after|benchmark|failure` (choose one actual section name).

The legacy loader is recovered from Git revision `df0a67cf875fa731a10de4ed8a61afd8188b3884` when the saved local snapshot is absent; that Git object must exist to reproduce the historical comparison. Source acquisition uses verified cached raw responses and is explicitly offline. This is not a cold API request measurement.

## Changes and why they matter

- Ingestion reports rows read, accepted into the interim output, rejected and reason counts. Unique per-run summaries preserve both executions, so the second run cannot overwrite the first proof. `rows_loaded` here means rows published to the CSV, not new database fact inserts.
- Row quarantine preserves original values and input row numbers. Duplicate conflicts reject every occurrence; invalid dates, missing/non-numeric values, provider fill values, bounds and temperature order have reason codes. An unusually large but physically valid precipitation value is retained rather than rejected by magnitude.
- The fact loader filters existing natural keys in a set-based anti-join before inserting new rows. The previous conflict-handling path attempted every existing fact on a reload. Keys and values remain intact; meaningful tests cover a partial load followed by completion and a repeated load.
- Solar metadata is corrected to MJ/m²/day, as verified in all eight raw payloads. Values are not converted. This metadata correction is applied during a load, including to existing dimensions; it does not rewrite raw data.
- Serving refresh runs in a transaction. A deliberate failure after table replacement rolls the replacement back, retains the previous successful timestamp and hash, and records the failed attempt. The dashboard queries the curated monthly view and displays both refresh age and archive coverage.
- New ML exports use an explicit predictor allowlist, remove same-day weather, use an eight-day delay for meteorological histories, group by location and source, require continuous dates and purge target dates crossing holdout boundaries. They have new filenames so original historical exports remain available.

The eight-day lag is a conservative assumption relative to NASA's nominal publication delay, not a historical publication-vintage reconstruction. Actual publication timestamps and retrospective revisions remain unverified, so operational forecasting readiness is still not claimed.

## Measurement interpretation

The required benchmark runs identical monthly mean daily precipitation aggregation over CSV+pandas, PostgreSQL and DuckDB SQL directly over Parquet. It checks every measured result within 1e-9 absolute tolerance. It reports warm cached medians, client wall times and explicit storage definitions. PostgreSQL includes CLI/connection/CSV-materialization overhead; DuckDB includes connection and fetch; pandas includes CSV parsing. These are local workload measurements, not pure server-engine speed or production scaling rankings.

Full workflow before/after runs both start from separate copies of the same existing database and include offline cached ingestion, quality, schema, loading, serving, ML preparation, dashboard and regression checks. Both runs share the updated other stages; the loader implementation differs through the anti-join and the verified native solar-unit label correction, without changing measurements. One paired run establishes observed improvement, not a stable statistical distribution; cold network acquisition remains unmeasured.

## Coordinates and scope

The retained ingestion uses Morogoro longitude 37.6612 and Songea latitude/longitude −10.6833/35.6500, while YAML lists 37.6680 and −10.6822/35.6513. Phase 2 preserves the established extract and request IDs; it does not silently re-download different points. Resolve configuration reconciliation separately with an explicit dataset-version decision.

The original problems remain limited spatial coverage, single-source dependency and statistical extremes. None is replaced by the new technical demonstrations.

## Executed Phase 2 results (2026-10-04)

| Evidence | Verified result |
|---|---|
| Paired cached ingestion | Distinct summaries; both 73,048 read/loaded, zero rejects/duplicates, original CSV hash unchanged; `outputs/evidence/idempotency_proof.json` |
| Bad-row quality gate | 11 input rows, four accepted, seven quarantined; reason codes retained; deliberately valid large rainfall retained; CLI returns 1 and FAIL; `outputs/evidence/quarantine_proof.json` |
| Full cached workflow | Before 589.800996 s; after 29.499108 s; observed 19.993859× speedup / 94.998464% reduction; identical ordered fact-value fingerprint and counts; `outputs/evidence/pipeline_improvement.json` |
| Loader stage | Before 553.438081 s; after 4.428124 s; source values and IDs retained |
| Regression suite | Baseline run: 69 passed in 12.50 s; optimized run: 69 passed in 6.38 s; timing includes local variability; `outputs/evidence/tests_before.txt`, `tests_after.txt` |
| Failure recovery | Deliberate post-replacement failure rolled back; last-good fingerprint and successful timestamp unchanged; generated snapshot displays FAILED_REFRESH; `outputs/evidence/failed_refresh_proof.json` |
| New ML exports | 72,728 rows: 52,288 train, 8,760 validation, 11,680 test; 304 history/target exclusions and 16 boundary purges; `outputs/evidence/ml_availability_results.json` |
| Preservation | Protected established CSV, manifest, original ML metadata, original quality report and unrelated notebook fingerprints unchanged; `outputs/evidence/preservation_check.json` |

### Required engine benchmark

All engines returned 2,400 groups matching within 1e-9 absolute tolerance, on the original 73,048-row dataset. One warmup and five measured repetitions were used; these are warm/cached client medians.

| Engine | Median aggregate (s) | Storage (MiB) |
|---|---:|---:|
| CSV + pandas | 0.104578 | 5.976842 |
| PostgreSQL | 0.138663 | 13.085938 |
| DuckDB SQL over Parquet | 0.082169 | 0.929847 |

DuckDB directly querying Parquet had the lowest observed median client time and smallest stored representation in this local experiment. PostgreSQL's measurement includes psql startup/connection and its storage includes indexes, so this table is not a pure engine-compute ranking. All results agree, and the small cached dataset does not justify conclusions about production scale or cold-query performance.

Evidence: `outputs/evidence/required_engine_benchmark.json` and `.csv`. The temporary PostgreSQL 18.4 cluster was stopped after measurement; the original port-5432 service still accepted connections.

### Dashboard verification and remaining facts

The in-app browser rendered the curated dashboard, monthly table, FRESH label and separate archive coverage. Browser session errors prevented automated filter interaction and screenshot capture, so those checks remain unverified; no screenshot proof is claimed. The query/data and refresh/rollback behavior were checked by code and isolated demonstrations. The local preview is `http://127.0.0.1:8765/hydromet_dashboard.html`; standalone HTML also opens directly from the filesystem.

Remaining facts: exact source publication timestamps/vintages; a true cold API profile; repeated full-workflow timing distribution; final submission page counts; team names/owners/date; current live cloud account access and completed-job byte statistics. No scheduler, cloud refresh, source fallback or trained-model accuracy is claimed. The new ML exports implement a conservative lag assumption, not verified operational source availability.

## Final verification and unresolved facts

Final regression after the quality-gate and isolated-cluster safeguards: **70 passed in 8.04 seconds**, retained in `outputs/evidence/regression_final.txt`. `git diff --check` passed. Ignore checks confirmed the temporary PostgreSQL cluster, isolated DuckDB and local quarantine rows are excluded from Git. Branch is `main`; remote is `https://github.com/jovinvicent10/hydromet-data-pipeline.git`. No dependencies were changed, and no files were staged, committed or pushed.

The original notebook and quality-report changes predate this work and remain untouched. The presentation and manual-submission guides are ready. The remaining uncertainties are publication vintages, true cold API timing, repeated timing variance, final page layout, team placeholders, live cloud access/completed-job byte statistics, browser filter interaction and screenshot automation. These are disclosed limitations rather than invented completion.
