from __future__ import annotations

import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import duckdb
import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# PROJECT PATHS
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

# Separate DuckDB used ONLY for fair wide-format benchmarking.
WIDE_DUCKDB_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nasa_power_tanzania_daily_wide.duckdb"
)

# Existing Week 2 analytical database.
STAR_DUCKDB_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)

BENCHMARK_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "benchmarks"
)

FIGURE_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "figures"
)

PHYSICAL_RESULTS_PATH = (
    BENCHMARK_DIR
    / "storage_benchmark_results.csv"
)

STAR_RESULTS_PATH = (
    BENCHMARK_DIR
    / "star_schema_benchmark_results.csv"
)

METADATA_PATH = (
    BENCHMARK_DIR
    / "benchmark_metadata.json"
)


# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

WIDE_TABLE_NAME = "weather_wide"

STAR_VIEW_NAME = "vw_weather_observations"

REPEATS = 10

FILTER_LOCATION = "Arusha"

FILTER_START_DATE = "2020-01-01"

FILTER_END_DATE = "2025-12-31"

PRECIPITATION_COLUMN = "PRECTOTCORR"


# ============================================================
# GENERAL UTILITIES
# ============================================================

def ensure_directories() -> None:

    PARQUET_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    BENCHMARK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def require_file(
    path: Path,
    label: str,
) -> None:

    if not path.exists():

        raise FileNotFoundError(
            f"{label} was not found:\n{path}"
        )


def file_size_mb(
    path: Path,
) -> float:

    return (
        path.stat().st_size
        / (1024 ** 2)
    )


# ============================================================
# BENCHMARK TIMER
# ============================================================

def benchmark_function(
    function: Callable[[], Any],
    repeats: int = REPEATS,
) -> dict[str, float]:

    """
    Run one unmeasured warm-up execution,
    followed by measured repetitions.

    Returns:
        mean
        median
        standard deviation
        minimum
        maximum
    """

    # --------------------------------------------------------
    # Warm-up
    # --------------------------------------------------------

    function()

    timings = []

    # --------------------------------------------------------
    # Measured repetitions
    # --------------------------------------------------------

    for _ in range(repeats):

        start = time.perf_counter()

        function()

        end = time.perf_counter()

        timings.append(
            end - start
        )

    return {

        "mean_seconds":
            statistics.mean(
                timings
            ),

        "median_seconds":
            statistics.median(
                timings
            ),

        "std_seconds":
            (
                statistics.stdev(
                    timings
                )
                if len(timings) > 1
                else 0.0
            ),

        "min_seconds":
            min(
                timings
            ),

        "max_seconds":
            max(
                timings
            ),
    }


def add_metric_columns(
    row: dict[str, Any],
    prefix: str,
    stats: dict[str, float],
) -> None:

    row[
        f"{prefix}_mean_seconds"
    ] = stats[
        "mean_seconds"
    ]

    row[
        f"{prefix}_median_seconds"
    ] = stats[
        "median_seconds"
    ]

    row[
        f"{prefix}_std_seconds"
    ] = stats[
        "std_seconds"
    ]

    row[
        f"{prefix}_min_seconds"
    ] = stats[
        "min_seconds"
    ]

    row[
        f"{prefix}_max_seconds"
    ] = stats[
        "max_seconds"
    ]


# ============================================================
# SOURCE DATA VALIDATION
# ============================================================

