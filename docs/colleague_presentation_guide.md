# HydroMet-ETL Colleague Presentation Guide

Team: [MEMBER 1], [MEMBER 2], [MEMBER 3], [MEMBER 4]. Submission date: [SUBMISSION DATE]. Speaker/owners: [OWNER].

## Opening you can say aloud

“We built a repeatable path from NASA POWER weather data to tables that researchers can query. The archive contains 25 years of daily data for eight Tanzanian points. Our three problems are limited spatial coverage, dependency on one provider, and unusual weather values that need careful interpretation. We preserve the original data, check it, record its origin and create simpler outputs for analysis.”

## Who uses it and for what?

Climate researchers compare monthly rainfall and temperature at the sampled points. Agricultural analysts investigate seasonal patterns and prepare research features. Another engineer needs clear commands and evidence to repeat the workflow. None of these activities establishes complete national coverage, a validated crop recommendation or a production forecast.

The data cover 2001-01-01 to 2025-12-31: 9,131 dates × eight points = 73,048 daily rows. Seven variables describe temperature, humidity, rain, wind and solar radiation. NASA POWER returns values from gridded products for requested coordinates; the labels are not proof of eight ground stations.

## Explain each stage with an example

| Stage | Plain explanation | HydroMet example |
|---|---|---|
| Ingestion | Bring data from a provider into the project | Request Arusha's daily temperatures and rain; preserve serialized JSON |
| Provenance | Record where a value came from | The request ID and manifest identify coordinates, period and raw file |
| Checksum | Fingerprint a file so unexpected changes can be detected | Recomputing SHA-256 shows the preserved Arusha file still matches the manifest |
| Idempotency | Repeating the same task does not add duplicates | Two cached runs each produce 73,048 rows and the same CSV fingerprint |
| Quality gate | Evaluate rules before downstream use | Reject negative rainfall, invalid dates and conflicting duplicate keys |
| Quarantine | Keep rejected source rows separately with explanations | An injected humidity value of 120% has `HUMIDITY_RANGE`, not silent deletion |
| Star schema | Store measurements with shared descriptive tables | A rainfall fact joins a date, Arusha, precipitation in mm/day and NASA_POWER |
| Grain | State exactly what one row represents | One fact is one variable at one location/date/source; seven variables give 511,336 facts |
| Serving mart | Give analysts a simpler table | One daily row contains all seven weather columns |
| Aggregation | Combine daily measurements into a summary | Arusha January 2001 has 65.76 mm rainfall across 31 days |
| Dashboard | Read the curated summary and make it understandable | Choose Arusha and 2001 to inspect monthly rainfall and temperature |
| Freshness | Say when the output was last successfully refreshed | Display refresh age separately from the archive end date, 2025-12-31 |
| ML features | Build useful inputs from information before a prediction | Average rain from t−14 through t−8 instead of using unpublished same-day rain |
| Holdout split | Keep later outcomes separate when evaluating a future model | Remove a training row whose tomorrow's outcome belongs to validation |
| Profiling | Measure where time is spent | Time ingestion, checks, database loading and every downstream stage |
| Optimization | Change a measured bottleneck while checking results | Filter already-present facts before inserting, preserving values and keys |

## Why both star and wide tables?

“One large weather table is convenient to read, so we keep one as a serving product. The star schema stores shared descriptions once and gives every measurement an explicit variable and source. The pipeline pivots that structure into wide daily rows so colleagues can use simple queries. These are two views of the same measurements, not different datasets.”

A primary key identifies a row. A foreign key links it to another table. The fact's natural uniqueness rule is date + location + variable + source. A row count that increases from 73,048 to 511,336 is a change of grain, not evidence of duplicate weather days.

## What each lab demonstrates

| Lab | What to show | Honest boundary |
|---|---|---|
| 1 | Dataset, four-member placeholders, original three supported problems and concise problem draft | Names, submission date and final page layout still need review |
| 2 | Typed schema, keys, real load and Arusha monthly query | Source/version harmonization is not automatic |
| 3 | Direct ingestion command, distinct run summaries, unchanged hash and row accounting | Paired proof uses cached raw data, not fresh network retrieval |
| 4 | Required benchmark table with CSV+pandas, PostgreSQL and DuckDB-over-Parquet | Include client overhead and cache/storage definitions; do not generalize rankings |
| 5 | Historical sandbox screenshots and estimated bytes; proposed cloud design | Editor estimates differ from completed-job statistics; no cloud scheduler is deployed |
| 6 | Executable checks, rejected rows with reasons and isolated bad-row proof | IQR warnings remain review indicators; they are not automatic rejects |
| 7 | Curated-output dashboard, refresh age and failed-refresh snapshot | The dashboard is a regenerated local snapshot, not a live hosted service |
| 8 | Predictor allowlist, delayed histories, target-date-safe partitions and DATASHEET | Exact publication vintages remain unverified; no model has been trained |
| 9 | Whole cached-workflow stage timings and paired loader comparison | Cold API timing is not measured; one pair is not a performance distribution |

Use [the tracker](lab_requirements_tracker.md) for the exact current statuses and [Phase 2 evidence](phase2_implementation_and_evidence.md) for results. Do not present a planned component as an executed result.

