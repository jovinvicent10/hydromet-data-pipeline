"""Conservative availability-aware historical ML preparation.

This is a retrospective experiment, not a reconstruction of source vintages.
An eight-day weather lag exceeds NASA's nominal meteorological delay; actual
publication timestamps and later revisions are not present in this archive.
"""
from pathlib import Path
import hashlib
import json
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / 'data/database/hydromet.duckdb'
OUTPUT_DIR = PROJECT_ROOT / 'data/processed'
METADATA_DIR = PROJECT_ROOT / 'metadata'
FEATURES_PATH = OUTPUT_DIR / 'ml_weather_availability_features.parquet'
TRAIN_PATH = OUTPUT_DIR / 'ml_weather_availability_train.parquet'
VALIDATION_PATH = OUTPUT_DIR / 'ml_weather_availability_validation.parquet'
TEST_PATH = OUTPUT_DIR / 'ml_weather_availability_test.parquet'
METADATA_PATH = METADATA_DIR / 'ml_availability_metadata.json'
TRAIN_END = pd.Timestamp('2018-12-31')
VALIDATION_START = pd.Timestamp('2019-01-01')
VALIDATION_END = pd.Timestamp('2021-12-31')
TEST_START = pd.Timestamp('2022-01-01')
TEST_END = pd.Timestamp('2025-12-31')
WEATHER_DELAY_DAYS = 8
PREDICTORS = ['latitude', 'longitude', 'month', 'day_of_year',
              'precip_lag_8', 'precip_lag_14', 'precip_lag_30',
              'precip_mean_7d_available', 'precip_mean_30d_available',
              'temperature_mean_7d_available', 'humidity_mean_7d_available']
AUDIT_COLUMNS = ['observation_date', 'target_date', 'location_name', 'source_name',
                 'latest_weather_observation_date', 'target_precip_next_day']


def load_daily_weather():
    with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
        df = connection.execute('SELECT * FROM mart_weather_daily ORDER BY location_name, source_name, observation_date').fetchdf()
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df


def create_features(df):
    df = df.sort_values(['location_name', 'source_name', 'observation_date']).reset_index(drop=True).copy()
    groups = df.groupby(['location_name', 'source_name'], sort=False)
    diffs = groups.observation_date.diff().dropna()
    if not diffs.eq(pd.Timedelta(days=1)).all():
        raise ValueError('Features require unique continuous daily observations per location/source')
    result = df[['observation_date', 'location_name', 'source_name', 'latitude', 'longitude']].copy()
    result['month'] = df.observation_date.dt.month
    result['day_of_year'] = df.observation_date.dt.dayofyear
    for lag in (8, 14, 30):
        result[f'precip_lag_{lag}'] = groups.prectotcorr.shift(lag)
    for source, name, window in [('prectotcorr','precip_mean_7d_available',7),
                                  ('prectotcorr','precip_mean_30d_available',30),
                                  ('t2m','temperature_mean_7d_available',7),
                                  ('rh2m','humidity_mean_7d_available',7)]:
        result[name] = groups[source].transform(lambda s: s.shift(WEATHER_DELAY_DAYS).rolling(window, min_periods=window).mean())
    result['latest_weather_observation_date'] = groups.observation_date.shift(WEATHER_DELAY_DAYS)
    result['target_precip_next_day'] = groups.prectotcorr.shift(-1)
    result['target_date'] = groups.observation_date.shift(-1)
    return result[AUDIT_COLUMNS + PREDICTORS]


def remove_incomplete_feature_rows(df):
    result = df.dropna(subset=PREDICTORS + ['target_precip_next_day', 'target_date', 'latest_weather_observation_date']).copy()
    # Remove observations whose target falls into the next holdout partition.
    crosses = ((result.observation_date <= TRAIN_END) & (result.target_date > TRAIN_END)) | ((result.observation_date <= VALIDATION_END) & (result.target_date > VALIDATION_END) & (result.observation_date >= VALIDATION_START))
    cleaned = result.loc[~crosses].reset_index(drop=True)
    cleaned.attrs['target_boundary_rows_removed'] = int(crosses.sum())
    cleaned.attrs['history_or_target_rows_removed'] = len(df) - len(result)
    return cleaned


def temporal_split(df):
    return (df.loc[(df.observation_date <= TRAIN_END) & (df.target_date <= TRAIN_END)].copy(),
            df.loc[(df.observation_date >= VALIDATION_START) & (df.target_date <= VALIDATION_END)].copy(),
            df.loc[(df.observation_date >= TEST_START) & (df.target_date <= TEST_END)].copy())


def validate_temporal_split(train, validation, test):
    if any(part.empty for part in (train, validation, test)):
        raise ValueError('Empty temporal partition')
    if train.target_date.max() >= validation.observation_date.min() or validation.target_date.max() >= test.observation_date.min():
        raise ValueError('Target crosses a holdout boundary')
    for part in (train, validation, test):
        if not (part.target_date - part.observation_date).eq(pd.Timedelta(days=1)).all():
            raise ValueError('Target must be the next calendar day')
        if not (part.observation_date - part.latest_weather_observation_date).ge(pd.Timedelta(days=WEATHER_DELAY_DAYS)).all():
            raise ValueError('Weather observation is too recent under the configured lag policy')


def save_outputs(features, train, validation, test):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for path, frame in [(FEATURES_PATH, features), (TRAIN_PATH, train), (VALIDATION_PATH, validation), (TEST_PATH, test)]:
        frame.to_parquet(path, index=False)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata = {'prediction_task': 'Issue at end of local-solar day t for precipitation on t+1',
                'weather_delay_days': WEATHER_DELAY_DAYS, 'predictor_allowlist': PREDICTORS,
                'excluded_predictors': ['t2m','t2m_min','t2m_max','rh2m','prectotcorr','ws2m','allsky_sfc_sw_dwn','precip_lag_1','precip_lag_3','target_precip_next_day'],
                'availability_status': 'Conservative lag assumption; actual publication timestamps and historical vintages unverified',
                'target_boundary_rows_removed': features.attrs.get('target_boundary_rows_removed', 0),
                'history_or_target_rows_removed': features.attrs.get('history_or_target_rows_removed', 0),
                'ml_ready_rows': len(features),
                'file_sha256': hashes, 'source_database': str(DATABASE_PATH),
                'train': {'rows':len(train), 'feature_end':str(train.observation_date.max().date()), 'target_end':str(train.target_date.max().date())},
                'validation': {'rows':len(validation), 'feature_end':str(validation.observation_date.max().date()), 'target_end':str(validation.target_date.max().date())},
                'test': {'rows':len(test), 'feature_end':str(test.observation_date.max().date()), 'target_end':str(test.target_date.max().date())}}
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return metadata


def main():
    original = load_daily_weather()
    features = remove_incomplete_feature_rows(create_features(original))
    train, validation, test = temporal_split(features)
    validate_temporal_split(train, validation, test)
    metadata = save_outputs(features, train, validation, test)
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
