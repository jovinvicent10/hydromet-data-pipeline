from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml


# ---------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """
    Load project configuration from YAML.
    """
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def nasa_date(date_string: str) -> str:
    """
    Convert YYYY-MM-DD to YYYYMMDD required by NASA POWER.
    """
    return date_string.replace("-", "")


def ensure_directory(path: Path) -> None:
    """
    Create directory if it does not exist.
    """
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# NASA POWER request
# ---------------------------------------------------------

def fetch_nasa_power(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: list[str],
    community: str = "AG",
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Download daily NASA POWER data for a point location.
    """

    config = load_config()

    base_url = config["nasa_power"]["base_url"]

    request_params = {
        "parameters": ",".join(parameters),
        "community": community,
        "longitude": longitude,
        "latitude": latitude,
        "start": nasa_date(start_date),
        "end": nasa_date(end_date),
        "format": "JSON",
    }

    logger.info(
        "Requesting NASA POWER data for latitude=%s longitude=%s",
        latitude,
        longitude,
    )

    response = requests.get(
        base_url,
        params=request_params,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# Save raw JSON
# ---------------------------------------------------------

def save_raw_json(
    data: dict[str, Any],
    location_name: str,
    start_date: str,
    end_date: str,
    raw_directory: Path,
) -> Path:
    """
    Save untouched NASA POWER response.
    """

    ensure_directory(raw_directory)

    safe_location = location_name.lower().replace(" ", "_")

    filename = (
        f"nasa_power_{safe_location}_"
        f"{start_date}_{end_date}.json"
    )

    output_path = raw_directory / filename

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    logger.info("Raw response saved to %s", output_path)

    return output_path


# ---------------------------------------------------------
# Convert NASA response to dataframe
# ---------------------------------------------------------

def response_to_dataframe(
    response: dict[str, Any],
    location_name: str,
    latitude: float,
    longitude: float,
) -> pd.DataFrame:
    """
    Transform NASA POWER JSON response into tidy tabular form.
    """

    parameter_data = response["properties"]["parameter"]

    frames = []

    for parameter_name, observations in parameter_data.items():

        series = pd.Series(
            observations,
            name=parameter_name,
        )

        frames.append(series)

    dataframe = pd.concat(frames, axis=1)

    dataframe.index.name = "date"

    dataframe = dataframe.reset_index()

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        format="%Y%m%d",
        errors="coerce",
    )

    dataframe.insert(1, "location", location_name)
    dataframe.insert(2, "latitude", latitude)
    dataframe.insert(3, "longitude", longitude)
    dataframe["source"] = "NASA_POWER"

    return dataframe


# ---------------------------------------------------------
# Download one location
# ---------------------------------------------------------

def download_location(
    location: dict[str, Any],
    config: dict[str, Any],
) -> pd.DataFrame:
    """
    Download NASA POWER data for a single configured location.
    """

    location_name = location["name"]
    latitude = location["latitude"]
    longitude = location["longitude"]

    start_date = config["data"]["start_date"]
    end_date = config["data"]["end_date"]

    parameters = config["nasa_power"]["parameters"]
    community = config["nasa_power"]["community"]

    raw_directory = PROJECT_ROOT / config["paths"]["raw"]

    response = fetch_nasa_power(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        parameters=parameters,
        community=community,
    )

    save_raw_json(
        data=response,
        location_name=location_name,
        start_date=start_date,
        end_date=end_date,
        raw_directory=raw_directory,
    )

    dataframe = response_to_dataframe(
        response=response,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
    )

    logger.info(
        "%s: downloaded %s observations",
        location_name,
        len(dataframe),
    )

    return dataframe


# ---------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------

def main() -> None:

    config = load_config()

    all_frames = []

    for location in config["locations"]:

        try:

            dataframe = download_location(
                location=location,
                config=config,
            )

            all_frames.append(dataframe)

            # Avoid rapidly repeating API calls
            time.sleep(1)

        except requests.RequestException as exc:

            logger.exception(
                "NASA POWER request failed for %s: %s",
                location["name"],
                exc,
            )

    if not all_frames:

        raise RuntimeError(
            "No NASA POWER data was successfully downloaded."
        )

    combined = pd.concat(
        all_frames,
        ignore_index=True,
    )

    interim_directory = (
        PROJECT_ROOT /
        config["paths"]["interim"]
    )

    ensure_directory(interim_directory)

    output_file = interim_directory / "nasa_power_tanzania_daily.csv"

    combined.to_csv(
        output_file,
        index=False,
    )

    logger.info(
        "Combined dataset saved to %s",
        output_file,
    )

    logger.info(
        "Dataset shape: %s rows x %s columns",
        combined.shape[0],
        combined.shape[1],
    )


if __name__ == "__main__":
    main()