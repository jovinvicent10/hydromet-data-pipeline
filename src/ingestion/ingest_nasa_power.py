from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


# ============================================================
# Project configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "nasa_power"
)

INTERIM_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
)

METADATA_DIR = (
    PROJECT_ROOT
    / "metadata"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
    / "ingestion"
)

MANIFEST_PATH = (
    METADATA_DIR
    / "ingestion_manifest.json"
)

INTERIM_PATH = (
    INTERIM_DIR
    / "nasa_power_tanzania_daily.csv"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "reports"
)

RUN_SUMMARY_PATH = (
    REPORT_DIR
    / "ingestion_run_summary.json"
)


# ============================================================
# NASA POWER configuration
# ============================================================

BASE_URL = (
    "https://power.larc.nasa.gov/"
    "api/temporal/daily/point"
)

START_DATE = "20010101"
END_DATE = "20251231"

PARAMETERS = [
    "T2M",
    "T2M_MIN",
    "T2M_MAX",
    "RH2M",
    "PRECTOTCORR",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
]


LOCATIONS = {
    "Arusha": (-3.3869, 36.6830),
    "Dar_es_Salaam": (-6.7924, 39.2083),
    "Dodoma": (-6.1630, 35.7516),
    "Mbeya": (-8.9094, 33.4608),
    "Morogoro": (-6.8235, 37.6612),
    "Mwanza": (-2.5164, 32.9175),
    "Songea": (-10.6833, 35.6500),
    "Tabora": (-5.0162, 32.8266),
}


# ============================================================
# Directory setup
# ============================================================

def ensure_directories() -> None:

    for directory in [
        RAW_DIR,
        INTERIM_DIR,
        METADATA_DIR,
        LOG_DIR,
        REPORT_DIR,
    ]:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


# ============================================================
# Logging
# ============================================================

