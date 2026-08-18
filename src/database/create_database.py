from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIR = PROJECT_ROOT / "data" / "database"

DATABASE_PATH = (
    DATABASE_DIR /
    "hydromet.duckdb"
)

SCHEMA_PATH = (
    PROJECT_ROOT /
    "sql" /
    "01_create_schema.sql"
)


def create_database():

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        f"Creating database: "
        f"{DATABASE_PATH}"
    )

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        schema_sql = file.read()

    connection.execute(
        schema_sql
    )

    print(
        "Database schema created successfully."
    )

    tables = connection.execute(
        """
        SHOW TABLES
        """
    ).fetchdf()

    print("\nCreated tables:")
    print(tables)

    connection.close()


if __name__ == "__main__":

    create_database()