# HydroMet-ETL Metrics and Acceptance Criteria

Reviewed on 2026-10-04. Baselines come from saved repository evidence; no pipeline or benchmark was rerun for this documentation update. Acceptance criteria describe evaluation expectations, not newly implemented checks.

## The original three problems

| Problem and metric | Definition and denominator | Baseline | Acceptance and interpretation |
|---|---|---|---|
| Limited spatial coverage: points | Distinct configured locations | 8 | Disclose actual points; no national area percentage follows from point counts or coordinate spans. Expansion needs a defined sampling frame. |
| Temporal completeness at sampled points | Unique valid location-date keys / (configured points × inclusive dates) | 73,048 / (8 × 9,131) = 100% | Expect all configured historical dates, with no gaps or duplicates. This does not establish spatial representativeness. |
| Single-source dependency: providers | Distinct provider labels | 1, `NASA_POWER` | Disclose dependency; future integration requires independent acquisition and harmonization. Upstream products within POWER are not independent pipeline providers. |
| Cross-source agreement | Bias, MAE and paired count on common variable-location-day support | Not available | Specify matching, units and day convention before comparing; independent validation is not established. |
| Statistical extremes: flag rate | Values outside Q1−1.5×IQR and Q3+1.5×IQR / nonmissing values per variable | See below | Review warnings; do not target zero outliers or automatically delete extremes. |
| Extreme review completion | Observation-level flags with a recorded decision / flags requiring review | Not available | Future review must retain identities, thresholds, decisions and evidence. Aggregate counts cannot measure completion. |

## Statistical warnings

Current quartiles are computed per variable over all locations and dates, rather than by location or season. Pooling and precipitation skew affect screening. Flags are neither confirmed errors nor validated extreme-event classifications.

| Variable | Flags | Rate out of 73,048 values |
|---|---:|---:|
| T2M | 1,636 | 2.240% |
| T2M_MIN | 1,037 | 1.420% |
| T2M_MAX | 344 | 0.471% |
| RH2M | 109 | 0.149% |
| PRECTOTCORR | 8,350 | 11.431% |
| WS2M | 156 | 0.214% |
| ALLSKY_SFC_SW_DWN | 897 | 1.228% |

Total: 12,529 flagged variable-values / 511,336 meteorological values = 2.450%. This is not a count of distinct location-day rows: several variables may flag the same row. Evidence: [quality report](../outputs/quality/data_quality_report.json) and [advanced profiling](../outputs/reports/advanced_data_profiling_report.json).

## Integrity and delivery

| Metric | Definition and expectation | Evidence |
|---|---|---|
| Error-rule failures | Failed ERROR rules; acceptance 0 | Quality report: 0, PASS, seven warning rules. Rule failures are not unique bad-row counts. |
| Ordinary missingness | Null meteorological cells / 511,336 expected cells; baseline target 0 | Profiling reports 0 ordinary missing values. Provider sentinels are a separate concern. |
| Duplicate wide keys | Repeated location-date rows; acceptance 0 | Profiling and quality report 0. Future multi-source keys must include source. |
| Fact reconciliation | Wide rows × seven variables | 511,336 expected facts; loader checks counts. A subsequent read-only Phase 1 query confirmed this count. |
| Serving reconciliation | Daily rows and monthly groups | Documented baseline: 73,048 daily rows, 8 × 25 × 12 = 2,400 monthly groups. Monthly daily counts should match calendar lengths. |
| Raw integrity | Recomputed fingerprint equals manifest checksum for every reused request | Manifest and ingestion verification logic exist; a subsequent read-only Phase 1 audit verified all eight manifest-linked files. |
| Repeatability | Equivalent requests produce the same interim hash and no duplicate keys | Saved ingestion and quality hashes agree; this is not a newly repeated ingestion run. |
| ML retention | Retained feature rows / source rows | 72,800 / 73,048 = 99.660%; 248 excluded rows: 30 initial days plus one final day per point. Splits: 52,352 + 8,768 + 11,680. |

## Runtime and storage

The saved [orchestration summary](../outputs/orchestration/pipeline_run_summary.json) records SUCCESS in 154.858648 seconds for six stages, with ingestion skipped and tests included. Database loading took 147.597132 seconds, 95.31% of total. This is one downstream run; uptime, repeated-run failure rate, API latency and freshness SLA are not established.

The saved [optimization summary](../outputs/optimization/optimization_summary.json) reports median CSV load 0.083082 seconds and Parquet load 0.004337 seconds. Speedup = CSV median / Parquet median = 19.16×; time reduction = (1 − Parquet median / CSV median) × 100 = 94.78%. Storage reduction is 83.98%. Its `size_mb` uses 1024² bytes, so sizes are MiB: CSV 5.976842 and Parquet 0.957728.

This experiment uses one warmup and ten measured repetitions with logical-equivalence validation on the same 73,048-row, 12-column dataset. The older 17.29× narrative example lacks a matching verified run artifact in this audit; use the saved JSON for this snapshot. Neither implies that the entire pipeline speeds up by the same factor. [Benchmark metadata](../outputs/benchmarks/benchmark_metadata.json) describes a separate physical-format comparison and a separate star-schema benchmark.

