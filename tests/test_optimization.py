"""
Tests for HydroMet-ETL
Week 10 — Unit 9: Performance Optimization

The tests validate the correctness and evidence produced by
the CSV-to-Parquet optimization experiment.
"""

from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "nasa_power_tanzania_daily.csv"
)

PARQUET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nasa_power_tanzania_daily_optimized.parquet"
)

SUMMARY_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "optimization"
    / "optimization_summary.json"
)

COMPARISON_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "optimization"
    / "optimization_comparison.csv"
)


def load_summary():

    with open(
        SUMMARY_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def test_optimized_parquet_exists():

    assert PARQUET_PATH.exists()


def test_optimization_summary_exists():

    assert SUMMARY_PATH.exists()


def test_optimization_comparison_exists():

    assert COMPARISON_PATH.exists()


def test_same_row_count():

    csv_df = pd.read_csv(CSV_PATH)

    parquet_df = pd.read_parquet(
        PARQUET_PATH
    )

    assert len(csv_df) == len(parquet_df)


def test_expected_row_count():

    parquet_df = pd.read_parquet(
        PARQUET_PATH
    )

    assert len(parquet_df) == 73_048


def test_same_columns():

    csv_df = pd.read_csv(
        CSV_PATH,
        nrows=1,
    )

    parquet_df = pd.read_parquet(
        PARQUET_PATH
    )

    assert list(csv_df.columns) == list(
        parquet_df.columns
    )


def test_parquet_smaller_than_csv():

    assert (
        PARQUET_PATH.stat().st_size
        < CSV_PATH.stat().st_size
    )


def test_summary_confirms_same_dataset():

    summary = load_summary()

    assert (
        summary["methodology"][
            "same_logical_dataset"
        ]
        is True
    )

    assert (
        summary["methodology"][
            "equivalence_validation"
        ]
        is True
    )


def test_recorded_parquet_faster_than_csv():

    summary = load_summary()

    csv_median = summary["csv"][
        "median_seconds"
    ]

    parquet_median = summary["parquet"][
        "median_seconds"
    ]

    assert parquet_median < csv_median


def test_positive_speedup():

    summary = load_summary()

    assert (
        summary["improvement"]["speedup"]
        > 1
    )


def test_positive_storage_reduction():

    summary = load_summary()

    assert (
        summary["improvement"][
            "storage_reduction_percent"
        ]
        > 0
    )