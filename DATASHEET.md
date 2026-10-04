# HydroMet-ETL Dataset Datasheet

Documentation snapshot: 2026-10-04. This describes the existing historical extract and its derivatives; it does not certify current upstream service behavior or a new pipeline execution.

## Motivation and stewardship

HydroMet-ETL was developed for DSAI 6226, Data Engineering and Analytics, at NM-AIST to demonstrate reproducible hydrometeorological data engineering for climate and agricultural analytics in Tanzania. Repository maintainers are responsible for configuration, validation evidence and documentation. A formal operational data steward, support contact, retention policy and production SLA are not specified in the reviewed documentation.

The original problems remain **limited spatial coverage, single-source dependency and statistical extremes**. The pipeline makes these limitations visible; it has not resolved national sampling or independent source validation.

## Composition and sampling

The canonical interim extract contains 73,048 rows and 12 columns: five identifiers/metadata fields and seven numeric meteorological variables. It covers 9,131 daily labels from 2001-01-01 through 2025-12-31 at eight configured points. It contains environmental values, not records about individuals; no personal identifiers are part of the documented schema.

| Location label | Latitude | Longitude |
|---|---:|---:|
| Arusha | -3.3869 | 36.6830 |
| Dodoma | -6.1630 | 35.7516 |
| Dar_es_Salaam | -6.7924 | 39.2083 |
| Morogoro | -6.8235 | 37.6612 |
| Mbeya | -8.9094 | 33.4608 |
| Mwanza | -2.5164 | 32.9175 |
| Songea | -10.6833 | 35.6500 |
| Tabora | -5.0162 | 32.8266 |

Coordinates are requested point coordinates, not evidence of weather stations or municipal area averages. The selection is configured; a probability sampling design or national representativeness assessment is not documented. Each point has 9,131 expected days. Names are labels for requested points, not administrative boundary coverage.

Variables are mean/minimum/maximum 2 m temperature, relative humidity, corrected precipitation, 2 m wind and surface shortwave radiation. Types, units and day conventions are in the [dictionary](docs/data_dictionary.md).

## Acquisition and provenance

The source is NASA POWER's daily point endpoint, requested with agricultural community `AG` and JSON format. Serialized responses and SHA-256 fingerprints are preserved under `data/raw/nasa_power/` and `metadata/ingestion_manifest.json`. The saved ingestion summary completed at `2026-09-02T05:37:18.478815+00:00` and identifies interim SHA-256 `fdab2668f283fe9531b39506ebb4325a462d9283ed5434d1cfaa67e8d743a8b9`.

The inspected manifest-linked Arusha response records API `v2.9.6`, time convention `LST`, fill value `-999.0` and upstream labels `SYN1DEG`, `MERRA2`, `POWER`. These labels describe the preserved response; they do not establish independent provider validation. Day labels follow local solar time, not an assumed UTC or civil-time boundary. See the [lineage register](docs/data_lineage.md) for transformations and traceability gaps.

## Processing and quality

The pipeline assembles wide rows, validates them, melts seven variables into a dimensional fact table, pivots them into a daily serving mart and prepares illustrative ML features. Source meteorological extremes are not automatically clipped or removed. The quality report dated `2026-10-03T23:19:05.725856+00:00` reports PASS, zero error-rule failures and 12,529 IQR variable-value flags. No ordinary missing meteorological values or duplicate location-date rows were reported.

IQR screening pools locations and dates per variable; it is a statistical diagnostic, not proof of invalid weather. Precipitation has 8,350 flags (11.431%). Seasonal and location context and independent evidence are needed for review. The quality table exists in SQL but its observation-level flags are not populated by the loader.

A known metadata issue remains: raw solar units are `MJ/m²/day`, while the loader labels them `kWh/m2/day` without conversion. Use raw units for interpreting this baseline and resolve the discrepancy before energy calculations. Provider sentinel normalization, source revisions and end-to-end release fingerprints are not fully documented controls. PASS does not establish accuracy against ground stations.

## Products and ML partitions

| Product | Grain / baseline |
|---|---|
| Interim CSV | Location-date for the current source, 73,048 rows |
| DuckDB facts | Location-date-variable-source, 511,336 expected rows |
| Daily mart | Location-date-source, 73,048 baseline rows |
| Monthly view | Location-year-month, 2,400 groups; source is omitted from grouping |
| ML feature dataset | 72,800 location-days after history/target exclusions |
| Train | 52,352 rows; feature dates 2001-01-31 through 2018-12-31 |
| Validation | 8,768 rows; feature dates 2019-01-01 through 2021-12-31 |
| Test | 11,680 rows; feature dates 2022-01-01 through 2025-12-30 |

