# HydroMet-ETL Cloud Architecture

## DSAI 6226 — Unit 5: Cloud Data Engineering

## 1. Purpose

This document describes how the HydroMet-ETL pipeline could be
implemented using cloud data-engineering services.

The objective is not to migrate every existing component to the
cloud immediately. Instead, the design demonstrates how the
existing reproducible HydroMet pipeline can evolve into a
cloud-based architecture while preserving:

- raw-data lineage;
- reproducibility;
- validation;
- data quality;
- analytical efficiency;
- cost awareness;
- security; and
- extensibility.

The design follows the principle of separating storage from compute.

---

## 2. Current Local Architecture

The current HydroMet-ETL implementation follows this pattern:

NASA POWER API
        |
        v
Python ingestion
        |
        v
Serialized raw JSON
        |
        v
Validated interim dataset
        |
        +------------------+
        |                  |
        v                  v
     Parquet            DuckDB
                           |
                           v
                    SQL / Analytics

The local architecture remains appropriate for the current dataset
because the dataset comfortably fits on one machine.

---

## 3. Proposed Cloud Architecture

                    NASA POWER API
                          |
                          | HTTPS
                          v
                +---------------------+
                | CLOUD INGESTION     |
                |                     |
                | Python job /        |
                | scheduled function  |
                |                     |
                | retries             |
                | validation          |
                | request IDs         |
                | logging             |
                +----------+----------+
                           |
                           v
                +---------------------+
                | OBJECT STORAGE      |
                | RAW ZONE            |
                |                     |
                | serialized JSON     |
                | manifest metadata   |
                | checksums           |
                +----------+----------+
                           |
                           v
                +---------------------+
                | VALIDATION AND      |
                | TRANSFORMATION      |
                |                     |
                | schema validation   |
                | quality checks      |
                | standardization     |
                | deterministic sort  |
                +----------+----------+
                           |
                           v
                +---------------------+
                | CURATED STORAGE     |
                |                     |
                | Parquet             |
                | partitioned files   |
                +----------+----------+
                           |
                           v
                +---------------------+
                | BIGQUERY            |
                | ANALYTICAL LAYER    |
                |                     |
                | SQL analytics       |
                | aggregate tables    |
                | date partitioning   |
                | controlled scans    |
                +----------+----------+
                           |
             +-------------+--------------+
             |             |              |
             v             v              v
         Dashboards      Reports      ML / Feature
                                      Engineering

---

## 4. Source Layer

The primary source is the NASA POWER Daily API.

The current project retrieves daily meteorological observations for
eight configured Tanzanian locations covering:

- 2001-01-01 to 2025-12-31;
- 9,131 dates;
- 73,048 location-day records;
- seven meteorological variables.

A cloud implementation would continue to access NASA POWER through
HTTPS rather than replacing the existing source.

---

## 5. Cloud Ingestion Layer

The ingestion component would execute the same core engineering
behaviour already demonstrated locally:

- deterministic request identifiers;
- bounded retries;
- exponential backoff;
- response validation;
- checksum generation;
- raw payload preservation;
- manifest-based provenance;
- duplicate protection;
- safe reruns;
- logging.

Possible cloud execution environments include a scheduled serverless
function or containerized batch job.

The design deliberately uses batch ingestion because the NASA POWER
weather data used in this project does not require second-level
streaming latency.

---

## 6. Object Storage and Raw Zone

Object storage would become the cloud equivalent of the project's
local `data/raw/` directory.

A conceptual structure could be:

gs://hydromet/raw/nasa_power/
gs://hydromet/curated/
gs://hydromet/metadata/

The raw zone would preserve:

- serialized NASA POWER JSON payloads;
- ingestion manifests;
- checksums;
- request metadata.

The raw layer should remain immutable where practical so that
downstream datasets can be reconstructed when transformation logic
changes.

No claim is made that this bucket has already been deployed. It is
part of the proposed cloud architecture.

---

## 7. Transformation and Quality Layer

Data would be validated before entering analytical storage.

Checks would include:

- expected schema;
- required columns;
- duplicate location-date records;
- date parsing;
- coordinate integrity;
- missing values;
- meteorological quality rules;
- statistical quality flags.

Extreme statistical values would be flagged rather than automatically
deleted.

---

## 8. Curated Parquet Layer

Validated datasets would be stored in Parquet.

Parquet is appropriate because it provides:

- columnar storage;
- typed values;
- compression;
- efficient analytical scanning;
- interoperability with multiple analytical engines.

For larger future datasets, files could be partitioned using fields
such as:

- year;
- source;
- region or spatial tile.

Partitioning should be introduced based on measured query patterns
rather than added unnecessarily to the small current dataset.

---

## 9. BigQuery Analytical Layer

BigQuery provides the cloud analytical warehouse layer.

For the Unit 5 experiment, a sample/full HydroMet wide dataset was
loaded into:

Project:
`hydromet-etl`

Dataset:
`hydromet`

Table:
`nasa_power_daily`

