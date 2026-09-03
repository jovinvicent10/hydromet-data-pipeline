from pathlib import Path

import pandas as pd

from src.quality.validate_hydromet import (
    EXPECTED_BASELINE,
    validate_hydromet,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "nasa_power_tanzania_daily.csv"
)


def test_quality_input_exists():
    assert DATA_PATH.exists()


def test_quality_pipeline_passes():
    report, _ = validate_hydromet(
        DATA_PATH,
        strict_baseline=True,
    )

    assert report["overall_status"] == "PASS"


def test_expected_row_count():
    report, _ = validate_hydromet(
        DATA_PATH,
        strict_baseline=True,
    )

    assert (
        report["rows"]
        == EXPECTED_BASELINE["rows"]
    )


def test_expected_locations():
    report, _ = validate_hydromet(
        DATA_PATH,
        strict_baseline=True,
    )

    assert (
        report["locations"]
        == EXPECTED_BASELINE["locations"]
    )


def test_no_duplicate_location_dates():

    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["date"],
    )

    duplicate_count = df.duplicated(
        subset=["location", "date"]
    ).sum()

    assert duplicate_count == 0


def test_temperature_consistency():

    df = pd.read_csv(DATA_PATH)

    violations = (
        (df["T2M_MIN"] > df["T2M"])
        | (df["T2M"] > df["T2M_MAX"])
    ).sum()

    assert violations == 0


def test_relative_humidity_range():

    df = pd.read_csv(DATA_PATH)

    assert df["RH2M"].between(
        0,
        100,
    ).all()


def test_precipitation_non_negative():

    df = pd.read_csv(DATA_PATH)

    assert (
        df["PRECTOTCORR"] >= 0
    ).all()