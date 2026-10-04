# HydroMet-ETL ML Data Preparation

## 1. Purpose

Week 9 / Unit 8 extends HydroMet-ETL from analytical serving
into reproducible machine-learning data preparation.

The objective is not to train a predictive model at this
stage.

The objective is to produce:

- an ML-ready feature table,
- leakage-aware temporal features,
- reproducible training data,
- reproducible validation data,
- reproducible test data,
- and documented split metadata.

---

## 2. Illustrative Prediction Task

The current ML preparation stage uses the following
illustrative forecasting task:

> Use weather information available up to day t to support
> prediction of precipitation on day t+1.

The prediction target is:

`target_precip_next_day`

This target is derived independently for each location.

---

## 3. Source Dataset

The ML preparation stage consumes:

`mart_weather_daily`

This is the governed daily analytical product created during
Week 8 / Unit 7.

Its current grain is:

> One location × one observation date × one source.

Using the governed serving product avoids creating a separate
ad-hoc ML ingestion path.

---

## 4. Feature Engineering

### Calendar Features

The following calendar variables are created:

- month
- day of year

These allow future models to represent seasonal patterns.

### Historical Precipitation Lags

The pipeline creates:

- 1-day precipitation lag
- 3-day precipitation lag
- 7-day precipitation lag

These variables contain historical observations from the
same location.

### Rolling Historical Features

The pipeline creates:

- 7-day historical mean precipitation
- 30-day historical mean precipitation
- 7-day historical mean temperature
- 7-day historical mean relative humidity

Rolling calculations are shifted by one day before the
window is calculated.

This ensures that the rolling window represents historical
information rather than accidentally incorporating future
observations.

---

## 5. Target Engineering

For each location, next-day precipitation is created using a
negative shift of the precipitation series.

Conceptually:

Day t precipitation → available predictor information

Day t+1 precipitation → prediction target

The target column is not intended to be supplied as an input
feature to a model.

---

## 6. Data Leakage

Data leakage occurs when information that would not actually
be available at prediction time influences model training or
evaluation.

Leakage can make model performance appear unrealistically
strong.

HydroMet-ETL controls temporal leakage through:

1. chronological ordering,
2. location-specific lag generation,
3. historical rolling windows,
4. one-day shifting of rolling inputs,
5. separation of the next-day target from predictors,
6. chronological train/validation/test splitting,
7. no random shuffling of time periods.

---

## 7. Temporal Split Strategy

The dataset is divided chronologically.

### Training

Up to:

`2018-12-31`

### Validation

From:

`2019-01-01`

through:

`2021-12-31`

### Test

From:

`2022-01-01`

through:

`2025-12-31`

The split is deterministic and does not use random sampling.

---

## 8. Why Chronological Splitting?

Random splitting is often useful for independent and
identically distributed observations.

However, forecasting has a temporal direction.

A model intended to predict future conditions should be
evaluated on periods later than those used for model
development.

The HydroMet-ETL split therefore follows:

Past → Future

rather than randomly mixing dates across datasets.

---

## 9. Role of the Three Datasets

### Training Dataset

Used to estimate model parameters.

### Validation Dataset

Used during model development for tasks such as:

- model selection,
- hyperparameter selection,
- feature selection,
- threshold selection.

### Test Dataset

Reserved for final evaluation after model-development
decisions have been completed.

Repeatedly using the test dataset to tune the model would
turn it into another validation dataset.

---

## 10. Initial Missing Feature Rows

Lag and rolling features naturally create missing values at
the beginning of each location's time series.

For example, a 30-day historical rolling mean cannot be
computed until sufficient historical observations exist.

These rows are removed from the final ML-ready feature table.

The final observation for each location also lacks a
next-day target and is therefore removed.

This is expected feature-engineering behavior rather than a
source-data-quality failure.

---

## 11. Outputs

The pipeline generates:

`data/processed/ml_weather_features.parquet`

`data/processed/ml_weather_train.parquet`

`data/processed/ml_weather_validation.parquet`

`data/processed/ml_weather_test.parquet`

and:

`metadata/ml_split_metadata.json`

The metadata file records the split strategy, date
boundaries, row counts and leakage controls.

---

## 12. Reproducibility

Create the ML-ready datasets using:

```powershell
python -m src.ml.prepare_ml_data
```
## Prediction-time availability review (Phase 1)

For this review, the proposed prediction contract is a forecast issued at the end of local-solar day t for day t+1. The historical export lacks per-value publication timestamps and does not implement this as-of contract. NASA's [data FAQ](https://power.larc.nasa.gov/docs/faqs/data/) describes approximately 2–3 days of meteorological latency and 5–7 days for solar data; [source methodology](https://power.larc.nasa.gov/docs/methodology/data/sources/) also describes later retrospective updates. A past observation date alone does not prove that its value existed at forecast time. These sources were consulted on 2026-10-04; exact publication timing must be checked against the chosen product and operational evidence.

