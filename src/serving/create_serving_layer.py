"""
HydroMet-ETL
Unit 7 / Week 8: Analytics Serving Layer

Creates:
    1. mart_weather_daily
    2. vw_monthly_climate_summary

The serving layer converts the observation-level analytical
star schema into consumer-friendly analytical products.
"""

from pathlib import Path

import duckdb


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)

SQL_PATH = (
    PROJECT_ROOT
    / "sql"
    / "05_create_serving_layer.sql"
)


# ------------------------------------------------------------
# Expected current baseline
# ------------------------------------------------------------

EXPECTED_DAILY_ROWS = 73_048
EXPECTED_MONTHLY_ROWS = 2_400


def create_serving_layer():
    """
    Create and validate the HydroMet analytics serving layer.
    """

    print("=" * 60)
    print("HydroMet-ETL Analytics Serving Layer")
    print("=" * 60)

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {DATABASE_PATH}"
        )

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"Serving SQL file not found: {SQL_PATH}"
        )

    sql = SQL_PATH.read_text(encoding="utf-8")

    connection = duckdb.connect(str(DATABASE_PATH))

    try:
        print("\nCreating analytics serving layer...")

        connection.execute(sql)

        print("Serving layer created successfully.")

        # ----------------------------------------------------
        # Validate daily mart
        # ----------------------------------------------------

        daily_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM mart_weather_daily
            """
        ).fetchone()[0]

        daily_locations = connection.execute(
            """
            SELECT COUNT(DISTINCT location_name)
            FROM mart_weather_daily
            """
        ).fetchone()[0]

        duplicate_daily_grain = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    location_name,
                    observation_date,
                    source_name,
                    COUNT(*) AS row_count
                FROM mart_weather_daily
                GROUP BY
                    location_name,
                    observation_date,
                    source_name
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        # ----------------------------------------------------
        # Validate monthly consumer view
        # ----------------------------------------------------

        monthly_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_monthly_climate_summary
            """
        ).fetchone()[0]

        print("\nValidation")
        print("-" * 60)
        print(f"Daily mart rows:       {daily_rows:,}")
        print(f"Locations:             {daily_locations}")
        print(f"Duplicate daily grain: {duplicate_daily_grain}")
        print(f"Monthly view rows:     {monthly_rows:,}")

        # ----------------------------------------------------
        # Current baseline checks
        # ----------------------------------------------------

        if daily_rows != EXPECTED_DAILY_ROWS:
            raise ValueError(
                "Unexpected daily mart row count. "
                f"Expected {EXPECTED_DAILY_ROWS:,}, "
                f"found {daily_rows:,}."
            )

        if monthly_rows != EXPECTED_MONTHLY_ROWS:
            raise ValueError(
                "Unexpected monthly view row count. "
                f"Expected {EXPECTED_MONTHLY_ROWS:,}, "
                f"found {monthly_rows:,}."
            )

        if daily_locations != 8:
            raise ValueError(
                f"Expected 8 locations, found {daily_locations}."
            )

        if duplicate_daily_grain != 0:
            raise ValueError(
                "Duplicate rows detected in the daily mart grain."
            )

        print("\nServing layer validation: PASS")

        # ----------------------------------------------------
        # Display a sample
        # ----------------------------------------------------

        print("\nSample monthly climate records")
        print("-" * 60)

        sample = connection.execute(
            """
            SELECT *
            FROM vw_monthly_climate_summary
            ORDER BY location_name, year, month
            LIMIT 10
            """
        ).fetchdf()

        print(sample.to_string(index=False))

    finally:
        connection.close()


if __name__ == "__main__":
    create_serving_layer()