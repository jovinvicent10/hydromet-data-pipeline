"""
HydroMet-ETL
Week 10 — Unit 9: Performance Optimization

CSV-to-Parquet Optimization Experiment

Objective
---------
Determine whether an equivalent Parquet representation of the
validated HydroMet daily dataset reduces repeated data-loading
time relative to CSV while preserving dataset correctness.

Method
------
1. Load the validated CSV.
2. Create/recreate an equivalent Parquet representation.
3. Verify row count, columns and values.
4. Warm up both loading methods.
5. Benchmark CSV loading.
6. Benchmark Parquet loading.
7. Calculate speedup and percentage time reduction.
8. Save reproducible evidence.

Important
---------
This experiment compares the SAME logical wide dataset in
both formats. It does not compare the analytical star schema
against the wide CSV representation.
"""

from pathlib import Path
import hashlib
import json
import statistics
import time

import pandas as pd


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "nasa_power_tanzania_daily.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "optimization"
)

PARQUET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nasa_power_tanzania_daily_optimized.parquet"
)

RESULTS_CSV = (
    OUTPUT_DIR
    / "optimization_comparison.csv"
)

SUMMARY_JSON = (
    OUTPUT_DIR
    / "optimization_summary.json"
)


REPETITIONS = 10
WARMUP_RUNS = 1


# ============================================================
# Utilities
# ============================================================

