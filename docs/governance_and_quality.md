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