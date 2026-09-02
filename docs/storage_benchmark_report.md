# Week 4 Storage and Query Performance Benchmark

## HydroMet-ETL: A Reproducible Hydrometeorological Data Engineering Pipeline for Climate and Agricultural Analytics in Tanzania

## 1. Objective

The purpose of this benchmark is to evaluate the storage efficiency and analytical performance of different data storage approaches used in the HydroMet-ETL pipeline.

The experiment compares:

- CSV
- Parquet
- DuckDB using the same wide-format dataset
- DuckDB analytical star schema

The benchmark evaluates:

1. Storage size
2. Full dataset loading performance
3. Filter-query performance
4. Aggregation-query performance

The analytical DuckDB star schema is evaluated separately because its storage grain differs from the source-wide dataset.

---

## 2. Dataset

The benchmark uses the NASA POWER daily hydrometeorological dataset collected for eight locations in Tanzania.

The dataset contains:

- 73,048 location-day records
- Eight locations
- Daily observations from 2001 to 2025
- Seven meteorological variables

The meteorological variables are:

- T2M
- T2M_MIN
- T2M_MAX
- RH2M
- PRECTOTCORR
- WS2M
- ALLSKY_SFC_SW_DWN

For the physical-format comparison, the same 73,048-row wide dataset was represented in CSV, Parquet, and DuckDB.

This ensures that differences in performance primarily reflect the storage format rather than differences in data-model design.

---

## 3. Benchmark Methodology

Each benchmark function was executed once as an unmeasured warm-up run.

After the warm-up, each operation was executed ten times.

The following statistics were recorded:

- Mean execution time
- Median execution time
- Standard deviation
- Minimum execution time
- Maximum execution time

Median execution time is emphasized when comparing performance because it is less sensitive to occasional timing variability.

The benchmark was executed on the same computer and Python environment for all storage formats.

---

## 4. Physical Storage Comparison

The same wide-format dataset was stored using CSV, Parquet, and DuckDB.

### Results

| Storage Format | Storage Size (MB) | Median Load Time (s) | Median Filter Time (s) | Median Aggregation Time (s) |
|---|---:|---:|---:|---:|
| CSV | 5.976842 | 0.089954 | 0.089598 | 0.079378 |
| Parquet | 0.957728 | 0.004449 | 0.005411 | 0.012793 |
| DuckDB Wide | 1.261719 | 0.046459 | 0.014790 | 0.018984 |

---

## 5. Storage Efficiency

Parquet provided the smallest physical representation of the dataset.

CSV required approximately:

5.98 MB

while Parquet required approximately:

0.96 MB

and wide-format DuckDB required approximately:

1.26 MB.

Parquet therefore required approximately 84% less storage than CSV.

The results demonstrate the storage efficiency of compressed columnar formats for analytical datasets.

---

## 6. Full Dataset Loading Performance

The median loading times were:

- CSV: 0.089954 seconds
- Parquet: 0.004449 seconds
- DuckDB Wide: 0.046459 seconds

Parquet was approximately 20 times faster than CSV for loading the complete dataset.

This result reflects the advantages of a binary columnar representation compared with parsing text-based CSV data.

---

## 7. Filter Query Performance

The filtering benchmark retrieved observations for Arusha between 1 January 2020 and 31 December 2025.

Median execution times were:

- CSV: 0.089598 seconds
- Parquet: 0.005411 seconds
- DuckDB Wide: 0.014790 seconds

Parquet was approximately 16.6 times faster than CSV for this filtering operation.

DuckDB also substantially outperformed CSV.

The results show that analytical storage formats can reduce the amount of work required to execute selective analytical queries.

---

## 8. Aggregation Performance

The aggregation benchmark calculated mean monthly precipitation for each location.

Median execution times were:

- CSV: 0.079378 seconds
- Parquet: 0.012793 seconds
- DuckDB Wide: 0.018984 seconds

Parquet was approximately 6.2 times faster than CSV for this analytical aggregation.

DuckDB also performed significantly better than CSV.

---

## 9. DuckDB Star-Schema Analytical Benchmark

The production analytical database uses a long-form star schema rather than the wide representation used for the physical-format benchmark.

The fact table contains 511,336 observation-level records because each meteorological variable is stored as a separate observation.

The relationship is:

73,048 source rows × 7 meteorological variables = 511,336 fact observations.

Because the star schema has a different grain, its storage size and full-table performance should not be directly compared with the wide CSV, Parquet, and DuckDB representations.

Instead, realistic analytical queries were benchmarked separately.

### Star-Schema Results

| Query | Result Rows | Median Time (s) |
|---|---:|---:|
| All variables for Arusha, 2020–2025 | 15,344 | 0.035404 |
| Monthly precipitation by location | 2,400 | 0.020622 |

These results demonstrate that the analytical star schema can efficiently support realistic hydrometeorological analytical workloads.

---

## 10. Data Equivalence Validation

Before benchmarking, the pipeline validated that the CSV, Parquet, and wide DuckDB representations contained equivalent data.

The validation confirmed:

- Equal total row counts
- Equal filtered-result row counts
- Equal aggregation grouping keys
- Equivalent precipitation aggregation values within numerical tolerance

The equivalence validation passed successfully.

This is important because performance comparisons are meaningful only when the systems are processing equivalent data and analytical tasks.

---

## 11. Interpretation

The experiment demonstrates that no single storage technology should automatically be considered best for every data-engineering task.

CSV remains useful because it is portable, human-readable, and widely supported. However, its text-based structure results in larger storage requirements and slower analytical processing.

Parquet provided the strongest results for compact analytical file storage. It achieved the smallest storage size and the fastest performance for full loading, filtering, and aggregation in this experiment.

DuckDB provided strong analytical performance while also supporting SQL queries, relational modeling, dimensional schemas, constraints, views, and more complex analytical workflows.

Therefore, Parquet and DuckDB serve complementary roles within the HydroMet-ETL architecture rather than being direct replacements for one another.

---

## 12. Recommended Architecture

Based on the benchmark results, the HydroMet-ETL pipeline can use a layered storage architecture.

Raw API responses should remain preserved in the raw data layer for reproducibility and provenance.

Parquet is appropriate for processed analytical files because it provides compact storage and efficient column-oriented access.

DuckDB is appropriate for structured analytical modeling, SQL-based analysis, dimensional modeling, and downstream analytical workloads.

The proposed architecture is therefore:

NASA POWER API

→ Raw JSON preservation

→ Validated interim dataset

→ Parquet analytical files

→ DuckDB analytical star schema

→ SQL queries, reporting, visualization, and machine learning

---

## 13. Limitations

The benchmark was performed on a relatively small dataset of 73,048 wide-format records.

Performance differences may change as data volume increases.

The operating-system file cache and other system processes may also influence execution time.

The benchmark measures performance on one machine and should not be interpreted as a universal performance ranking across all hardware and workloads.

In addition, the DuckDB analytical star schema has a different storage grain from the wide physical representations. For this reason, it was intentionally benchmarked separately.

---

## 14. Conclusion

The Week 4 experiment successfully compared CSV, Parquet, and DuckDB for hydrometeorological data storage and analytics.

For the identical wide-format dataset, Parquet achieved the best combination of storage efficiency and analytical performance.

DuckDB also provided strong query performance and offers important advantages for structured analytical modeling and SQL-based workflows.

The benchmark therefore supports the use of Parquet for efficient analytical file storage and DuckDB for relational and analytical database workloads within HydroMet-ETL.

Most importantly, the experiment separates physical-format benchmarking from analytical-schema benchmarking, making the comparison reproducible and methodologically defensible.