def sha256_file(path: Path) -> str:
    """Calculate SHA-256 fingerprint for a file."""

    digest = hashlib.sha256()

    with open(path, "rb") as file:

        for chunk in iter(
            lambda: file.read(8192),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def measure(function):
    """Measure repeated execution time after warm-up."""

    for _ in range(WARMUP_RUNS):
        result = function()
        del result

    timings = []

    for _ in range(REPETITIONS):

        start = time.perf_counter()

        result = function()

        end = time.perf_counter()

        timings.append(end - start)

        del result

    return timings


def summarize(name, timings):
    """Summarize timing measurements."""

    return {
        "format": name,
        "repetitions": len(timings),
        "mean_seconds": statistics.mean(timings),
        "median_seconds": statistics.median(timings),
        "std_seconds": statistics.stdev(timings),
        "min_seconds": min(timings),
        "max_seconds": max(timings),
    }


# ============================================================
# Loading functions
# ============================================================

def read_csv():
    """Load source CSV."""

    return pd.read_csv(
        CSV_PATH,
        parse_dates=["date"],
    )


def read_parquet():
    """Load optimized Parquet representation."""

    return pd.read_parquet(
        PARQUET_PATH
    )


# ============================================================
# Dataset equivalence
# ============================================================

def normalize_for_comparison(df):
    """
    Normalize dataframe ordering before equivalence testing.

    Column ordering is retained from the source dataset.
    """

    result = df.copy()

    result["date"] = pd.to_datetime(
        result["date"]
    )

    result = result.sort_values(
        ["location", "date"]
    ).reset_index(drop=True)

    return result


def validate_equivalence(
    csv_df,
    parquet_df,
):
    """
    Verify that CSV and Parquet represent the same logical
    dataset.
    """

    csv_normalized = normalize_for_comparison(
        csv_df
    )

    parquet_normalized = normalize_for_comparison(
        parquet_df
    )

    if len(csv_normalized) != len(
        parquet_normalized
    ):
        raise ValueError(
            "Row-count mismatch between CSV and Parquet."
        )

    if list(csv_normalized.columns) != list(
        parquet_normalized.columns
    ):
        raise ValueError(
            "Column mismatch between CSV and Parquet."
        )

    pd.testing.assert_frame_equal(
        csv_normalized,
        parquet_normalized,
        check_dtype=False,
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )

    return True


# ============================================================
# Main experiment
# ============================================================

def main():

    print("=" * 70)
    print("HydroMet-ETL — Week 10 / Unit 9")
    print("CSV → Parquet Performance Optimization")
    print("=" * 70)

    if not CSV_PATH.exists():

        raise FileNotFoundError(
            f"Source CSV not found: {CSV_PATH}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PARQUET_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Load authoritative CSV
    # --------------------------------------------------------

    print("\nLoading authoritative CSV...")

    source_df = read_csv()

    print(
        f"Rows: {len(source_df):,}"
    )

    print(
        f"Columns: {len(source_df.columns)}"
    )

    # --------------------------------------------------------
    # Generate equivalent Parquet
    # --------------------------------------------------------

    print(
        "\nCreating equivalent optimized Parquet dataset..."
    )

    source_df.to_parquet(
        PARQUET_PATH,
        index=False,
    )

    # --------------------------------------------------------
    # Verify equivalence
    # --------------------------------------------------------

    print("\nValidating dataset equivalence...")

    parquet_df = read_parquet()

    validate_equivalence(
        source_df,
        parquet_df,
    )

    print("Dataset equivalence: PASS")

    # --------------------------------------------------------
    # File sizes
    # --------------------------------------------------------

    csv_size_bytes = CSV_PATH.stat().st_size
    parquet_size_bytes = PARQUET_PATH.stat().st_size

    csv_size_mb = (
        csv_size_bytes
        / (1024 ** 2)
    )

    parquet_size_mb = (
        parquet_size_bytes
        / (1024 ** 2)
    )

    storage_reduction_pct = (
        (
            csv_size_bytes
            - parquet_size_bytes
        )
        / csv_size_bytes
        * 100
    )

    # --------------------------------------------------------
    # Benchmark CSV
    # --------------------------------------------------------

    print(
        "\nBenchmarking CSV loading..."
    )

    csv_timings = measure(
        read_csv
    )

    csv_summary = summarize(
        "CSV",
        csv_timings,
    )

    # --------------------------------------------------------
    # Benchmark Parquet
    # --------------------------------------------------------

    print(
        "Benchmarking Parquet loading..."
    )

    parquet_timings = measure(
        read_parquet
    )

    parquet_summary = summarize(
        "Parquet",
        parquet_timings,
    )

    # --------------------------------------------------------
    # Calculate improvement
    # --------------------------------------------------------

    csv_median = csv_summary[
        "median_seconds"
    ]

    parquet_median = parquet_summary[
        "median_seconds"
    ]

    speedup = (
        csv_median
        / parquet_median
    )

    time_reduction_pct = (
        (
            csv_median
            - parquet_median
        )
        / csv_median
        * 100
    )

    # --------------------------------------------------------
    # Save comparison CSV
    # --------------------------------------------------------

    results_df = pd.DataFrame(
        [
            csv_summary,
            parquet_summary,
        ]
    )

    results_df.to_csv(
        RESULTS_CSV,
        index=False,
    )

    # --------------------------------------------------------
    # Integrity fingerprints
    # --------------------------------------------------------

    csv_sha256 = sha256_file(
        CSV_PATH
    )

    parquet_sha256 = sha256_file(
        PARQUET_PATH
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    summary = {
        "pipeline": "HydroMet-ETL",
        "stage": (
            "Week 10 - Unit 9 "
            "Performance Optimization"
        ),
        "optimization": (
            "Replace repeated analytical CSV reads "
            "with equivalent Parquet reads"
        ),
        "methodology": {
            "same_logical_dataset": True,
            "repetitions": REPETITIONS,
            "warmup_runs": WARMUP_RUNS,
            "timing_method": "time.perf_counter",
            "equivalence_validation": True,
        },
        "dataset": {
            "rows": int(len(source_df)),
            "columns": int(
                len(source_df.columns)
            ),
        },
        "csv": {
            **csv_summary,
            "size_mb": csv_size_mb,
            "sha256": csv_sha256,
        },
        "parquet": {
            **parquet_summary,
            "size_mb": parquet_size_mb,
            "sha256": parquet_sha256,
        },
        "improvement": {
            "speedup": speedup,
            "time_reduction_percent": (
                time_reduction_pct
            ),
            "storage_reduction_percent": (
                storage_reduction_pct
            ),
        },
    }

    temp_json = SUMMARY_JSON.with_suffix(
        ".json.tmp"
    )

    with open(
        temp_json,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    temp_json.replace(
        SUMMARY_JSON
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)

    print(
        f"CSV median load:      "
        f"{csv_median:.6f} seconds"
    )

    print(
        f"Parquet median load:  "
        f"{parquet_median:.6f} seconds"
    )

    print(
        f"Load speedup:         "
        f"{speedup:.2f}x"
    )

    print(
        f"Time reduction:       "
        f"{time_reduction_pct:.2f}%"
    )

    print(
        f"\nCSV size:             "
        f"{csv_size_mb:.3f} MB"
    )

    print(
        f"Parquet size:         "
        f"{parquet_size_mb:.3f} MB"
    )

    print(
        f"Storage reduction:    "
        f"{storage_reduction_pct:.2f}%"
    )

    print(
        "\nDataset equivalence:  PASS"
    )

    print(
        "Optimization experiment: PASS"
    )

    print("\nOutputs:")
    print(RESULTS_CSV)
    print(SUMMARY_JSON)
    print(PARQUET_PATH)


if __name__ == "__main__":
    main()