"""
HydroMet-ETL
Week 9 — Unit 8: ML Data Preparation

Purpose
-------
Create a reproducible machine-learning-ready weather dataset
from the governed daily analytical mart.

Illustrative ML task
--------------------
Use weather information available up to day t to support
prediction of precipitation on day t+1.

This module performs:
1. extraction from DuckDB,
2. chronological sorting,
3. leakage-aware feature engineering,
4. next-day target creation,
5. temporal train/validation/test splitting,
6. Parquet export,
7. split metadata export.
"""

from pathlib import Path
import json

import duckdb
import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

METADATA_DIR = (
    PROJECT_ROOT
    / "metadata"
)

FEATURES_PATH = OUTPUT_DIR / "ml_weather_features.parquet"
TRAIN_PATH = OUTPUT_DIR / "ml_weather_train.parquet"
VALIDATION_PATH = OUTPUT_DIR / "ml_weather_validation.parquet"
TEST_PATH = OUTPUT_DIR / "ml_weather_test.parquet"

METADATA_PATH = METADATA_DIR / "ml_split_metadata.json"


# ============================================================
# Temporal split boundaries
# ============================================================

TRAIN_END = pd.Timestamp("2018-12-31")
VALIDATION_START = pd.Timestamp("2019-01-01")
VALIDATION_END = pd.Timestamp("2021-12-31")
TEST_START = pd.Timestamp("2022-01-01")
TEST_END = pd.Timestamp("2025-12-31")


