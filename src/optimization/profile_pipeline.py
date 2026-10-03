"""
HydroMet-ETL
Week 10 — Unit 9: Performance Optimization

Baseline Pipeline Profiler

Purpose
-------
Measure representative HydroMet-ETL operations before optimization.

The profiler measures:
1. CSV loading
2. Parquet loading
3. DuckDB daily-mart extraction
4. DuckDB monthly analytical query
5. Pandas ML feature engineering

Methodology
-----------
- One warm-up execution is performed where appropriate.
- Each measured operation is repeated several times.
- Mean, median, standard deviation, minimum and maximum
  execution times are recorded.
- Results are written to CSV and JSON.
- No optimization is performed in this script.

This establishes the BEFORE measurement required for a
defensible performance-optimization experiment.
"""

from pathlib import Path
import json
import statistics
import time

import duckdb
import pandas as pd

from src.ml.prepare_ml_data import create_features


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
    / "nasa_power_tanzania_daily.parquet"
)

ML_FEATURES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml_weather_features.parquet"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "optimization"
)

BASELINE_CSV = (
    OUTPUT_DIR
    / "baseline_profile.csv"
)

BASELINE_JSON = (
    OUTPUT_DIR
    / "baseline_profile.json"
)


# ============================================================
# Profiling configuration
# ============================================================

REPETITIONS = 10
WARMUP_RUNS = 1


def timed_runs(function, repetitions=REPETITIONS):
    """
    Measure execution time for a callable.

    One warm-up run is performed before measured repetitions.
    """

    for _ in range(WARMUP_RUNS):
        function()

    timings = []

    for _ in range(repetitions):

        start = time.perf_counter()

        result = function()

        end = time.perf_counter()

        timings.append(end - start)

        # Explicitly release the result reference.
        del result

    return timings


def summarize_timings(operation, timings):
    """Convert raw timing observations into summary statistics."""

    return {
        "operation": operation,
        "repetitions": len(timings),
        "mean_seconds": statistics.mean(timings),
        "median_seconds": statistics.median(timings),
        "std_seconds": (
            statistics.stdev(timings)
            if len(timings) > 1
            else 0.0
        ),
        "min_seconds": min(timings),
        "max_seconds": max(timings),
    }


# ============================================================
# Operation 1 — CSV loading
# ============================================================

def load_csv():
    """Load the validated interim CSV dataset."""

    return pd.read_csv(
        CSV_PATH,
        parse_dates=["date"],
    )


# ============================================================
# Operation 2 — Parquet loading
# ============================================================

def load_parquet():
    """
    Load the wide Parquet representation.

    If the benchmark Parquet file is unavailable, use the
    generated ML feature Parquet file only as a fallback
    profiling workload.
    """

    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)

    if ML_FEATURES_PATH.exists():
        return pd.read_parquet(ML_FEATURES_PATH)

    raise FileNotFoundError(
        "No suitable Parquet dataset was found."
    )


# ============================================================
# Operation 3 — DuckDB daily mart extraction
# ============================================================

