# HydroMet-ETL Governance and Data Quality

## 1. Governance Objective

Data governance defines the rules, responsibilities, controls and
evidence used to ensure that data remains trustworthy, traceable,
secure and appropriate for its intended use.

HydroMet-ETL applies governance through:

- source documentation;
- data lineage;
- quality rules;
- reproducible ingestion;
- integrity checks;
- version control;
- controlled configuration;
- documented analytical outputs.

---

## 2. Data Quality as Code

Data-quality checks are implemented as executable Python rather than
manual notebook observations.

The validator is executed using:

```bash
python -m src.quality.validate_hydromet
```


## Unit 6 Validation Evidence

| Metric | Validated result |
|---|---:|
| Overall quality status | PASS |
| Rows | 73,048 |
| Locations | 8 |
| Unique dates | 9,131 |
| Error-rule failures | 0 |
| IQR statistical flags | 12,529 |
| Unit 6 tests | 8 passed |
| Full project tests | 25 passed |
| Dataset SHA-256 | fdab2668f283fe9531b39506ebb4325a462d9283ed5434d1cfaa67e8d743a8b9 |
## Phase 1 evidence and governance boundary

The table above records earlier Unit 6 evidence; its test counts are historical rather than current full-suite results. The retained orchestration test log reports 54 passes. The current read-only audit confirms the interim fingerprint and zero rows in `fact_quality_flag`. Aggregate quality reporting is implemented; rejected-row quarantine, reason codes and an isolated bad-row demonstration are missing.

Owners: [OWNER]. Team: [MEMBER 1], [MEMBER 2], [MEMBER 3], [MEMBER 4]. Submission date: [SUBMISSION DATE]. Statistical extremes are warnings, not automatic rejects; later quarantine should distinguish hard validity failures from reviewable events and preserve source rows.

The documented environmental fields and city-point coordinates do not identify individuals. This assessment follows the identifiable-person definition in the [PDPC's Personal Data Protection Act](https://www.pdpc.go.tz/media/media/THE_PERSONAL_DATA_PROTECTION_ACT.pdf), consulted 2026-10-04. Person-linked household/farm data or user records would require a new assessment and appropriate controls; this is not a blanket finding of institutional compliance.

See the [tracker](lab_requirements_tracker.md), [datasheet](../DATASHEET.md) and [evidence audit](phase1_evidence_audit.md).

## Phase 2 quality proof

`src/quality/quarantine.py` implements row reason codes, retains original rejected values and row numbers, and checks read = accepted + rejected. Ingestion records accounting and blocks interim publication when hard-invalid rows occur. The quality CLI writes quarantine before attempting aggregate diagnostics, so malformed numeric input cannot disappear in an unhandled validation step; it exits nonzero on rejected rows.

The isolated proof deliberately introduced duplicate-key conflicts, humidity outside range, a missing temperature, negative rain, an invalid date and a provider wind fill value. Eleven input rows yielded four accepted and seven rejected; reason counts overlap when one row violates several rules. A large physically valid rainfall value was retained. The established archive was unchanged. Evidence: `outputs/evidence/quarantine_proof.json`, `bad_row_quality_gate.txt`; original rejected rows remain under ignored `data/processed/lab_evidence/bad_rows/`.