| Exported column(s) | Meaning / feature formula | Availability at forecast issue time | Proposed predictor decision; current export unchanged |
|---|---|---|---|
| observation_date | Feature date t | Known calendar information | Use to derive calendar features; retain as audit key |
| location_name | Configured location | Known | Optional categorical predictor; assess generalization to new points |
| latitude, longitude | Requested point coordinates | Known | Eligible static predictors |
| country | Constant Tanzania label | Known | Audit metadata; omit constant predictor |
| source_name | NASA_POWER provider label | Known | Audit metadata; omit constant predictor |
| t2m | Same-day mean temperature | Delayed meteorology | Exclude from a next-day operational predictor allowlist |
| t2m_min | Same-day minimum temperature | Delayed meteorology | Exclude |
| t2m_max | Same-day maximum temperature | Delayed meteorology | Exclude |
| rh2m | Same-day relative humidity | Delayed meteorology | Exclude |
| prectotcorr | Same-day rainfall | Delayed meteorology | Exclude |
| ws2m | Same-day wind speed | Delayed meteorology | Exclude |
| allsky_sfc_sw_dwn | Same-day solar radiation | Delayed solar plus unit metadata issue | Exclude |
| month | Calendar month of t | Known in advance | Eligible; encodes annual seasonality |
| day_of_year | Calendar day number of t | Known in advance | Eligible; preserve leap-year interpretation |
| precip_lag_1 | Precipitation on t−1 | One-day-old meteorology may not yet be published | Exclude or replace with availability-safe lag |
| precip_lag_3 | Precipitation on t−3 | Borderline under nominal 2–3-day delay; exact publication time absent | Do not assume eligible; enforce as-of evidence or conservative lag |
| precip_lag_7 | Precipitation on t−7 | Nominal delay suggests availability, but historical vintage is unproven | Conditional only; verify publication/vintage or document conservative policy |
| precip_rolling_7d | Mean precipitation t−7 through t−1 | Window contains possibly unavailable recent days | Shift window farther back using validated availability policy |
| precip_rolling_30d | Mean precipitation t−30 through t−1 | Same recent-day issue | Shift window farther back |
| temperature_rolling_7d | Mean temperature t−7 through t−1 | Same recent-day issue | Shift window farther back |
| humidity_rolling_7d | Mean humidity t−7 through t−1 | Same recent-day issue | Shift window farther back |
| target_precip_next_day | Precipitation on t+1, generated by shift(−1) | Future outcome, observed later | Label only; always exclude from predictors |

This matrix covers all exported columns, including metadata and target. The export currently retains unavailable columns; documentation has not removed them. A future allowlist must explicitly select eligible predictors and validate every input's publication time. Calendar and static features are known ahead; lagged weather requires a source-availability policy. If availability evidence cannot be obtained, present the dataset as retrospective feature preparation rather than a proven operational next-day forecast.

### Target boundaries and feature history

Splits currently use feature date. Thus the eight training rows dated 2018-12-31 have targets dated 2019-01-01, and the eight validation rows dated 2021-12-31 have targets dated 2022-01-01. For strict target-time separation, purge these boundary rows or split by target date, then recompute counts and tests. Existing counts remain historical until that change is executed.

Historical windows for holdout dates may use preceding training-period weather if it would have been available at the prediction time; that is not inherently leakage. Retrospectively revised source values and unknown publication timestamps are separate risks. No model is trained, and no predictive accuracy or operational readiness is verified.

## Phase 2 availability-aware export

The updated module produces separate `ml_weather_availability_*.parquet` artifacts. It exports only audit keys, static/calendar predictors, delayed histories and target. Meteorological histories use an eight-day delay: 7-day means cover t−14 through t−8, and the 30-day precipitation mean covers t−37 through t−8. Precipitation lags are t−8, t−14 and t−30. Same-day weather, short lags and solar measurements are excluded from the predictor allowlist; the target remains label-only.

Executed isolated results: 72,728 rows, including 52,288 train / 8,760 validation / 11,680 test. The first 37 days and final day per location remove 304 rows; eight rows at each of two holdout boundaries remove another 16. Training features end 2018-12-30 with targets ending 2018-12-31; validation features end 2021-12-30 with targets ending 2021-12-31. Test features end 2025-12-30 with targets ending 2025-12-31.

The historical feature counts and matrix above describe the earlier export; the new implementation excludes the unavailable raw predictor columns and uses the revised names/formulas above. Source/date metadata are audit fields, not automatically model inputs. Tests verify future/recent weather changes cannot alter the feature values at a fixed issue date, windows use the intended old observations, missing days are rejected and target dates do not cross holdout boundaries.

The lag policy exceeds nominal publication delay but lacks actual issue-time source vintages. It is an implemented conservative retrospective experiment, not certified operational availability. Evidence and file fingerprints: `outputs/evidence/ml_availability_results.json`.
