# HydroMet-ETL Analytics Serving Layer

## 1. Purpose

The HydroMet-ETL analytics serving layer provides clean,
consumer-friendly analytical products derived from the
underlying DuckDB star schema.

The engineering layer stores meteorological observations at
a fine-grained level:

> One meteorological variable observed at one location on one
> date from one source.

This representation provides flexibility and extensibility,
but downstream analysts should not need to reconstruct the
weather dataset manually for common analytical tasks.

The serving layer therefore exposes simplified analytical
products.

---

## 2. Architecture

The serving architecture is:

NASA POWER API

↓

Reliable ingestion and raw preservation

↓

Validated interim dataset

↓

DuckDB dimensional model

↓

`vw_weather_observations`

↓

`mart_weather_daily`

↓

`vw_monthly_climate_summary`

↓

Analytics / dashboards / reporting / downstream ML

---

## 3. Daily Weather Mart

### Object

`mart_weather_daily`

### Type

Physical DuckDB table.

### Grain

One row per:

- observation date
- location
- source

For the current NASA POWER dataset this corresponds to one
daily weather record for each location.

### Current Expected Size

73,048 rows.

### Variables

The mart exposes the seven meteorological variables as
analytical columns:

- `t2m`
- `t2m_min`
- `t2m_max`
- `rh2m`
- `prectotcorr`
- `ws2m`
- `allsky_sfc_sw_dwn`

The underlying star schema stores these variables vertically
as observation records. The serving mart pivots them into a
wide representation suitable for common analytical
workflows.

---

## 4. Why Create a Serving Mart?

The star schema is optimized for structured analytical
storage and extensibility.

However, downstream consumers often require a simpler
interface.

Without the serving mart, an analyst would need to understand:

- fact tables
- dimension tables
- joins
- variable identifiers
- source identifiers
- pivoting logic

The serving mart hides this implementation complexity.

Consumers can work directly with a familiar daily weather
table.

This provides separation between:

1. engineering storage design, and
2. analytical consumption design.

---

## 5. Monthly Climate Consumer View

### Object

`vw_monthly_climate_summary`

### Type

DuckDB view.

### Grain

One row per:

- location
- year
- month

### Current Expected Size

2,400 rows.

This follows from:

8 locations × 25 years × 12 months = 2,400 records.

### Metrics

The view provides:

- mean temperature
- mean minimum temperature
- mean maximum temperature
- mean relative humidity
- total monthly precipitation
- mean wind speed
- mean solar radiation
- number of daily observations

---

## 6. Why Precipitation Is Summed

Daily precipitation represents an amount accumulated over a
daily period.

For monthly climate reporting, daily precipitation values are
therefore summed to obtain total monthly precipitation.

By contrast, variables such as temperature, relative
humidity, wind speed and solar radiation are summarized using
means in this consumer view.

---

## 7. Consumer Use Cases

The serving layer can support:

### Climate Analysis

Analysts can study seasonal and interannual climate
patterns.

### Agricultural Analytics

Monthly precipitation, temperature, humidity and solar
radiation can support crop and agricultural risk analysis.

### Dashboards

The monthly view provides a compact dataset suitable for
visualization and reporting.

### Machine Learning

The daily mart can serve as an upstream source for later
feature engineering.

However, ML-specific feature engineering and train,
validation and test splitting are intentionally handled
separately in the ML preparation stage.

This separation helps reduce the risk of data leakage.

---

## 8. Data Quality

The serving layer does not replace the HydroMet-ETL data
quality framework.

Quality validation occurs before analytical serving.

The existing quality framework checks:

- required columns
- missing values
- duplicate location-date records
- coordinate bounds
- relative humidity bounds
- non-negative precipitation
- non-negative wind speed
- non-negative solar radiation
- temperature consistency
- daily date continuity
- source consistency

Statistical IQR flags remain warnings rather than automatic
data errors.

---

## 9. Reproducibility

The serving layer is created using:

```powershell
python -m src.serving.create_serving_layer