def load_source_csv() -> pd.DataFrame:

    require_file(
        CSV_PATH,
        "Interim NASA POWER CSV dataset",
    )

    df = pd.read_csv(
        CSV_PATH,
        parse_dates=[
            "date"
        ],
    )

    required_columns = {

        "date",

        "location",

        PRECIPITATION_COLUMN,
    }

    missing_columns = (
        required_columns
        .difference(
            df.columns
        )
    )

    if missing_columns:

        raise ValueError(
            "The interim CSV is missing "
            "required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    if df.empty:

        raise ValueError(
            "The interim CSV contains no rows."
        )

    return df


# ============================================================
# CREATE PARQUET
# ============================================================

def create_parquet(
    df: pd.DataFrame,
) -> None:

    df.to_parquet(
        PARQUET_PATH,
        index=False,
        compression="snappy",
    )


# ============================================================
# CREATE FAIR WIDE DUCKDB DATASET
# ============================================================

def create_wide_duckdb(
    df: pd.DataFrame,
) -> None:

    """
    Create a separate DuckDB database containing
    exactly the same wide dataset represented by
    CSV and Parquet.

    This ensures that the physical storage benchmark
    is an apples-to-apples comparison.
    """

    if WIDE_DUCKDB_PATH.exists():

        try:

            WIDE_DUCKDB_PATH.unlink()

        except PermissionError as exc:

            raise PermissionError(

                "The wide benchmark DuckDB file "
                "is currently locked:\n"
                f"{WIDE_DUCKDB_PATH}\n\n"
                "Close any program using it and "
                "run the benchmark again."

            ) from exc

    with duckdb.connect(
        str(
            WIDE_DUCKDB_PATH
        )
    ) as connection:

        connection.register(
            "source_dataframe",
            df,
        )

        connection.execute(
            f"""
            CREATE TABLE {WIDE_TABLE_NAME} AS

            SELECT *

            FROM source_dataframe
            """
        )

        connection.unregister(
            "source_dataframe"
        )

        duckdb_rows = (
            connection.execute(
                f"""
                SELECT COUNT(*)

                FROM {WIDE_TABLE_NAME}
                """
            )
            .fetchone()[0]
        )

    if duckdb_rows != len(df):

        raise RuntimeError(

            "Wide DuckDB row count does "
            "not match CSV row count.\n"

            f"CSV rows: {len(df):,}\n"

            f"DuckDB rows: {duckdb_rows:,}"
        )


# ============================================================
# PREPARE BENCHMARK DATA
# ============================================================

def prepare_benchmark_data() -> int:

    print(
        "Preparing benchmark datasets..."
    )

    df = load_source_csv()

    create_parquet(
        df
    )

    create_wide_duckdb(
        df
    )

    print(
        f"Source rows: {len(df):,}"
    )

    print(
        f"Parquet created: {PARQUET_PATH}"
    )

    print(
        f"Wide DuckDB created: "
        f"{WIDE_DUCKDB_PATH}"
    )

    return len(df)


# ============================================================
# VALIDATE EXISTING STAR SCHEMA
# ============================================================

def validate_star_schema() -> None:

    require_file(
        STAR_DUCKDB_PATH,
        "HydroMet analytical DuckDB database",
    )

    required_columns = {

        "observation_date",

        "year",

        "month",

        "location_name",

        "variable_code",

        "value",
    }

    with duckdb.connect(
        str(
            STAR_DUCKDB_PATH
        ),
        read_only=True,
    ) as connection:

        try:

            description = (
                connection.execute(
                    f"""
                    DESCRIBE {STAR_VIEW_NAME}
                    """
                )
                .fetchdf()
            )

        except duckdb.CatalogException as exc:

            raise RuntimeError(

                f"The required view "
                f"'{STAR_VIEW_NAME}' "
                "does not exist.\n\n"
                "Create the Week 2 analytical "
                "view before running this benchmark."

            ) from exc

        actual_columns = set(
            description[
                "column_name"
            ]
        )

        missing_columns = (
            required_columns
            .difference(
                actual_columns
            )
        )

        if missing_columns:

            raise RuntimeError(

                f"View '{STAR_VIEW_NAME}' "
                "is missing required columns: "

                + ", ".join(
                    sorted(
                        missing_columns
                    )
                )
            )


# ============================================================
# CSV - FULL LOAD
# ============================================================

def load_csv() -> pd.DataFrame:

    return pd.read_csv(
        CSV_PATH,
        parse_dates=[
            "date"
        ],
    )


# ============================================================
# PARQUET - FULL LOAD
# ============================================================

def load_parquet() -> pd.DataFrame:

    return pd.read_parquet(
        PARQUET_PATH
    )


# ============================================================
# WIDE DUCKDB - FULL LOAD
# ============================================================

def load_wide_duckdb() -> pd.DataFrame:

    with duckdb.connect(
        str(
            WIDE_DUCKDB_PATH
        ),
        read_only=True,
    ) as connection:

        return (
            connection.execute(
                f"""
                SELECT *

                FROM {WIDE_TABLE_NAME}
                """
            )
            .df()
        )


# ============================================================
# CSV FILTER BENCHMARK
# ============================================================

def filter_csv() -> pd.DataFrame:

    df = pd.read_csv(
        CSV_PATH,
        parse_dates=[
            "date"
        ],
    )

    return df[

        (
            df[
                "location"
            ]
            == FILTER_LOCATION
        )

        &

        (
            df[
                "date"
            ]
            >= FILTER_START_DATE
        )

        &

        (
            df[
                "date"
            ]
            <= FILTER_END_DATE
        )

    ]


# ============================================================
# PARQUET FILTER BENCHMARK
# ============================================================

def filter_parquet() -> pd.DataFrame:

    return pd.read_parquet(

        PARQUET_PATH,

        filters=[

            (
                "location",
                "==",
                FILTER_LOCATION,
            ),

            (
                "date",
                ">=",
                pd.Timestamp(
                    FILTER_START_DATE
                ),
            ),

            (
                "date",
                "<=",
                pd.Timestamp(
                    FILTER_END_DATE
                ),
            ),
        ],
    )


# ============================================================
# WIDE DUCKDB FILTER BENCHMARK
# ============================================================

def filter_wide_duckdb() -> pd.DataFrame:

    with duckdb.connect(
        str(
            WIDE_DUCKDB_PATH
        ),
        read_only=True,
    ) as connection:

        return (
            connection.execute(
                f"""
                SELECT *

                FROM {WIDE_TABLE_NAME}

                WHERE location = ?

                  AND date
                      BETWEEN ?
                          AND ?
                """,

                [

                    FILTER_LOCATION,

                    FILTER_START_DATE,

                    FILTER_END_DATE,
                ],
            )
            .df()
        )


# ============================================================
# CSV AGGREGATION
# ============================================================

def aggregate_csv() -> pd.DataFrame:

    df = pd.read_csv(

        CSV_PATH,

        usecols=[

            "date",

            "location",

            PRECIPITATION_COLUMN,
        ],

        parse_dates=[
            "date"
        ],
    )

    df[
        "year"
    ] = df[
        "date"
    ].dt.year

    df[
        "month"
    ] = df[
        "date"
    ].dt.month

    result = (

        df.groupby(

            [

                "location",

                "year",

                "month",
            ],

            as_index=False,

        )[
            PRECIPITATION_COLUMN
        ]

        .mean()

        .rename(

            columns={

                PRECIPITATION_COLUMN:
                    "mean_precipitation"
            }
        )
    )

    return result


# ============================================================
# PARQUET AGGREGATION
# ============================================================

def aggregate_parquet() -> pd.DataFrame:

    df = pd.read_parquet(

        PARQUET_PATH,

        columns=[

            "date",

            "location",

            PRECIPITATION_COLUMN,
        ],
    )

    df[
        "year"
    ] = df[
        "date"
    ].dt.year

    df[
        "month"
    ] = df[
        "date"
    ].dt.month

    result = (

        df.groupby(

            [

                "location",

                "year",

                "month",
            ],

            as_index=False,

        )[
            PRECIPITATION_COLUMN
        ]

        .mean()

        .rename(

            columns={

                PRECIPITATION_COLUMN:
                    "mean_precipitation"
            }
        )
    )

    return result


# ============================================================
# WIDE DUCKDB AGGREGATION
# ============================================================

def aggregate_wide_duckdb() -> pd.DataFrame:

    with duckdb.connect(
        str(
            WIDE_DUCKDB_PATH
        ),
        read_only=True,
    ) as connection:

        return (
            connection.execute(
                f"""
                SELECT

                    location,

                    EXTRACT(
                        YEAR
                        FROM date
                    )::INTEGER
                    AS year,

                    EXTRACT(
                        MONTH
                        FROM date
                    )::INTEGER
                    AS month,

                    AVG(
                        {PRECIPITATION_COLUMN}
                    )
                    AS mean_precipitation

                FROM {WIDE_TABLE_NAME}

                GROUP BY

                    location,

                    year,

                    month

                ORDER BY

                    location,

                    year,

                    month
                """
            )
            .df()
        )


# ============================================================
# STAR SCHEMA FILTER BENCHMARK
# ============================================================

def star_filter_query() -> pd.DataFrame:

    with duckdb.connect(

        str(
            STAR_DUCKDB_PATH
        ),

        read_only=True,

    ) as connection:

        return (
            connection.execute(
                f"""
                SELECT *

                FROM {STAR_VIEW_NAME}

                WHERE location_name = ?

                  AND observation_date
                      BETWEEN ?
                          AND ?
                """,

                [

                    FILTER_LOCATION,

                    FILTER_START_DATE,

                    FILTER_END_DATE,
                ],
            )
            .df()
        )


# ============================================================
# STAR SCHEMA AGGREGATION BENCHMARK
# ============================================================

def star_precipitation_aggregation() -> pd.DataFrame:

    with duckdb.connect(

        str(
            STAR_DUCKDB_PATH
        ),

        read_only=True,

    ) as connection:

        return (
            connection.execute(
                f"""
                SELECT

                    location_name
                        AS location,

                    year,

                    month,

                    AVG(value)
                        AS mean_precipitation

                FROM {STAR_VIEW_NAME}

                WHERE variable_code = ?

                GROUP BY

                    location_name,

                    year,

                    month

                ORDER BY

                    location_name,

                    year,

                    month
                """,

                [
                    PRECIPITATION_COLUMN
                ],
            )
            .df()
        )


# ============================================================
# NORMALIZE FILTER RESULTS
# ============================================================

def normalize_filter_result(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    result[
        "date"
    ] = pd.to_datetime(
        result[
            "date"
        ]
    )

    result = (

        result.sort_values(

            [

                "location",

                "date",
            ]
        )

        .reset_index(
            drop=True
        )
    )

    return result


# ============================================================
# NORMALIZE AGGREGATION RESULTS
# ============================================================

def normalize_aggregation_result(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    return (

        result[

            [

                "location",

                "year",

                "month",

                "mean_precipitation",
            ]
        ]

        .sort_values(

            [

                "location",

                "year",

                "month",
            ]
        )

        .reset_index(
            drop=True
        )
    )


# ============================================================
# VALIDATE EQUIVALENCE
# ============================================================

def validate_equivalence() -> dict[str, Any]:

    print(
        "Validating wide-format equivalence..."
    )

    # --------------------------------------------------------
    # Row counts
    # --------------------------------------------------------

    csv_load = load_csv()

    parquet_load = load_parquet()

    duckdb_load = load_wide_duckdb()

    row_counts = {

        "CSV":
            len(
                csv_load
            ),

        "Parquet":
            len(
                parquet_load
            ),

        "DuckDB_wide":
            len(
                duckdb_load
            ),
    }

    if len(
        set(
            row_counts.values()
        )
    ) != 1:

        raise RuntimeError(

            "Wide-format row counts differ: "

            f"{row_counts}"
        )

    # --------------------------------------------------------
    # Filter result counts
    # --------------------------------------------------------

    csv_filter = (
        normalize_filter_result(
            filter_csv()
        )
    )

    parquet_filter = (
        normalize_filter_result(
            filter_parquet()
        )
    )

    duckdb_filter = (
        normalize_filter_result(
            filter_wide_duckdb()
        )
    )

    filter_counts = {

        "CSV":
            len(
                csv_filter
            ),

        "Parquet":
            len(
                parquet_filter
            ),

        "DuckDB_wide":
            len(
                duckdb_filter
            ),
    }

    if len(
        set(
            filter_counts.values()
        )
    ) != 1:

        raise RuntimeError(

            "Filter result row counts differ: "

            f"{filter_counts}"
        )

    # --------------------------------------------------------
    # Aggregation validation
    # --------------------------------------------------------

    csv_aggregation = (
        normalize_aggregation_result(
            aggregate_csv()
        )
    )

    parquet_aggregation = (
        normalize_aggregation_result(
            aggregate_parquet()
        )
    )

    duckdb_aggregation = (
        normalize_aggregation_result(
            aggregate_wide_duckdb()
        )
    )

    key_columns = [

        "location",

        "year",

        "month",
    ]

    if not csv_aggregation[
        key_columns
    ].equals(
        parquet_aggregation[
            key_columns
        ]
    ):

        raise RuntimeError(

            "CSV and Parquet aggregation "
            "grouping keys differ."
        )

    if not csv_aggregation[
        key_columns
    ].equals(
        duckdb_aggregation[
            key_columns
        ]
    ):

        raise RuntimeError(

            "CSV and DuckDB aggregation "
            "grouping keys differ."
        )

    tolerance = 1e-9

    csv_parquet_difference = (

        csv_aggregation[
            "mean_precipitation"
        ]

        .sub(

            parquet_aggregation[
                "mean_precipitation"
            ]
        )

        .abs()

        .max()
    )

    csv_duckdb_difference = (

        csv_aggregation[
            "mean_precipitation"
        ]

        .sub(

            duckdb_aggregation[
                "mean_precipitation"
            ]
        )

        .abs()

        .max()
    )

    if (
        csv_parquet_difference
        > tolerance
    ):

        raise RuntimeError(

            "CSV and Parquet aggregation "
            "values differ beyond tolerance."
        )

    if (
        csv_duckdb_difference
        > tolerance
    ):

        raise RuntimeError(

            "CSV and DuckDB aggregation "
            "values differ beyond tolerance."
        )

    print(
        "Wide-format equivalence validation passed."
    )

    return {

        "row_counts":
            row_counts,

        "filter_result_counts":
            filter_counts,

        "aggregation_rows":
            len(
                csv_aggregation
            ),

        "aggregation_tolerance":
            tolerance,
    }


# ============================================================
# RUN PHYSICAL STORAGE BENCHMARK
# ============================================================

def run_physical_benchmarks() -> pd.DataFrame:

    print()

    print(
        "Running apples-to-apples "
        "physical-format benchmarks..."
    )

    storage_sizes = {

        "CSV":
            file_size_mb(
                CSV_PATH
            ),

        "Parquet":
            file_size_mb(
                PARQUET_PATH
            ),

        "DuckDB_wide":
            file_size_mb(
                WIDE_DUCKDB_PATH
            ),
    }

    load_functions = {

        "CSV":
            load_csv,

        "Parquet":
            load_parquet,

        "DuckDB_wide":
            load_wide_duckdb,
    }

    filter_functions = {

        "CSV":
            filter_csv,

        "Parquet":
            filter_parquet,

        "DuckDB_wide":
            filter_wide_duckdb,
    }

    aggregation_functions = {

        "CSV":
            aggregate_csv,

        "Parquet":
            aggregate_parquet,

        "DuckDB_wide":
            aggregate_wide_duckdb,
    }

    results = []

    for storage_type in [

        "CSV",

        "Parquet",

        "DuckDB_wide",

    ]:

        print(
            f"Benchmarking {storage_type}..."
        )

        load_stats = (
            benchmark_function(

                load_functions[
                    storage_type
                ]
            )
        )

        filter_stats = (
            benchmark_function(

                filter_functions[
                    storage_type
                ]
            )
        )

        aggregation_stats = (
            benchmark_function(

                aggregation_functions[
                    storage_type
                ]
            )
        )

        row = {

            "storage_type":
                storage_type,

            "storage_size_mb":
                storage_sizes[
                    storage_type
                ],
        }

        add_metric_columns(

            row,

            "load",

            load_stats,
        )

        add_metric_columns(

            row,

            "filter",

            filter_stats,
        )

        add_metric_columns(

            row,

            "aggregation",

            aggregation_stats,
        )

        results.append(
            row
        )

    results_df = (
        pd.DataFrame(
            results
        )
    )

    results_df.to_csv(

        PHYSICAL_RESULTS_PATH,

        index=False,
    )

    return results_df


# ============================================================
# RUN STAR-SCHEMA BENCHMARK
# ============================================================

def run_star_schema_benchmarks() -> pd.DataFrame:

    print()

    print(
        "Running DuckDB star-schema "
        "analytical benchmarks..."
    )

    benchmark_functions = {

        (
            "filter_all_variables_"
            "arusha_2020_2025"
        ):
            star_filter_query,

        (
            "monthly_precipitation_"
            "by_location"
        ):
            star_precipitation_aggregation,
    }

    results = []

    for (

        benchmark_name,

        function,

    ) in benchmark_functions.items():

        print(

            "Benchmarking star schema: "

            f"{benchmark_name}..."
        )

        stats = (
            benchmark_function(
                function
            )
        )

        result_df = (
            function()
        )

        row = {

            "benchmark":
                benchmark_name,

            "result_rows":
                len(
                    result_df
                ),
        }

        add_metric_columns(

            row,

            "query",

            stats,
        )

        results.append(
            row
        )

    results_df = (
        pd.DataFrame(
            results
        )
    )

    results_df.to_csv(

        STAR_RESULTS_PATH,

        index=False,
    )

    return results_df


# ============================================================
# CHART CREATION
# ============================================================

def save_bar_chart(

    dataframe: pd.DataFrame,

    x_column: str,

    y_column: str,

    title: str,

    y_label: str,

    output_path: Path,

) -> None:

    plt.figure(
        figsize=(
            8,
            5,
        )
    )

    plt.bar(

        dataframe[
            x_column
        ],

        dataframe[
            y_column
        ],
    )

    plt.title(
        title
    )

    plt.xlabel(
        "Storage format"
    )

    plt.ylabel(
        y_label
    )

    plt.tight_layout()

    plt.savefig(

        output_path,

        dpi=200,

        bbox_inches="tight",
    )

    plt.close()


def create_charts(
    physical_results: pd.DataFrame,
) -> None:

    save_bar_chart(

        physical_results,

        "storage_type",

        "storage_size_mb",

        "Physical Storage Size Comparison",

        "Storage size (MB)",

        FIGURE_DIR
        / "storage_size_comparison.png",
    )

    save_bar_chart(

        physical_results,

        "storage_type",

        "load_median_seconds",

        "Full Dataset Load Performance",

        "Median time (seconds)",

        FIGURE_DIR
        / "load_time_comparison.png",
    )

    save_bar_chart(

        physical_results,

        "storage_type",

        "filter_median_seconds",

        "Filtered Query Performance",

        "Median time (seconds)",

        FIGURE_DIR
        / "filter_query_comparison.png",
    )

    save_bar_chart(

        physical_results,

        "storage_type",

        "aggregation_median_seconds",

        (
            "Monthly Rainfall "
            "Aggregation Performance"
        ),

        "Median time (seconds)",

        FIGURE_DIR
        / "aggregation_query_comparison.png",
    )


# ============================================================
# BENCHMARK METADATA
# ============================================================

def save_metadata(

    source_rows: int,

    validation: dict[str, Any],

    physical_results: pd.DataFrame,

    star_results: pd.DataFrame,

) -> None:

    metadata = {

        "project":
            "HydroMet-ETL",

        "benchmark_generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "benchmark_methodology": {

            "warmup_runs_per_function":
                1,

            "measured_repetitions":
                REPEATS,

            "reported_statistics": [

                "mean",

                "median",

                "standard_deviation",

                "minimum",

                "maximum",
            ],
        },

        "source_dataset": {

            "path":
                str(
                    CSV_PATH.relative_to(
                        PROJECT_ROOT
                    )
                ),

            "rows":
                source_rows,
        },

        "physical_format_comparison": {

            "description":

                (
                    "CSV, Parquet and DuckDB_wide "
                    "contain the same source-wide "
                    "dataset. This provides an "
                    "apples-to-apples physical "
                    "storage and query comparison."
                ),

            "results_file":

                str(

                    PHYSICAL_RESULTS_PATH
                    .relative_to(
                        PROJECT_ROOT
                    )
                ),
        },

        "star_schema_benchmark": {

            "description":

                (
                    "The analytical DuckDB star "
                    "schema is benchmarked separately "
                    "because its grain differs from "
                    "the wide source dataset."
                ),

            "database":

                str(

                    STAR_DUCKDB_PATH
                    .relative_to(
                        PROJECT_ROOT
                    )
                ),

            "view":
                STAR_VIEW_NAME,

            "results_file":

                str(

                    STAR_RESULTS_PATH
                    .relative_to(
                        PROJECT_ROOT
                    )
                ),
        },

        "filter_definition": {

            "location":
                FILTER_LOCATION,

            "start_date":
                FILTER_START_DATE,

            "end_date":
                FILTER_END_DATE,
        },

        "aggregation_definition": {

            "variable":
                PRECIPITATION_COLUMN,

            "operation":
                (
                    "Mean monthly precipitation "
                    "by location"
                ),
        },

        "equivalence_validation":
            validation,

        "environment": {

            "python_version":
                platform.python_version(),

            "platform":
                platform.platform(),

            "pandas_version":
                pd.__version__,

            "duckdb_version":
                duckdb.__version__,
        },

        "physical_result_rows":
            len(
                physical_results
            ),

        "star_schema_result_rows":
            len(
                star_results
            ),
    }

    temporary_path = (
        METADATA_PATH.with_suffix(
            ".json.tmp"
        )
    )

    with temporary_path.open(

        "w",

        encoding="utf-8",

    ) as file:

        json.dump(

            metadata,

            file,

            indent=2,
        )

    temporary_path.replace(
        METADATA_PATH
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    ensure_directories()

    print(
        "=" * 72
    )

    print(
        "HYDROMET-ETL STORAGE "
        "AND QUERY BENCHMARK"
    )

    print(
        "=" * 72
    )

    print()

    # --------------------------------------------------------
    # Prepare equivalent physical representations
    # --------------------------------------------------------

    source_rows = (
        prepare_benchmark_data()
    )

    # --------------------------------------------------------
    # Validate analytical database
    # --------------------------------------------------------

    validate_star_schema()

    # --------------------------------------------------------
    # Validate result equivalence
    # --------------------------------------------------------

    validation = (
        validate_equivalence()
    )

    # --------------------------------------------------------
    # Fair physical benchmark
    # --------------------------------------------------------

    physical_results = (
        run_physical_benchmarks()
    )

    # --------------------------------------------------------
    # Analytical star-schema benchmark
    # --------------------------------------------------------

    star_results = (
        run_star_schema_benchmarks()
    )

    # --------------------------------------------------------
    # Figures
    # --------------------------------------------------------

    create_charts(
        physical_results
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    save_metadata(

        source_rows,

        validation,

        physical_results,

        star_results,
    )

    # --------------------------------------------------------
    # Console summary
    # --------------------------------------------------------

    print()

    print(
        "=" * 72
    )

    print(
        "PHYSICAL FORMAT "
        "BENCHMARK RESULTS"
    )

    print(
        "=" * 72
    )

    display_columns = [

        "storage_type",

        "storage_size_mb",

        "load_median_seconds",

        "filter_median_seconds",

        "aggregation_median_seconds",
    ]

    print(

        physical_results[
            display_columns
        ]

        .to_string(
            index=False
        )
    )

    print()

    print(
        "=" * 72
    )

    print(
        "STAR-SCHEMA ANALYTICAL "
        "BENCHMARK RESULTS"
    )

    print(
        "=" * 72
    )

    print(

        star_results.to_string(
            index=False
        )
    )

    print()

    print(
        "Benchmark completed successfully."
    )

    print(
        f"Physical results: "
        f"{PHYSICAL_RESULTS_PATH}"
    )

    print(
        f"Star-schema results: "
        f"{STAR_RESULTS_PATH}"
    )

    print(
        f"Metadata: "
        f"{METADATA_PATH}"
    )

    print(
        f"Figures: "
        f"{FIGURE_DIR}"
    )


if __name__ == "__main__":
    main()