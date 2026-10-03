"""
Tests for the HydroMet-ETL analytics serving layer.
"""

from pathlib import Path

import duckdb
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)


@pytest.fixture
def connection():
    """Open a read-only DuckDB connection for testing."""

    if not DATABASE_PATH.exists():
        pytest.fail(
            f"DuckDB database does not exist: {DATABASE_PATH}"
        )

    con = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    yield con

    con.close()


def test_daily_mart_exists(connection):
    """The daily analytical mart should exist."""

    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'mart_weather_daily'
        """
    ).fetchone()[0]

    assert result == 1


def test_monthly_view_exists(connection):
    """The monthly consumer view should exist."""

    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.views
        WHERE table_name = 'vw_monthly_climate_summary'
        """
    ).fetchone()[0]

    assert result == 1


def test_daily_mart_row_count(connection):
    """Current baseline should contain 73,048 daily rows."""

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM mart_weather_daily
        """
    ).fetchone()[0]

    assert count == 73_048


def test_daily_mart_location_count(connection):
    """Daily mart should contain eight locations."""

    count = connection.execute(
        """
        SELECT COUNT(DISTINCT location_name)
        FROM mart_weather_daily
        """
    ).fetchone()[0]

    assert count == 8


def test_daily_mart_unique_grain(connection):
    """
    Each location/date/source combination should occur once.
    """

    duplicate_groups = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                location_name,
                observation_date,
                source_name,
                COUNT(*) AS n
            FROM mart_weather_daily
            GROUP BY
                location_name,
                observation_date,
                source_name
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    assert duplicate_groups == 0


def test_daily_mart_required_weather_columns(connection):
    """Daily mart should expose all seven weather variables."""

    columns = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'mart_weather_daily'
        """
    ).fetchall()

    column_names = {row[0] for row in columns}

    expected = {
        "t2m",
        "t2m_min",
        "t2m_max",
        "rh2m",
        "prectotcorr",
        "ws2m",
        "allsky_sfc_sw_dwn",
    }

    assert expected.issubset(column_names)


def test_monthly_view_row_count(connection):
    """
    Eight locations across 25 complete years should produce
    2,400 location-year-month records.
    """

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM vw_monthly_climate_summary
        """
    ).fetchone()[0]

    assert count == 2_400


def test_monthly_view_unique_grain(connection):
    """
    Monthly view grain should be unique by
    location/year/month.
    """

    duplicate_groups = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                location_name,
                year,
                month,
                COUNT(*) AS n
            FROM vw_monthly_climate_summary
            GROUP BY
                location_name,
                year,
                month
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    assert duplicate_groups == 0