For future measurement, retain dataset hash, code revision, environment, run time, selected stages and methodology. Evaluate quality per ingestion, reconciliation per load and performance under comparable conditions. No numeric runtime SLA or predictive accuracy claim has been established.

## Consumer metric contracts

The curated input is `mart_weather_daily`, and monthly outputs are defined by `vw_monthly_climate_summary`. Unless stated otherwise, use the current `NASA_POWER` source, all configured points and the full 2001–2025 interval; user-selected location/date filters must be displayed. Owners are deliberately unassigned placeholders.

| Metric | Formula | Grain and filters | Unit | Owner |
|---|---|---|---|---|
| Monthly total precipitation | Sum of daily `prectotcorr` over month | Location-year-month, NASA_POWER; include only complete daily intervals and report day count | mm/month accumulated | [OWNER] |
| Monthly mean temperature | Sum of nonnull `t2m` / count of nonnull `t2m` | Location-year-month; source and date filters above | °C | [OWNER] |
| Monthly mean minimum / maximum temperature | AVG(`t2m_min`) / AVG(`t2m_max`) separately | Location-year-month; not the minimum/maximum of the month | °C | [OWNER] |
| Mean relative humidity | AVG(`rh2m`) | Location-year-month; disclose nonnull count | % | [OWNER] |
| Mean wind speed | AVG(`ws2m`) | Location-year-month; disclose nonnull count | m/s | [OWNER] |
| Mean daily solar radiation | AVG(`allsky_sfc_sw_dwn`) | Location-year-month; raw baseline unit governs until loader metadata is corrected | MJ/m²/day | [OWNER] |
| Monthly day completeness | Distinct included observation dates / calendar days in month × 100 | Location-year-month-source; no duplicate days | % | [OWNER] |
| Monthly mean daily precipitation (benchmark/cloud) | AVG(`PRECTOTCORR`) | Location-year-month over same extract; do not confuse with monthly total | mm/day | [OWNER] |
| Observation coverage end | MAX(`observation_date`) | Curated output and displayed source/location filters | Date | [OWNER] |
| Refresh age (proposed) | Evaluation timestamp − last successful curated-output refresh timestamp | One output version; UTC timestamps, displayed in Africa/Nairobi if desired | Hours | [OWNER] |
| Freshness label (proposed) | UNKNOWN if no success metadata; FAILED_REFRESH if last attempt failed; otherwise FRESH when age ≤ [FRESHNESS THRESHOLD HOURS], STALE when older | Output-version metadata, evaluated at display time | Label | [OWNER] |

The refresh formulas and label policy are documentation proposals, not implemented consumer features. A recently rebuilt archive ending in 2025 can have a recent refresh timestamp and old observation coverage at the same time. An overall pipeline completion timestamp is not a dedicated curated refresh timestamp; retain the serving-stage success time and output fingerprint in a later implementation. Show the last-good refresh age alongside a failed attempt instead of marking stale data fresh.

## Phase 1 verification update

A read-only 2026-10-04 audit confirmed 511,336 facts, 0 quality-flag rows, 73,048 daily mart rows and 2,400 monthly groups, and recomputed the documented CSV hash. The example Arusha January 2001 result is 65.76 mm total precipitation, 23.152903 °C mean temperature and 31 daily observations. See `docs/phase1_evidence_audit.md` for the query and evidence boundaries. These checks verify existing artifacts; they are not a new pipeline run.

## Phase 2 metrics update

Observed full cached workflow: 589.800996 s before and 29.499108 s after; speedup = before / after = 19.993859×; time reduction = (1 − after / before) × 100 = 94.998464%. These are one paired cached run of all eight workflow stages; ingestion uses retained raw files. The baseline loader took 553.438081 s, versus approximately 4.43 s after the anti-join optimization. Ordered natural-key/value fingerprints and all output counts agree. This full-workflow result is separate from the older isolated CSV/Parquet loading benchmark.

Required-engine aggregate medians: CSV+pandas 0.104578 s, PostgreSQL 0.138663 s, DuckDB-over-Parquet 0.082169 s. All return 2,400 equivalent monthly groups; storage definitions and client timing boundaries are explicit in `outputs/evidence/required_engine_benchmark.json`. These are warm cached timings, not cold engine-only results.

New ML row retention: 72,728 / 73,048 = 99.562%; 304 history/target exclusions plus 16 target-boundary purges. Chronological split counts are 52,288 / 8,760 / 11,680. Earlier 72,800-row metrics remain historical for the original preparation.

Freshness formulas above are now implemented by `freshness_label` and dashboard JavaScript with a 24-hour threshold. Last-good refresh timestamps and logical output hashes are recorded by the serving stage; a failed attempt displays FAILED_REFRESH while preserving the previous successful output. The observed archive end date remains 2025-12-31. Metric owners are still [OWNER].
