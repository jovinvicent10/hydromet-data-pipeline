from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "nasa_power_tanzania_daily.csv"
)


# =========================================================
# Meteorological variable metadata
# =========================================================

VARIABLE_METADATA = {
    "T2M": {
        "name": "Mean air temperature at 2 metres",
        "unit": "degC",
        "description": "Daily mean air temperature at 2 metres",
    },
    "T2M_MIN": {
        "name": "Minimum air temperature at 2 metres",
        "unit": "degC",
        "description": "Daily minimum air temperature at 2 metres",
    },
    "T2M_MAX": {
        "name": "Maximum air temperature at 2 metres",
        "unit": "degC",
        "description": "Daily maximum air temperature at 2 metres",
    },
    "RH2M": {
        "name": "Relative humidity at 2 metres",
        "unit": "%",
        "description": "Daily relative humidity at 2 metres",
    },
    "PRECTOTCORR": {
        "name": "Corrected precipitation",
        "unit": "mm/day",
        "description": "Daily corrected precipitation",
    },
    "WS2M": {
        "name": "Wind speed at 2 metres",
        "unit": "m/s",
        "description": "Daily wind speed at 2 metres",
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "All-sky surface shortwave downward irradiance",
        "unit": "kWh/m2/day",
        "description": "Daily surface shortwave solar radiation",
    },
}


# =========================================================
# Utility functions
# =========================================================

def connect_database() -> duckdb.DuckDBPyConnection:
    """
    Open a connection to the HydroMet DuckDB database.
    """

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DATABASE_PATH}. "
            "Run create_database.py first."
        )

    return duckdb.connect(str(DATABASE_PATH))


def load_source_data() -> pd.DataFrame:
    """
    Load the interim NASA POWER dataset.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Input dataset not found at {DATA_PATH}."
        )

    df = pd.read_csv(DATA_PATH)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="raise",
    )

    return df


# =========================================================
# Dimension loaders
# =========================================================

def load_dim_location(
    connection: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
) -> None:
    """
    Load unique locations into dim_location.
    """

    locations = (
        df[
            [
                "location",
                "latitude",
                "longitude",
            ]
        ]
        .drop_duplicates()
        .sort_values("location")
        .reset_index(drop=True)
    )

    locations["location_id"] = (
        locations.index + 1
    )

    connection.register(
        "locations_df",
        locations,
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO dim_location (
            location_id,
            location_name,
            latitude,
            longitude,
            country
        )
        SELECT
            location_id,
            location,
            latitude,
            longitude,
            'Tanzania'
        FROM locations_df
        """
    )

    connection.unregister(
        "locations_df"
    )


