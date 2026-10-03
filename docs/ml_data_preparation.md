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