def load_daily_weather() -> pd.DataFrame:
    """Load the governed daily weather mart from DuckDB."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        df = connection.execute(
            """
            SELECT
                observation_date,
                location_name,
                latitude,
                longitude,
                country,
                source_name,
                t2m,
                t2m_min,
                t2m_max,
                rh2m,
                prectotcorr,
                ws2m,
                allsky_sfc_sw_dwn
            FROM mart_weather_daily
            ORDER BY location_name, observation_date
            """
        ).fetchdf()

    finally:
        connection.close()

    df["observation_date"] = pd.to_datetime(
        df["observation_date"]
    )

    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create leakage-aware temporal weather features.

    All lag and rolling calculations are performed separately
    for each location.
    """

    df = df.copy()

    df = df.sort_values(
        ["location_name", "observation_date"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Calendar features
    # --------------------------------------------------------

    df["month"] = df["observation_date"].dt.month
    df["day_of_year"] = df["observation_date"].dt.dayofyear

    # --------------------------------------------------------
    # Group by location
    # --------------------------------------------------------

    grouped = df.groupby(
        "location_name",
        group_keys=False,
    )

    # --------------------------------------------------------
    # Historical precipitation lags
    # --------------------------------------------------------

    df["precip_lag_1"] = grouped["prectotcorr"].shift(1)
    df["precip_lag_3"] = grouped["prectotcorr"].shift(3)
    df["precip_lag_7"] = grouped["prectotcorr"].shift(7)

    # --------------------------------------------------------
    # Historical rolling features
    #
    # shift(1) ensures the rolling window uses observations
    # strictly before the current day.
    # --------------------------------------------------------

    df["precip_rolling_7d"] = grouped[
        "prectotcorr"
    ].transform(
        lambda s: s.shift(1).rolling(
            window=7,
            min_periods=7,
        ).mean()
    )

    df["precip_rolling_30d"] = grouped[
        "prectotcorr"
    ].transform(
        lambda s: s.shift(1).rolling(
            window=30,
            min_periods=30,
        ).mean()
    )

    df["temperature_rolling_7d"] = grouped[
        "t2m"
    ].transform(
        lambda s: s.shift(1).rolling(
            window=7,
            min_periods=7,
        ).mean()
    )

    df["humidity_rolling_7d"] = grouped[
        "rh2m"
    ].transform(
        lambda s: s.shift(1).rolling(
            window=7,
            min_periods=7,
        ).mean()
    )

    # --------------------------------------------------------
    # Prediction target
    #
    # Tomorrow's precipitation is the outcome to predict.
    # It is not an input feature.
    # --------------------------------------------------------

    df["target_precip_next_day"] = grouped[
        "prectotcorr"
    ].shift(-1)

    return df


def remove_incomplete_feature_rows(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove rows that cannot have complete historical features
    or a next-day target.

    Early rows in each location naturally lack enough history
    for 30-day rolling features.

    The final row in each location naturally lacks a next-day
    target.
    """

    required_ml_columns = [
        "precip_lag_1",
        "precip_lag_3",
        "precip_lag_7",
        "precip_rolling_7d",
        "precip_rolling_30d",
        "temperature_rolling_7d",
        "humidity_rolling_7d",
        "target_precip_next_day",
    ]

    clean = df.dropna(
        subset=required_ml_columns
    ).copy()

    clean = clean.reset_index(drop=True)

    return clean


def temporal_split(df: pd.DataFrame):
    """
    Split data chronologically.

    Train:
        through 2018-12-31

    Validation:
        2019-01-01 through 2021-12-31

    Test:
        2022-01-01 through 2025-12-31

    No random shuffling is used.
    """

    train = df[
        df["observation_date"] <= TRAIN_END
    ].copy()

    validation = df[
        (
            df["observation_date"]
            >= VALIDATION_START
        )
        & (
            df["observation_date"]
            <= VALIDATION_END
        )
    ].copy()

    test = df[
        (
            df["observation_date"]
            >= TEST_START
        )
        & (
            df["observation_date"]
            <= TEST_END
        )
    ].copy()

    return train, validation, test


def validate_temporal_split(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
):
    """Verify chronological separation between datasets."""

    if train.empty:
        raise ValueError("Training dataset is empty.")

    if validation.empty:
        raise ValueError("Validation dataset is empty.")

    if test.empty:
        raise ValueError("Test dataset is empty.")

    if train["observation_date"].max() >= validation[
        "observation_date"
    ].min():
        raise ValueError(
            "Temporal leakage detected between "
            "training and validation datasets."
        )

    if validation[
        "observation_date"
    ].max() >= test["observation_date"].min():
        raise ValueError(
            "Temporal leakage detected between "
            "validation and test datasets."
        )


def save_outputs(
    features: pd.DataFrame,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
):
    """Save ML-ready datasets and reproducibility metadata."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    features.to_parquet(
        FEATURES_PATH,
        index=False,
    )

    train.to_parquet(
        TRAIN_PATH,
        index=False,
    )

    validation.to_parquet(
        VALIDATION_PATH,
        index=False,
    )

    test.to_parquet(
        TEST_PATH,
        index=False,
    )

    metadata = {
        "pipeline": "HydroMet-ETL",
        "stage": "Week 9 - Unit 8 ML Data Preparation",
        "prediction_task": (
            "Use weather information available up to day t "
            "to support prediction of precipitation on day t+1."
        ),
        "split_strategy": "chronological",
        "random_shuffle": False,
        "train": {
            "end": str(TRAIN_END.date()),
            "rows": int(len(train)),
            "actual_start": str(
                train["observation_date"].min().date()
            ),
            "actual_end": str(
                train["observation_date"].max().date()
            ),
        },
        "validation": {
            "start": str(VALIDATION_START.date()),
            "end": str(VALIDATION_END.date()),
            "rows": int(len(validation)),
            "actual_start": str(
                validation["observation_date"].min().date()
            ),
            "actual_end": str(
                validation["observation_date"].max().date()
            ),
        },
        "test": {
            "start": str(TEST_START.date()),
            "end": str(TEST_END.date()),
            "rows": int(len(test)),
            "actual_start": str(
                test["observation_date"].min().date()
            ),
            "actual_end": str(
                test["observation_date"].max().date()
            ),
        },
        "ml_ready_rows": int(len(features)),
        "locations": int(
            features["location_name"].nunique()
        ),
        "target": "target_precip_next_day",
        "leakage_controls": [
            "Chronological split",
            "No random shuffle",
            "Lag features calculated within location",
            "Rolling features shifted by one day",
            "Next-day precipitation used only as target",
        ],
    }

    temp_path = METADATA_PATH.with_suffix(".json.tmp")

    with open(
        temp_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )

    temp_path.replace(METADATA_PATH)


def main():
    """Execute the complete ML data preparation stage."""

    print("=" * 65)
    print("HydroMet-ETL — Week 9 / Unit 8")
    print("ML Data Preparation")
    print("=" * 65)

    print("\nLoading governed daily weather mart...")
    daily = load_daily_weather()

    print(f"Source rows: {len(daily):,}")
    print(
        f"Locations:   "
        f"{daily['location_name'].nunique()}"
    )

    print("\nCreating leakage-aware features...")
    features = create_features(daily)

    print("Removing rows without sufficient history/target...")
    features = remove_incomplete_feature_rows(features)

    print(f"ML-ready rows: {len(features):,}")

    print("\nCreating chronological splits...")

    train, validation, test = temporal_split(features)

    validate_temporal_split(
        train,
        validation,
        test,
    )

    print(
        f"Train:      {len(train):,} rows | "
        f"{train['observation_date'].min().date()} -> "
        f"{train['observation_date'].max().date()}"
    )

    print(
        f"Validation: {len(validation):,} rows | "
        f"{validation['observation_date'].min().date()} -> "
        f"{validation['observation_date'].max().date()}"
    )

    print(
        f"Test:       {len(test):,} rows | "
        f"{test['observation_date'].min().date()} -> "
        f"{test['observation_date'].max().date()}"
    )

    print("\nSaving Parquet datasets and metadata...")

    save_outputs(
        features,
        train,
        validation,
        test,
    )

    print("\nML data preparation validation: PASS")

    print("\nOutputs")
    print("-" * 65)
    print(FEATURES_PATH)
    print(TRAIN_PATH)
    print(VALIDATION_PATH)
    print(TEST_PATH)
    print(METADATA_PATH)


if __name__ == "__main__":
    main()