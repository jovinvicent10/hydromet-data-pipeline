"""
Tests for HydroMet-ETL Week 9 / Unit 8
ML data preparation.
"""

from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

FEATURES_PATH = (
    PROCESSED_DIR
    / "ml_weather_features.parquet"
)

TRAIN_PATH = (
    PROCESSED_DIR
    / "ml_weather_train.parquet"
)

VALIDATION_PATH = (
    PROCESSED_DIR
    / "ml_weather_validation.parquet"
)

TEST_PATH = (
    PROCESSED_DIR
    / "ml_weather_test.parquet"
)


@pytest.fixture(scope="module")
def datasets():

    paths = [
        FEATURES_PATH,
        TRAIN_PATH,
        VALIDATION_PATH,
        TEST_PATH,
    ]

    for path in paths:
        if not path.exists():
            pytest.fail(
                f"Required ML dataset does not exist: {path}"
            )

    return {
        "features": pd.read_parquet(FEATURES_PATH),
        "train": pd.read_parquet(TRAIN_PATH),
        "validation": pd.read_parquet(
            VALIDATION_PATH
        ),
        "test": pd.read_parquet(TEST_PATH),
    }


def test_ml_feature_table_not_empty(datasets):

    assert not datasets["features"].empty


def test_all_eight_locations_preserved(datasets):

    assert (
        datasets["features"]["location_name"].nunique()
        == 8
    )


def test_required_ml_columns_exist(datasets):

    expected = {
        "month",
        "day_of_year",
        "precip_lag_1",
        "precip_lag_3",
        "precip_lag_7",
        "precip_rolling_7d",
        "precip_rolling_30d",
        "temperature_rolling_7d",
        "humidity_rolling_7d",
        "target_precip_next_day",
    }

    actual = set(
        datasets["features"].columns
    )

    assert expected.issubset(actual)


def test_required_ml_columns_have_no_missing_values(
    datasets,
):

    columns = [
        "precip_lag_1",
        "precip_lag_3",
        "precip_lag_7",
        "precip_rolling_7d",
        "precip_rolling_30d",
        "temperature_rolling_7d",
        "humidity_rolling_7d",
        "target_precip_next_day",
    ]

    assert (
        datasets["features"][columns]
        .isna()
        .sum()
        .sum()
        == 0
    )


def test_training_precedes_validation(datasets):

    train_max = pd.to_datetime(
        datasets["train"]["observation_date"]
    ).max()

    validation_min = pd.to_datetime(
        datasets["validation"]["observation_date"]
    ).min()

    assert train_max < validation_min


def test_validation_precedes_test(datasets):

    validation_max = pd.to_datetime(
        datasets["validation"]["observation_date"]
    ).max()

    test_min = pd.to_datetime(
        datasets["test"]["observation_date"]
    ).min()

    assert validation_max < test_min


def test_train_boundary(datasets):

    maximum = pd.to_datetime(
        datasets["train"]["observation_date"]
    ).max()

    assert maximum <= pd.Timestamp("2018-12-31")


def test_validation_boundaries(datasets):

    dates = pd.to_datetime(
        datasets["validation"]["observation_date"]
    )

    assert dates.min() >= pd.Timestamp(
        "2019-01-01"
    )

    assert dates.max() <= pd.Timestamp(
        "2021-12-31"
    )


def test_test_boundaries(datasets):

    dates = pd.to_datetime(
        datasets["test"]["observation_date"]
    )

    assert dates.min() >= pd.Timestamp(
        "2022-01-01"
    )

    assert dates.max() <= pd.Timestamp(
        "2025-12-31"
    )


def test_split_rows_reconstruct_feature_table(datasets):

    total = (
        len(datasets["train"])
        + len(datasets["validation"])
        + len(datasets["test"])
    )

    assert total == len(datasets["features"])