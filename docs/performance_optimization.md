# HydroMet-ETL Performance Optimization

## 1. Overview

Week 10 / Unit 9 focuses on performance profiling and
evidence-based optimization.

The objective was not to optimize arbitrary parts of the
pipeline.

Instead, HydroMet-ETL followed the engineering cycle:

Measure → Identify Bottleneck → Optimize → Measure Again →
Validate Correctness → Document Results.

---

## 2. Baseline Profiling

Five representative pipeline operations were profiled.

Each operation used:

- one warm-up execution,
- ten measured repetitions,
- `time.perf_counter()` for timing,
- median, mean, standard deviation, minimum and maximum
  execution-time statistics.

The baseline median execution times were:

| Operation | Median Time (seconds) |
|---|---:|
| CSV loading | 0.085893 |
| DuckDB daily mart extraction | 0.074763 |
| ML feature engineering | 0.026488 |
| DuckDB monthly precipitation aggregation | 0.019933 |
| Parquet loading | 0.004224 |

CSV loading was the slowest measured baseline operation.

This provided an evidence-based optimization target.

---

## 3. Optimization Question

The optimization experiment investigated:

> Can repeated loading of the validated HydroMet daily
> dataset be accelerated by using Parquet instead of CSV
> while preserving the same logical dataset?

The experiment did not compare the wide CSV dataset with the
DuckDB star schema because those representations have
different grains and physical structures.

Instead, CSV and Parquet contained the same wide dataset.

---

## 4. Controlled Dataset

The optimization experiment used:

- 73,048 rows
- 12 columns

The authoritative validated CSV was converted into an
equivalent Parquet representation.

Before performance results were accepted, the two
representations were checked for:

- identical row count,
- identical columns,
- equivalent values,
- equivalent logical ordering after normalization.

Dataset equivalence passed successfully.

---

## 5. Benchmark Methodology

Both formats were measured under the same experimental
approach:

- one warm-up run,
- ten measured repetitions,
- the same logical dataset,
- the same Python environment,
- the same machine,
- `time.perf_counter()` timing.

Median execution time was used as the primary comparison
metric because it is less sensitive to occasional timing
variation than a single measurement.

---

## 6. Verified Performance Results

The controlled optimization experiment produced:

| Metric | CSV | Parquet |
|---|---:|---:|
| Median load time | 0.085139 s | 0.004924 s |
| Storage size | 5.977 MB | 0.958 MB |

The measured improvement was:

- 17.29× loading speedup
- 94.22% reduction in median loading time
- 83.98% reduction in physical storage size

Dataset equivalence:

**PASS**

Optimization experiment:

**PASS**

---

## 7. Interpretation

The results show that Parquet is substantially more efficient
than CSV for this repeated analytical loading workload.

The improvement should not be interpreted as meaning that
the complete HydroMet-ETL pipeline is 17.29 times faster.

The measured speedup applies specifically to loading the
73,048-row wide dataset during this controlled experiment.

---

## 8. Why Parquet Improves Analytical Loading

CSV is a text-oriented format.

When numerical data is read from CSV, the reader must parse
text and convert values into appropriate in-memory data
types.

Parquet is a typed columnar format designed for analytical
workloads.

It provides:

- typed storage,
- columnar organization,
- efficient compression,
- efficient analytical reads,
- column projection capabilities.

These properties make it suitable for repeated analytical
processing.

---

## 9. Storage Architecture Decision

The optimization does not require removing CSV from
HydroMet-ETL.

Instead, the formats serve different purposes.

### CSV

Useful for:

- interoperability,
- human-readable exchange,
- simple external inspection,
- compatibility with many tools.

### Parquet

Preferred for:

- repeated analytical reads,
- downstream data processing,
- efficient storage,
- analytical workflows.

### DuckDB

Continues to provide:

- dimensional analytical modelling,
- SQL querying,
- serving tables and views,
- governed analytical access.

The resulting architecture therefore treats Parquet and
DuckDB as complementary analytical technologies rather than
mutually exclusive replacements.

---

## 10. Relationship to Earlier Benchmarking

Week 4 compared physical storage and analytical performance
across CSV, Parquet and DuckDB.

Week 10 extends that work by following an explicit
optimization workflow.

First, representative operations were profiled.

Second, the slowest measured operation was identified.

Third, an optimization was selected.

Fourth, the same logical dataset was compared before and
after the optimization.

Finally, dataset equivalence was validated.

This makes the Week 10 experiment an optimization exercise
rather than merely a storage-format comparison.

---

## 11. Correctness Before Performance

Performance improvements are only useful when data
correctness is preserved.

For this reason, HydroMet-ETL verifies equivalence before
accepting the performance result.

The optimization experiment checks that CSV and Parquet
contain equivalent:

- row counts,
- columns,
- values.

This follows the principle:

> Optimize performance without changing the meaning of the
> data.

---

## 12. Reproducibility

Run baseline profiling using:

```powershell
python -m src.optimization.profile_pipeline