def configure_logging() -> None:

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    log_file = (
        LOG_DIR
        / f"ingestion_{timestamp}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


# ============================================================
# Hash utilities
# ============================================================

def sha256_file(
    path: Path,
) -> str:

    sha256 = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(8192),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def build_request_id(
    location: str,
    latitude: float,
    longitude: float,
) -> str:

    payload = {
        "source": "NASA_POWER",
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "start": START_DATE,
        "end": END_DATE,
        "parameters": sorted(PARAMETERS),
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# Manifest
# ============================================================

def load_manifest() -> dict[str, Any]:

    if not MANIFEST_PATH.exists():

        return {
            "source": "NASA_POWER",
            "requests": {},
        }

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        manifest = json.load(file)

    # Backward compatibility for older manifest structures.
    manifest.setdefault(
        "source",
        "NASA_POWER",
    )

    manifest.setdefault(
        "requests",
        {},
    )

    return manifest

def save_manifest(
    manifest: dict[str, Any],
) -> None:

    temporary_path = (
        MANIFEST_PATH
        .with_suffix(".tmp")
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4,
        )

    temporary_path.replace(
        MANIFEST_PATH
    )


# ============================================================
# API request
# ============================================================

def fetch_nasa_power(
    latitude: float,
    longitude: float,
    max_attempts: int = 3,
) -> dict:

    params = {
        "parameters":
            ",".join(PARAMETERS),

        "community":
            "AG",

        "longitude":
            longitude,

        "latitude":
            latitude,

        "start":
            START_DATE,

        "end":
            END_DATE,

        "format":
            "JSON",
    }

    last_error = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        try:

            logging.info(
                "NASA POWER request "
                "attempt %s/%s",
                attempt,
                max_attempts,
            )

            response = requests.get(
                BASE_URL,
                params=params,
                timeout=120,
            )

            response.raise_for_status()

            return response.json()

        except (
            requests.RequestException,
            ValueError,
        ) as error:

            last_error = error

            logging.warning(
                "Request failed: %s",
                error,
            )

            if attempt < max_attempts:

                wait_seconds = (
                    2 ** (attempt - 1)
                )

                logging.info(
                    "Retrying in %s seconds...",
                    wait_seconds,
                )

                time.sleep(
                    wait_seconds
                )

    raise RuntimeError(
        "NASA POWER request failed "
        f"after {max_attempts} attempts."
    ) from last_error


# ============================================================
# Raw-data validation
# ============================================================

def validate_payload(
    payload: dict,
) -> None:

    if "properties" not in payload:

        raise ValueError(
            "NASA POWER response "
            "does not contain properties."
        )

    parameter_data = (
        payload
        .get("properties", {})
        .get("parameter", {})
    )

    missing_parameters = [
        parameter
        for parameter in PARAMETERS
        if parameter
        not in parameter_data
    ]

    if missing_parameters:

        raise ValueError(
            "NASA POWER response "
            "is missing parameters: "
            f"{missing_parameters}"
        )


# ============================================================
# Raw persistence
# ============================================================

def save_raw_payload(
    payload: dict,
    location: str,
    request_id: str,
) -> Path:

    filename = (
        f"{location.lower()}_"
        f"{START_DATE}_{END_DATE}_"
        f"{request_id}.json"
    )

    path = (
        RAW_DIR
        / filename
    )

    temporary_path = (
        path.with_suffix(".tmp")
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
        )

    temporary_path.replace(path)

    return path


# ============================================================
# Transformation
# ============================================================

def payload_to_dataframe(
    payload: dict,
    location: str,
    latitude: float,
    longitude: float,
) -> pd.DataFrame:

    parameter_data = (
        payload["properties"]["parameter"]
    )

    dates = sorted(
        parameter_data["T2M"].keys()
    )

    records = []

    for date_string in dates:

        record = {
            "date":
                pd.to_datetime(
                    date_string,
                    format="%Y%m%d",
                ),

            "location":
                location,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "source":
                "NASA_POWER",
        }

        for parameter in PARAMETERS:

            record[parameter] = (
                parameter_data[
                    parameter
                ].get(date_string)
            )

        records.append(record)

    return pd.DataFrame(records)


# ============================================================
# Interim-data validation
# ============================================================

def validate_dataframe(
    df: pd.DataFrame,
) -> None:

    required_columns = {
        "date",
        "location",
        "latitude",
        "longitude",
        "source",
        *PARAMETERS,
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Transformed dataset is "
            "missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if df.empty:

        raise ValueError(
            "Transformed dataset is empty."
        )

    duplicates = (
        df.duplicated(
            ["location", "date"]
        ).sum()
    )

    if duplicates > 0:

        raise ValueError(
            f"Detected {duplicates} "
            "duplicate location-date rows."
        )


# ============================================================
# Safe interim write
# ============================================================

def save_interim(
    df: pd.DataFrame,
) -> None:

    df = (
        df
        .sort_values(
            ["location", "date"]
        )
        .reset_index(drop=True)
    )

    temporary_path = (
        INTERIM_PATH
        .with_suffix(".tmp")
    )

    df.to_csv(
        temporary_path,
        index=False,
    )

    temporary_path.replace(
        INTERIM_PATH
    )


# ============================================================
# Main ingestion
# ============================================================

def main() -> None:

    ensure_directories()
    configure_logging()

    logging.info(
        "Starting NASA POWER ingestion."
    )

    manifest = load_manifest()

    manifest["pipeline"] = {
        "name": "HydroMet-ETL",
        "source": "NASA_POWER",
        "temporal_resolution": "daily",
        "start_date": START_DATE,
        "end_date": END_DATE,
        "parameter_count": len(PARAMETERS),
        "location_count": len(LOCATIONS),
    }

    all_frames = []

    for (
        location,
        coordinates,
    ) in LOCATIONS.items():

        latitude, longitude = coordinates

        request_id = build_request_id(
            location,
            latitude,
            longitude,
        )

        logging.info(
            "Processing %s "
            "(request_id=%s)",
            location,
            request_id,
        )

        existing_entry = (
            manifest["requests"]
            .get(request_id)
        )

        raw_path = None
        payload = None

        # --------------------------------------------
        # Reuse existing immutable raw file
        # --------------------------------------------

        if (
            existing_entry
            and existing_entry.get(
                "status"
            ) == "success"
        ):

            raw_file_value = (
                existing_entry.get(
                    "raw_file"
                )
            )

            if raw_file_value:

                stored_path = Path(
                    raw_file_value
                )

                # New manifests use project-relative paths.
                # Older manifests may still contain absolute paths.
                if stored_path.is_absolute():

                    raw_path = stored_path

                else:

                    raw_path = (
                        PROJECT_ROOT
                        / stored_path
                    )

            if (
                raw_path is not None
                and raw_path.exists()
            ):

                current_checksum = (
                    sha256_file(
                        raw_path
                    )
                )

                expected_checksum = (
                    existing_entry.get(
                        "sha256"
                    )
                )

                if (
                    expected_checksum
                    and current_checksum
                    != expected_checksum
                ):

                    raise RuntimeError(
                        "Checksum mismatch for "
                        f"{raw_path}"
                    )

                logging.info(
                    "Existing validated raw "
                    "file found. Skipping API."
                )

                with raw_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    payload = json.load(file)

            else:

                logging.warning(
                    "Manifest references a "
                    "missing raw file. "
                    "Downloading again."
                )

        # --------------------------------------------
        # Download if no reusable raw payload exists
        # --------------------------------------------

        if payload is None:

            payload = fetch_nasa_power(
                latitude,
                longitude,
            )

            validate_payload(
                payload
            )

            raw_path = (
                save_raw_payload(
                    payload,
                    location,
                    request_id,
                )
            )

        # Validate cached and newly downloaded payloads.
        validate_payload(
            payload
        )

        if raw_path is None:

            raise RuntimeError(
                "Raw file path could not be "
                f"resolved for {location}."
            )

        checksum = sha256_file(
            raw_path
        )

        location_df = (
            payload_to_dataframe(
                payload,
                location,
                latitude,
                longitude,
            )
        )

        all_frames.append(
            location_df
        )

        manifest["requests"][
            request_id
        ] = {
            "location":
                location,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "start_date":
                START_DATE,

            "end_date":
                END_DATE,

            "parameters":
                PARAMETERS,

            "raw_file":
                str(
                    raw_path.relative_to(
                        PROJECT_ROOT
                    )
                ),

            "sha256":
                checksum,

            "status":
                "success",

            "last_verified_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        # Preserve partial progress after each location.
        save_manifest(
            manifest
        )

    final_df = pd.concat(
        all_frames,
        ignore_index=True,
    )

    validate_dataframe(
        final_df
    )

    # Write the final deterministic interim dataset first.
    save_interim(
        final_df
    )

    # --------------------------------------------
    # Dataset-level provenance metadata
    # --------------------------------------------

    manifest["dataset"] = {
        "rows":
            int(len(final_df)),

        "locations":
            int(
                final_df[
                    "location"
                ].nunique()
            ),

        "start_date":
            final_df[
                "date"
            ].min().strftime(
                "%Y-%m-%d"
            ),

        "end_date":
            final_df[
                "date"
            ].max().strftime(
                "%Y-%m-%d"
            ),

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "interim_file":
            str(
                INTERIM_PATH.relative_to(
                    PROJECT_ROOT
                )
            ),

        "sha256":
            sha256_file(
                INTERIM_PATH
            ),
    }

    save_manifest(
        manifest
    )

    # --------------------------------------------
    # Run-level summary
    # --------------------------------------------

    run_summary = {
        "pipeline":
            "HydroMet-ETL",

        "source":
            "NASA_POWER",

        "status":
            "success",

        "rows":
            int(len(final_df)),

        "locations":
            int(
                final_df[
                    "location"
                ].nunique()
            ),

        "start_date":
            final_df[
                "date"
            ].min().strftime(
                "%Y-%m-%d"
            ),

        "end_date":
            final_df[
                "date"
            ].max().strftime(
                "%Y-%m-%d"
            ),

        "output_file":
            str(
                INTERIM_PATH.relative_to(
                    PROJECT_ROOT
                )
            ),

        "output_sha256":
            sha256_file(
                INTERIM_PATH
            ),

        "completed_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    temporary_summary_path = (
        RUN_SUMMARY_PATH
        .with_suffix(".tmp")
    )

    with temporary_summary_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            run_summary,
            file,
            indent=4,
        )

    temporary_summary_path.replace(
        RUN_SUMMARY_PATH
    )

    logging.info(
        "Final interim dataset "
        "contains %s rows.",
        f"{len(final_df):,}",
    )

    logging.info(
        "Ingestion run summary "
        "saved to %s",
        RUN_SUMMARY_PATH,
    )

    logging.info(
        "NASA POWER ingestion "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
