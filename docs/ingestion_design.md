# NASA POWER Ingestion Design

## Objective

The ingestion layer retrieves daily hydrometeorological data from the
NASA POWER API while ensuring reproducibility, integrity and safe
reruns.

## Idempotency

Each logical API request is assigned a deterministic request identifier
derived from the source, location, coordinates, date range and selected
parameters.

Before making an API call, the pipeline checks the ingestion manifest.
If the request has already completed successfully and the corresponding
raw file exists with a valid SHA-256 checksum, the cached raw response
is reused.

This prevents unnecessary API requests and ensures that rerunning the
same pipeline does not create duplicate data.

## Raw Data Preservation

Original API responses are stored in the raw data layer before
transformation.

Raw files are treated as immutable source evidence.

## Integrity Verification

SHA-256 checksums are calculated for raw files and the final interim
dataset.

A checksum mismatch causes the pipeline to stop rather than silently
processing altered data.

## Safe Writes

Files are first written to temporary paths and then atomically moved to
their final locations after successful completion.

This reduces the risk of leaving partially written files after a
pipeline failure.

## Retry Strategy

Transient API failures are handled using a bounded retry mechanism with
exponential backoff.

## Data Lineage

The ingestion manifest records:

- request identifier
- data source
- location
- coordinates
- requested date range
- requested parameters
- raw file location
- SHA-256 checksum
- processing status
- verification timestamp

## Validation

The transformed interim dataset is checked for:

- required columns
- empty results
- duplicate location-date records
- expected location count
- expected row count

## Demonstrated Idempotency

The ingestion pipeline was executed twice using the same configuration.

Both executions produced 73,048 records and the resulting interim
dataset had an identical SHA-256 checksum across runs.

This demonstrates that repeated execution of the same ingestion request
produces the same dataset without duplication.