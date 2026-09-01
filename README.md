# HydroMet-ETL

A reproducible hydrometeorological data engineering pipeline for climate
and agricultural analytics in Tanzania.

## Course

DSAI 6226 — Data Engineering and Analytics

## Project Objective

The project aims to design and implement a reproducible data engineering
pipeline for acquiring, validating, cleaning, transforming, storing and
serving hydrometeorological data.

## Initial Data Source

NASA POWER Daily API

## Study Area

Tanzania

## Initial Temporal Coverage

2001–2025

## Pipeline

Data Source → Ingestion → Raw Storage → Validation → Cleaning →
Transformation → Database / Parquet → Analytics → ML-ready datasets

## Project Status

Week 1 — Dataset adoption and initial data quality assessment.

## Data Architecture

HydroMet-ETL uses a dimensional analytical model implemented in
DuckDB.

### Fact Table

`fact_observation`

Grain:

> One meteorological variable observed at one location on one date
> from one data source.

### Dimensions

- `dim_date`
- `dim_location`
- `dim_variable`
- `dim_source`

### Quality Assurance

Observation-level quality information is stored separately in
`fact_quality_flag`, allowing potentially valid environmental extremes
to be flagged without altering the original observation.

See:

- `docs/database_schema.md`
- `docs/hydromet_er_diagram.md`