The loaded dataset was validated using SQL.

Observed result:

- 73,048 rows;
- 8 locations;
- minimum date: 2001-01-01;
- maximum date: 2025-12-31.

This matches the validated local HydroMet dataset.

---

## 10. BigQuery Cost-Awareness Experiment

A full-column query using:

SELECT *

was estimated by BigQuery to process:

7.04 MB

A query requesting only:

- date;
- location;
- PRECTOTCORR

was estimated to process:

1.74 MB.

The reduction was:

(7.04 - 1.74) / 7.04 x 100

approximately 75.3%.

This demonstrates an important cloud-engineering principle:

query design affects computational resource consumption and therefore
cost.

Columnar warehouses can avoid reading unnecessary columns when the
query explicitly requests only the required fields.

The current experiment should not be presented as evidence of
date-partition pruning because the demonstrated table was not shown
as a deliberately date-partitioned production table.

A future production version should consider partitioning the BigQuery
table by observation date if query patterns frequently target bounded
date ranges.

---

## 11. Aggregate Analysis

The following analytical query was executed:

monthly mean daily precipitation by:

- location;
- year; and
- month.

The query produced 2,400 grouped results.

BigQuery estimated that the query would process:

1.74 MB.

This confirms that the uploaded HydroMet dataset can be queried using
cloud analytical SQL.

---

## 12. Cost Model

The architecture considers four major cloud cost categories.

### 12.1 Storage

Raw JSON, curated Parquet, metadata and warehouse tables occupy cloud
storage.

Engineering response:

- preserve necessary raw data;
- use compressed analytical formats;
- define retention policies when appropriate;
- avoid unnecessary copies.

### 12.2 Compute

Transformation jobs consume compute resources.

Engineering response:

- run batch jobs only when needed;
- use serverless or scheduled compute where appropriate;
- terminate temporary resources after execution.

### 12.3 Bytes Scanned

Cloud analytical queries may incur cost based on the amount of data
read.

Engineering response:

- avoid unnecessary SELECT * queries;
- select only required columns;
- filter early;
- use partitioning where justified;
- review query estimates before executing large scans.

### 12.4 Egress

Moving data out of a cloud provider may incur network charges.

Engineering response:

- move computation to the data;
- avoid repeatedly downloading large raw datasets;
- export only required analytical results.

---

## 13. Security Design

### Least Privilege

Users and pipeline components should receive only the permissions
required to perform their tasks.

### Identity and Access Management

Cloud workloads should use managed identities and IAM roles rather
than credentials embedded directly in source code.

### Encryption

Data should remain encrypted in transit and at rest.

### Region Selection

Cloud region selection must consider:

- latency;
- cost;
- service availability;
- data governance;
- legal requirements.

For the current NASA POWER dataset, personal data is not being
processed. Nevertheless, region selection remains an important
architectural consideration for future datasets.

---

## 14. Why Spark Is Not Required

The current HydroMet dataset is small enough to fit comfortably on a
single machine.

The final wide CSV benchmark size was approximately:

5.98 MB.

Using a Spark cluster for this workload would introduce unnecessary:

- infrastructure;
- configuration;
- debugging complexity;
- cost.

The project therefore uses local analytical tools and introduces
BigQuery to demonstrate cloud architecture and cost-aware analytics,
not because distributed computation is currently required.

Spark would become justified only if future spatial and temporal data
volumes genuinely exceed practical single-machine processing limits.

---

## 15. Relationship Between Local and Cloud Architecture

The cloud design does not invalidate the existing local architecture.

Instead:

Local DuckDB
    = lightweight analytical engine for development and reproducible
      local analysis.

Parquet
    = portable analytical storage.

BigQuery
    = scalable cloud analytical warehouse.

Object storage
    = durable raw and curated cloud storage.

These technologies can coexist within the same data platform.

---

## 16. Recommended Evolution Path

The project should evolve incrementally.

Phase 1:
Current reproducible local pipeline.

Phase 2:
BigQuery analytical experimentation.

Phase 3:
Cloud object-storage raw and curated zones.

Phase 4:
Scheduled cloud ingestion.

Phase 5:
Additional sources such as CHIRPS.

Phase 6:
Cross-source harmonization and validation.

Phase 7:
Larger spatial datasets and agricultural analytics.

Phase 8:
Machine-learning feature pipelines and early-warning applications.

Cloud complexity should only be introduced when the engineering need
justifies it.

---

## 17. Conclusion

The Unit 5 implementation demonstrates that HydroMet-ETL can extend
from a reproducible local data pipeline into a cloud analytical
architecture.

The BigQuery experiment validated the same 73,048-row, eight-location
dataset used locally and demonstrated the relationship between query
design and bytes processed.

The proposed architecture preserves the principles established in
earlier units:

- reproducibility;
- explicit data architecture;
- idempotent ingestion;
- quality validation;
- open analytical storage;
- evidence-based technology selection.

The result is a cloud-ready architecture that can scale as future
data volume, source diversity and analytical requirements increase.