## Short demonstration sequence

1. Open the problem statement and say the three problems without substituting other findings.
2. Show `outputs/evidence/idempotency_proof.json` and the two distinct ingestion summaries. Explain equal fingerprints and zero duplicates.
3. Show `outputs/evidence/quarantine_proof.json`; optionally inspect the ignored local rejected-row CSV. Explain why a physically valid large rainfall value was kept.
4. Open the generated `outputs/evidence/hydromet_dashboard.html`. Choose Arusha and 2001. Explain rainfall totals, day counts and observation coverage.
5. Open `outputs/evidence/dashboard_failed_refresh.html`. Show `FAILED_REFRESH`; explain the unchanged last-good output and rollback.
6. Show the required-engine benchmark and pipeline improvement JSON. State measurement boundaries before the speedup.
7. Show ML availability metadata and the predictor allowlist. Explain publication delay and target-date boundaries.
8. Close with the tracker: executed evidence first, remaining limitations second.

Use existing evidence for the presentation; repeating the full benchmark live is optional. Rebuilding historical evidence can take longer than the demonstration slot. The complete isolated reproduction command is `.\scripts\run_lab_evidence.ps1`.

## Likely questions and honest answers

**Is this all of Tanzania?** No. Eight configured points provide historical point-level coverage. National coverage needs an explicit sampling plan or gridded national extract.

**Why NASA POWER only?** It provides the existing reproducible archive. A second independent provider would improve cross-checking, but matching units, dates and spatial support still needs work.

**Are the 12,529 flags bad rows?** No. They count variable-values beyond pooled IQR bounds, and several can belong to one daily row. Rainfall is skewed and real events can be unusual.

**Why not delete all unusual rainfall?** That could remove the events analysts most need to study. Hard-invalid records go to quarantine; statistical extremes remain available for domain review.

**Do identical rainfall sequences prove faulty data?** No. Long dry spells can repeat zeros. The 73-day Mbeya sequence is a supporting diagnostic requiring context.

**Is solar radiation in kWh?** The retained payloads say MJ/m²/day. We corrected loader metadata without converting values. An existing historical database label stays unchanged until the updated loader is run against it; isolated evidence verifies the correction.

**Can the model predict tomorrow?** We have prepared data, not trained a model. Same-day NASA weather is delayed, so the new experiment excludes it and uses older histories. Exact publication times and historical revisions remain unresolved.

**Why is the archive old even when the label is FRESH?** Refresh age measures when an output was rebuilt; observation coverage says what weather dates are present. Both are displayed.

**What happens after a failed refresh?** The transaction rolls back and preserves the last-good output. The failed attempt is recorded and shown separately.

**Did you change the production PostgreSQL database?** No. The experiment uses a separate local cluster and lab database on port 55433; it is stopped after measurement.

**Is the cloud pipeline running?** No. BigQuery screenshots demonstrate historical queries. Ingestion, storage and scheduling in the proposed cloud design are not claimed as deployed.

**Does the data contain personal information?** The weather schema and city-point coordinates do not identify individuals. Person-linked household/farm data or user accounts would need a fresh assessment; see the authoritative PDPC reference in the datasheet.

**What proves the optimization is correct?** Compare ordered natural-key/value fingerprints and counts, plus tests for partial completion and repeated loads. The exact measured timings are in retained evidence, not assumed from code.

## Closing talking point

“The contribution is a reproducible and inspectable data workflow. We can show where the values came from, what rules ran, which records were rejected and why, which outputs refreshed successfully, and what remains uncertain. Spatial representation, independent provider validation and careful treatment of statistical extremes remain central limitations.”

## Results to present from the executed evidence

| Result | What it means |
|---|---|
| 69 tests passed in both workflow runs | Behavior and existing artifact checks passed; this is not trained-model accuracy |
| 589.80 → 29.50 seconds | One full cached-workflow comparison, approximately 19.99× faster, with matching measured values |
| 553.44 → 4.43 seconds for loading | Filtering existing facts avoids the former slow duplicate-conflict path |
| 2,400 matching benchmark groups | The required CSV+pandas, PostgreSQL and DuckDB-over-Parquet aggregate results agree |
| 11 deliberately bad-fixture input rows → four accepted + seven rejected | Quarantine accounting balances and reason codes explain exclusions |
| 72,728 new ML rows | Delayed-history preparation and target-boundary purges are implemented; exact publication vintages remain unknown |
| Same last-good hash after a deliberate refresh failure | Transaction rollback preserves the previous valid consumer output |

The benchmark medians are 0.104578 s (CSV+pandas), 0.138663 s (PostgreSQL) and 0.082169 s (DuckDB over Parquet), measured with the client boundaries in the report. The full workflow includes eight stages and cached raw-data acquisition, not a cold NASA API run. Browser observation confirmed the dashboard renders; automated filter interaction and screenshot capture could not be verified because of a browser-session error.

Final handover suite: **70 passed in 8.04 seconds**. The profiling snapshots each passed 69 tests; an additional cluster-target safety test was added afterward. Present these as separate verification snapshots, not conflicting measurements.