ML predicts precipitation on day t+1 using information through day t. Lag and shifted rolling features are computed within location without random shuffling. Thirty initial days and the last day per location lack sufficient history or a next-day target, removing 248 rows. Current splits use feature dates: the last training target falls on 2019-01-01 and the last validation target on 2022-01-01. Strict separation by target time requires a later boundary purge or split review. These exports do not establish model performance, deployment readiness or generalization to unseen locations.

The current ML groups by location and the monthly view omits source. Both need review before multiple providers coexist. Daily same-day values also assume they are available at prediction time; publication delays are not modeled.

## Intended uses and limitations

Suitable current uses include reproducible exploratory summaries at the sampled points, SQL exercises, storage experiments and illustrative time-series feature preparation. National estimates, district area averages, operational disaster warnings, crop prescriptions and station-validated extreme-event claims require additional spatial, domain and validation work. Spatial expansion and cross-source harmonization remain future work.

Structural completeness cannot remove gridded-product uncertainty, local terrain effects or source bias. Do not treat the eight points as a nationally representative sample or remove rare events simply because they trigger pooled IQR thresholds.

## Distribution, maintenance and rights

Data locations and evidence are documented in this repository; their presence in a local workspace does not establish redistribution in Git or a formal published release. BigQuery was a separate demonstrated exercise, not an automated cloud refresh. The launcher supports scheduling, but a deployed schedule and refresh cadence are not established.

A dataset license, formal release version, upstream attribution/redistribution review and retention policy are not established by the reviewed files. Confirm applicable source terms before publishing a dataset release. This review makes no claim about current licensing terms. A future release should identify its owner, source retrieval dates, configuration, code version, environment, hashes, quality evidence and change history. Changed source values are not currently versioned by the `INSERT OR IGNORE` loader.

See [problem statement](docs/data_problem_statement.md), [schema rationale](docs/database_schema.md), [metrics](docs/metrics.md) and [lineage](docs/data_lineage.md). No pipeline code was changed for this datasheet.

## Team and publication availability

Team: [MEMBER 1], [MEMBER 2], [MEMBER 3], [MEMBER 4]. Submission date: [SUBMISSION DATE]. Data steward: [OWNER].

NASA's [data FAQ](https://power.larc.nasa.gov/docs/faqs/data/) reports nominal 2–3-day meteorological and 5–7-day solar latency; [source methodology](https://power.larc.nasa.gov/docs/methodology/data/sources/) describes retrospective updates. Consulted 2026-10-04. Actual publication timestamps are not retained in the export, so same-day predictors and recent rolling windows cannot be presumed available for an operational next-day forecast. The [every-column availability review](docs/ml_data_preparation.md) proposes exclusions and delayed windows; exports remain unchanged until Phase 2.

The personal-data assessment is supported by the identifiable-person definition in the [PDPC Act](https://www.pdpc.go.tz/media/media/THE_PERSONAL_DATA_PROTECTION_ACT.pdf). Weather values and configured city points do not identify people in this schema; linking household coordinates or individual records would require reassessment.

The [lab tracker](docs/lab_requirements_tracker.md) records all completion gaps, and the [Phase 1 audit](docs/phase1_evidence_audit.md) records fresh read-only counts. This root file is the canonical datasheet.

## Phase 2 release note

New availability-aware exports are separate from the historical 72,800-row files: 72,728 rows (52,288 train, 8,760 validation, 11,680 test). Same-day weather and short lags are excluded; histories use an eight-day delay and 16 target-boundary rows are purged. Actual publication-vintage availability remains unverified; no model accuracy is claimed. See [ML preparation](docs/ml_data_preparation.md) and [executed evidence](docs/phase2_implementation_and_evidence.md).

The retained ingestion coordinates for Morogoro and Songea differ from YAML. The established extract/request IDs were preserved; configuration reconciliation requires an explicit dataset-version decision. The composition table in this document has been aligned to the retained extract, while `configs/config.yaml` remains unchanged.

Solar-unit labels are corrected to MJ/m²/day by the updated loader, without converting raw values. This correction was executed in the isolated lab database; the original local database was intentionally left unchanged. Executed paired ingestion, quarantine, curated refresh and failure recovery have new retained evidence; they do not establish expanded spatial coverage or a second provider.
