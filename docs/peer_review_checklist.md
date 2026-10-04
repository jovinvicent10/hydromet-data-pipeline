# HydroMet-ETL — Capstone Peer Review Checklist

## 1. Purpose

This checklist supports structured peer review of the HydroMet-ETL
capstone before final submission and presentation.

The review is intended to answer five questions:

1. Is the pipeline technically correct?
2. Is the project reproducible?
3. Is the evidence consistent with the claims?
4. Can another team member understand and operate the project?
5. Is the project ready for assessment and demonstration?

The review principle is:

**Verify → Challenge → Correct → Re-test → Finalize**

---

# 2. Project Problem and Scope

- [ ] Project problem is clearly stated.
- [ ] Data-engineering motivation is clear.
- [ ] Tanzania study context is explained.
- [ ] NASA POWER is identified as the primary source.
- [ ] Eight-location point-based coverage is stated accurately.
- [ ] Project does not claim complete national spatial coverage.
- [ ] Limitations are explicitly documented.

Reviewer comments:

____________________________________________________________

---

# 3. Source and Ingestion

- [ ] NASA POWER source is documented.
- [ ] Variables are documented.
- [ ] Study period is documented.
- [ ] Ingestion is reproducible.
- [ ] Deterministic request identifiers are explained.
- [ ] Raw source payload handling is documented.
- [ ] SHA-256 fingerprints are documented.
- [ ] Cache behavior is explained.
- [ ] Retry behavior is explained.
- [ ] Idempotency is explained.
- [ ] Ingestion manifest is available.
- [ ] Repeated ingestion does not create duplicate observations.

Reviewer comments:

____________________________________________________________

---

# 4. Configuration and Provenance

- [ ] Location configuration is documented.
- [ ] Configuration drift identified during capstone audit is disclosed.
- [ ] Morogoro coordinate difference is documented.
- [ ] Songea coordinate difference is documented.
- [ ] Existing baseline was not silently regenerated.
- [ ] Controlled migration is proposed for future correction.
- [ ] Dataset SHA-256 baseline is recorded.
- [ ] Data lineage implications are understood.

Reviewer comments:

____________________________________________________________

---

# 5. Data Profiling

- [ ] Initial profiling notebook is available.
- [ ] Advanced profiling notebook is available.
- [ ] Record counts are reported accurately.
- [ ] Date coverage is verified.
- [ ] Location coverage is verified.
- [ ] Missing-value checks are documented.
- [ ] Duplicate checks are documented.
- [ ] Physical plausibility checks are documented.
- [ ] Statistical extremes are interpreted carefully.
- [ ] IQR flags are not automatically classified as errors.

Reviewer comments:

____________________________________________________________

---

# 6. Data Quality

- [ ] Automated quality validator exists.
- [ ] Required schema is validated.
- [ ] Duplicate location-date grain is checked.
- [ ] Relative humidity bounds are checked.
- [ ] Precipitation non-negativity is checked.
- [ ] Wind-speed non-negativity is checked.
- [ ] Solar-radiation non-negativity is checked.
- [ ] Temperature consistency is checked.
- [ ] Coordinate bounds are checked.
- [ ] Date continuity is checked.
- [ ] Source consistency is checked.
- [ ] Dataset fingerprint is checked.
- [ ] Strict baseline mode is documented.

Expected baseline:

```text
Rows:           73,048
Locations:      8
Dates:          9,131
Error failures: 0
IQR flags:      12,529
Status:         PASS