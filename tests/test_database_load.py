from pathlib import Path

import duckdb


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "hydromet.duckdb"
)


EXPECTED_FACT_ROWS = 511_336
EXPECTED_LOCATIONS = 8
EXPECTED_VARIABLES = 7
EXPECTED_DATES = 9131


def connect():

    return duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )


def test_fact_row_count():

    connection = connect()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM fact_observation
        """
    ).fetchone()[0]

    connection.close()

    assert count == EXPECTED_FACT_ROWS


def test_location_count():

    connection = connect()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM dim_location
        """
    ).fetchone()[0]

    connection.close()

    assert count == EXPECTED_LOCATIONS


def test_variable_count():

    connection = connect()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM dim_variable
        """
    ).fetchone()[0]

    connection.close()

    assert count == EXPECTED_VARIABLES


def test_date_count():

    connection = connect()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM dim_date
        """
    ).fetchone()[0]

    connection.close()

    assert count == EXPECTED_DATES


def test_no_duplicate_fact_grain():

    connection = connect()

    duplicates = connection.execute(
        """
        SELECT COUNT(*)

        FROM (

            SELECT
                date_id,
                location_id,
                variable_id,
                source_id,
                COUNT(*) AS n

            FROM fact_observation

            GROUP BY
                date_id,
                location_id,
                variable_id,
                source_id

            HAVING COUNT(*) > 1

        )
        """
    ).fetchone()[0]

    connection.close()

    assert duplicates == 0