def load_dim_date(
    connection: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
) -> None:
    """
    Generate and load the date dimension.
    """

    dates = pd.DataFrame(
        {
            "full_date":
                sorted(
                    df["date"]
                    .dropna()
                    .unique()
                )
        }
    )

    dates["full_date"] = pd.to_datetime(
        dates["full_date"]
    )

    dates["date_id"] = (
        dates["full_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    dates["year"] = (
        dates["full_date"].dt.year
    )

    dates["quarter"] = (
        dates["full_date"].dt.quarter
    )

    dates["month"] = (
        dates["full_date"].dt.month
    )

    dates["month_name"] = (
        dates["full_date"]
        .dt.month_name()
    )

    dates["day"] = (
        dates["full_date"].dt.day
    )

    dates["day_of_year"] = (
        dates["full_date"]
        .dt.dayofyear
    )

    dates["is_leap_year"] = (
        dates["full_date"]
        .dt.is_leap_year
    )

    connection.register(
        "dates_df",
        dates,
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO dim_date (
            date_id,
            full_date,
            year,
            quarter,
            month,
            month_name,
            day,
            day_of_year,
            is_leap_year
        )
        SELECT
            date_id,
            full_date,
            year,
            quarter,
            month,
            month_name,
            day,
            day_of_year,
            is_leap_year
        FROM dates_df
        """
    )

    connection.unregister(
        "dates_df"
    )


def load_dim_variable(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """
    Load meteorological variable metadata.
    """

    rows = []

    for variable_id, (
        code,
        metadata,
    ) in enumerate(
        VARIABLE_METADATA.items(),
        start=1,
    ):

        rows.append(
            {
                "variable_id": variable_id,
                "variable_code": code,
                "variable_name":
                    metadata["name"],
                "unit":
                    metadata["unit"],
                "description":
                    metadata["description"],
            }
        )

    variable_df = pd.DataFrame(rows)

    connection.register(
        "variable_df",
        variable_df,
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO dim_variable (
            variable_id,
            variable_code,
            variable_name,
            unit,
            description
        )
        SELECT
            variable_id,
            variable_code,
            variable_name,
            unit,
            description
        FROM variable_df
        """
    )

    connection.unregister(
        "variable_df"
    )


def load_dim_source(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """
    Load NASA POWER as the current source.
    """

    connection.execute(
        """
        INSERT OR IGNORE INTO dim_source (
            source_id,
            source_name,
            provider,
            temporal_resolution,
            description
        )
        VALUES (
            1,
            'NASA_POWER',
            'NASA POWER',
            'daily',
            'NASA POWER daily meteorological data'
        )
        """
    )


# =========================================================
# Transform source data to long form
# =========================================================

def transform_to_long(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert the wide source table to one-row-per-variable
    long-form observations.
    """

    variable_columns = list(
        VARIABLE_METADATA.keys()
    )

    long_df = df.melt(
        id_vars=[
            "date",
            "location",
            "latitude",
            "longitude",
        ],
        value_vars=variable_columns,
        var_name="variable_code",
        value_name="value",
    )

    return long_df


# =========================================================
# Fact loader
# =========================================================

def load_fact_observation(
    connection: duckdb.DuckDBPyConnection,
    long_df: pd.DataFrame,
) -> None:
    """
    Load long-form observations into fact_observation.
    """

    connection.register(
        "long_df",
        long_df,
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO fact_observation (
            observation_id,
            date_id,
            location_id,
            variable_id,
            source_id,
            value
        )

        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    d.date_id,
                    l.location_id,
                    v.variable_id
            )
            +
            COALESCE(
                (
                    SELECT MAX(
                        observation_id
                    )
                    FROM fact_observation
                ),
                0
            )
            AS observation_id,

            d.date_id,

            l.location_id,

            v.variable_id,

            s.source_id,

            x.value

        FROM long_df x

        JOIN dim_date d
            ON d.full_date = x.date

        JOIN dim_location l
            ON l.location_name = x.location

        JOIN dim_variable v
            ON v.variable_code =
               x.variable_code

        JOIN dim_source s
            ON s.source_name =
               'NASA_POWER'
        """
    )

    connection.unregister(
        "long_df"
    )


# =========================================================
# Validation
# =========================================================

def validate_load(
    connection: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
) -> None:
    """
    Validate expected dimensions and fact-table counts.
    """

    expected_locations = (
        df["location"].nunique()
    )

    expected_dates = (
        df["date"].nunique()
    )

    expected_variables = len(
        VARIABLE_METADATA
    )

    expected_fact_rows = (
        len(df)
        * expected_variables
    )

    actual_locations = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM dim_location
            """
        ).fetchone()[0]
    )

    actual_dates = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM dim_date
            """
        ).fetchone()[0]
    )

    actual_variables = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM dim_variable
            """
        ).fetchone()[0]
    )

    actual_sources = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM dim_source
            """
        ).fetchone()[0]
    )

    actual_fact_rows = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM fact_observation
            """
        ).fetchone()[0]
    )

    print("\n" + "=" * 60)
    print("DATABASE LOAD VALIDATION")
    print("=" * 60)

    print(
        f"Locations: "
        f"{actual_locations} / "
        f"{expected_locations}"
    )

    print(
        f"Dates: "
        f"{actual_dates} / "
        f"{expected_dates}"
    )

    print(
        f"Variables: "
        f"{actual_variables} / "
        f"{expected_variables}"
    )

    print(
        f"Sources: "
        f"{actual_sources}"
    )

    print(
        f"Fact rows: "
        f"{actual_fact_rows:,} / "
        f"{expected_fact_rows:,}"
    )

    assert (
        actual_locations
        == expected_locations
    )

    assert (
        actual_dates
        == expected_dates
    )

    assert (
        actual_variables
        == expected_variables
    )

    assert actual_sources >= 1

    assert (
        actual_fact_rows
        == expected_fact_rows
    )

    print(
        "\nAll database validation "
        "checks passed."
    )


# =========================================================
# Main loader
# =========================================================

def main() -> None:

    print(
        "Loading HydroMet data "
        "into DuckDB..."
    )

    df = load_source_data()

    print(
        f"Source rows: "
        f"{len(df):,}"
    )

    connection = connect_database()

    try:

        load_dim_location(
            connection,
            df,
        )

        load_dim_date(
            connection,
            df,
        )

        load_dim_variable(
            connection,
        )

        load_dim_source(
            connection,
        )

        long_df = (
            transform_to_long(df)
        )

        print(
            f"Long-form rows: "
            f"{len(long_df):,}"
        )

        load_fact_observation(
            connection,
            long_df,
        )

        validate_load(
            connection,
            df,
        )

    finally:

        connection.close()

    print(
        "\nHydroMet DuckDB load "
        "completed successfully."
    )


if __name__ == "__main__":
    main()