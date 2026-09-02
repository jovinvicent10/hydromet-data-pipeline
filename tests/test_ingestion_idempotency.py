from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

INTERIM_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "nasa_power_tanzania_daily.csv"
)


EXPECTED_ROWS = 73_048
EXPECTED_LOCATIONS = 8


def load_data():

    return pd.read_csv(
        INTERIM_PATH
    )


def test_interim_file_exists():

    assert INTERIM_PATH.exists()


def test_expected_row_count():

    df = load_data()

    assert len(df) == EXPECTED_ROWS


def test_expected_location_count():

    df = load_data()

    assert (
        df["location"].nunique()
        == EXPECTED_LOCATIONS
    )


def test_no_duplicate_location_dates():

    df = load_data()

    duplicates = df.duplicated(
        ["location", "date"]
    ).sum()

    assert duplicates == 0


def test_unique_source():

    df = load_data()

    assert (
        df["source"].nunique()
        == 1
    )

    assert (
        df["source"]
        .iloc[0]
        == "NASA_POWER"
    )
    
EXPECTED_COLUMNS = {
    "date",
    "location",
    "latitude",
    "longitude",
    "source",
    "T2M",
    "T2M_MIN",
    "T2M_MAX",
    "RH2M",
    "PRECTOTCORR",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
}

def test_expected_schema():

    df = load_data()

    assert EXPECTED_COLUMNS.issubset(
        set(df.columns)
    )

def test_no_missing_location_or_date():

    df = load_data()

    assert (
        df["location"]
        .isna()
        .sum()
        == 0
    )

    assert (
        df["date"]
        .isna()
        .sum()
        == 0
    )