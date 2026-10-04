# HydroMet-ETL — Concise Problem Statement

**Team:** JOVIN NJAU,DANIEL LAIZER,BAKARI MSHANA,MOHAMMED ALLY  
**Submission date:** 5OCTOBER2026  
**Repository:** https://github.com/jovinvicent10/hydromet-data-pipeline

Climate researchers and agricultural analysts need reproducible weather summaries to compare seasons, investigate historical rainfall and temperature, and prepare exploratory forecasting datasets. HydroMet-ETL uses NASA POWER daily data for eight configured Tanzanian points from 2001-01-01 to 2025-12-31: 73,048 location-day rows with seven weather variables. These are values returned for requested coordinates from gridded source products, not eight verified ground stations or national area averages.

The project preserves three original problems. **Limited spatial coverage:** eight points provide complete daily coverage for the selected period but do not establish representative national coverage; additional sampling must follow an explicit spatial plan. **Single-source dependency:** NASA POWER is the only integrated provider, so acquisition depends on it and independent cross-source validation is unavailable; a source-aware schema prepares for later harmonization but does not implement a second source. **Statistical extremes requiring careful interpretation:** pooled IQR screening identifies 12,529 unusual variable-values, including 8,350 precipitation values, but these may represent real events; automatic deletion would risk removing useful climate evidence.

The engineering objective is to make this extract reproducible, validated and traceable while exposing these limitations. Existing stages preserve raw JSON and checksums, assemble daily rows, execute quality rules, load a DuckDB star schema, refresh a wide daily serving table and prepare chronological ML features. Acceptance includes zero duplicate location-date keys, complete dates at each configured point, reconciliation of 73,048 × seven = 511,336 facts and transparent warning counts. Expanded spatial coverage, additional providers and persisted observation-level review remain future work.

Repeated precipitation sequences (including a 73-day identical-value run at Mbeya) and 11 dates with identical rainfall across all points are supporting diagnostic findings, not replacement problems or confirmed errors. They require contextual investigation, including dry-season interpretation.

Analysts may use the curated data for point-level historical summaries and research preparation. National estimates, operational warnings and deployment-ready next-day forecasting need further evidence. Known issues include solar-unit metadata disagreement and publication-latency/split-boundary concerns. Evidence and lab gaps are tracked in [the requirements tracker](lab_requirements_tracker.md); the full discussion is in [the problem statement](data_problem_statement.md).

This is a concise one-page-intended draft; final page count depends on submission formatting and has not been rendered or certified.
