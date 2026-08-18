from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT /
    "data" /
    "database" /
    "hydromet.duckdb"
)


EXPECTED_TABLES = {
    "dim_date",
    "dim_location",
    "dim_variable",
    "dim_source",
    "fact_observation",
    "fact_quality_flag",
}


def test_database_exists():

    assert DATABASE_PATH.exists()


def test_expected_tables_exist():

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    tables = connection.execute(
        "SHOW TABLES"
    ).fetchdf()

    actual_tables = set(
        tables["name"].tolist()
    )

    connection.close()

    assert EXPECTED_TABLES.issubset(
        actual_tables
    )