def load_daily_mart():
    """Read the complete governed daily serving mart."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        result = connection.execute(
            """
            SELECT *
            FROM mart_weather_daily
            ORDER BY location_name, observation_date
            """
        ).fetchdf()

    finally:
        connection.close()

    return result


# ============================================================
# Operation 4 — DuckDB analytical aggregation
# ============================================================

def monthly_precipitation_query():
    """
    Execute a representative analytical aggregation.

    The result contains monthly total precipitation by
    location and year.
    """

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        result = connection.execute(
            """
            SELECT
                location_name,
                EXTRACT(YEAR FROM observation_date) AS year,
                EXTRACT(MONTH FROM observation_date) AS month,
                SUM(prectotcorr) AS total_precipitation
            FROM mart_weather_daily
            GROUP BY
                location_name,
                year,
                month
            ORDER BY
                location_name,
                year,
                month
            """
        ).fetchdf()

    finally:
        connection.close()

    return result


# ============================================================
# Operation 5 — ML feature engineering
# ============================================================

def ml_feature_engineering():
    """
    Measure the feature-engineering transformation itself.

    The source daily mart is loaded before the timer for this
    operation begins so this benchmark isolates transformation
    cost rather than combining database I/O with feature
    engineering.
    """

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

    return create_features(df)


def prepare_ml_source():
    """
    Load the ML source once.

    This is used for the isolated ML transformation benchmark,
    preventing database-loading time from being included in
    every feature-engineering measurement.
    """

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


# ============================================================
# Validation
# ============================================================

def validate_inputs():
    """Ensure required baseline assets exist."""

    required = [
        CSV_PATH,
        DATABASE_PATH,
    ]

    for path in required:

        if not path.exists():

            raise FileNotFoundError(
                f"Required profiling input not found: {path}"
            )

    if not PARQUET_PATH.exists() and not ML_FEATURES_PATH.exists():

        raise FileNotFoundError(
            "No Parquet input is available for profiling."
        )


# ============================================================
# Main profiler
# ============================================================

def main():

    print("=" * 70)
    print("HydroMet-ETL — Week 10 / Unit 9")
    print("Baseline Performance Profiling")
    print("=" * 70)

    validate_inputs()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    print("\n[1/5] Profiling CSV loading...")

    timings = timed_runs(load_csv)

    summary = summarize_timings(
        "csv_load",
        timings,
    )

    results.append(summary)

    print(
        f"Median: "
        f"{summary['median_seconds']:.6f} seconds"
    )

    # --------------------------------------------------------
    # Parquet
    # --------------------------------------------------------

    print("\n[2/5] Profiling Parquet loading...")

    timings = timed_runs(load_parquet)

    summary = summarize_timings(
        "parquet_load",
        timings,
    )

    results.append(summary)

    print(
        f"Median: "
        f"{summary['median_seconds']:.6f} seconds"
    )

    # --------------------------------------------------------
    # DuckDB daily mart
    # --------------------------------------------------------

    print(
        "\n[3/5] Profiling DuckDB daily-mart extraction..."
    )

    timings = timed_runs(load_daily_mart)

    summary = summarize_timings(
        "duckdb_daily_mart_load",
        timings,
    )

    results.append(summary)

    print(
        f"Median: "
        f"{summary['median_seconds']:.6f} seconds"
    )

    # --------------------------------------------------------
    # DuckDB aggregation
    # --------------------------------------------------------

    print(
        "\n[4/5] Profiling DuckDB monthly aggregation..."
    )

    timings = timed_runs(
        monthly_precipitation_query
    )

    summary = summarize_timings(
        "duckdb_monthly_precipitation",
        timings,
    )

    results.append(summary)

    print(
        f"Median: "
        f"{summary['median_seconds']:.6f} seconds"
    )

    # --------------------------------------------------------
    # ML feature engineering
    # --------------------------------------------------------

    print(
        "\n[5/5] Profiling ML feature engineering..."
    )

    ml_source = prepare_ml_source()

    def feature_workload():
        return create_features(
            ml_source.copy()
        )

    timings = timed_runs(
        feature_workload
    )

    summary = summarize_timings(
        "ml_feature_engineering",
        timings,
    )

    results.append(summary)

    print(
        f"Median: "
        f"{summary['median_seconds']:.6f} seconds"
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    results_df = pd.DataFrame(results)

    results_df = results_df.sort_values(
        "median_seconds",
        ascending=False,
    ).reset_index(drop=True)

    results_df.to_csv(
        BASELINE_CSV,
        index=False,
    )

    metadata = {
        "pipeline": "HydroMet-ETL",
        "stage": (
            "Week 10 - Unit 9 "
            "Baseline Performance Profiling"
        ),
        "repetitions": REPETITIONS,
        "warmup_runs": WARMUP_RUNS,
        "timing_method": "time.perf_counter",
        "results": results_df.to_dict(
            orient="records"
        ),
    }

    temp_json = BASELINE_JSON.with_suffix(
        ".json.tmp"
    )

    with open(
        temp_json,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    temp_json.replace(BASELINE_JSON)

    # --------------------------------------------------------
    # Display ranking
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("BASELINE PERFORMANCE RANKING")
    print("=" * 70)

    display_columns = [
        "operation",
        "median_seconds",
        "mean_seconds",
        "min_seconds",
        "max_seconds",
    ]

    print(
        results_df[
            display_columns
        ].to_string(
            index=False
        )
    )

    slowest = results_df.iloc[0]

    print("\nSlowest measured operation:")
    print(
        f"{slowest['operation']} "
        f"({slowest['median_seconds']:.6f} seconds median)"
    )

    print("\nBaseline profiling: PASS")

    print("\nOutputs:")
    print(BASELINE_CSV)
    print(BASELINE_JSON)


if __name__ == "__main__":
    main()