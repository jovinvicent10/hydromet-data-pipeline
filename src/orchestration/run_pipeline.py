"""
HydroMet-ETL
Week 11 — Pipeline Orchestration and Handover

Main Pipeline Orchestrator

Purpose
-------
Coordinate the major HydroMet-ETL stages in a defined order,
record execution status and duration, and stop safely if a
required stage fails.

Pipeline
--------
1. Ingestion
2. Data-quality validation
3. Database schema creation
4. Database loading
5. Analytics serving layer
6. ML data preparation
7. Consumer dashboard
8. Regression verification

Design principles
-----------------
- Reuse existing pipeline modules rather than duplicate logic.
- Stop downstream execution when a required stage fails.
- Capture stage duration and status.
- Produce machine-readable execution metadata.
- Support selective execution for development and handover.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "orchestration"
LOG_DIR = PROJECT_ROOT / "logs" / "orchestration"

RUN_SUMMARY_PATH = OUTPUT_DIR / "pipeline_run_summary.json"


# ============================================================
# Pipeline definition
# ============================================================

PIPELINE_STAGES = [
    {
        "name": "ingestion",
        "description": "Acquire and assemble NASA POWER data",
        "command": [
            sys.executable,
            "-m",
            "src.ingestion.ingest_nasa_power",
        ],
    },
    {
        "name": "data_quality",
        "description": "Validate governed HydroMet dataset",
        "command": [
            sys.executable,
            "-m",
            "src.quality.validate_hydromet",
            "--strict-baseline",
        ],
    },
    {
        "name": "database_schema",
        "description": "Create DuckDB analytical schema",
        "command": [
            sys.executable,
            "-m",
            "src.database.create_database",
        ],
    },
    {
        "name": "database_load",
        "description": "Load dimensional analytical model",
        "command": [
            sys.executable,
            "-m",
            "src.database.load_duckdb",
        ],
    },
    {
        "name": "serving_layer",
        "description": "Create analytical serving layer",
        "command": [
            sys.executable,
            "-m",
            "src.serving.create_serving_layer",
        ],
    },
    {
        "name": "ml_preparation",
        "description": "Generate leakage-aware ML-ready data",
        "command": [
            sys.executable,
            "-m",
            "src.ml.prepare_ml_data",
        ],
    },
    {
        "name": "consumer_dashboard",
        "description": "Query curated monthly output and render freshness-aware dashboard",
        "command": [sys.executable, "-m", "src.serving.build_dashboard"],
    },
    {
        "name": "regression_tests",
        "description": "Run complete automated test suite",
        "command": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
    },
]


# ============================================================
# Utility functions
# ============================================================

def utc_now():
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def ensure_directories():
    """Create orchestration output directories."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def safe_write_json(path: Path, payload: dict):
    """
    Write JSON using a temporary file followed by replacement.
    """

    temp_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with open(
        temp_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=4,
        )

    temp_path.replace(path)


# ============================================================
# Stage execution
# ============================================================

def run_stage(stage):
    """
    Execute one pipeline stage.

    Returns a dictionary containing execution metadata.
    """

    stage_name = stage["name"]

    print("\n" + "=" * 70)
    print(
        f"STAGE: {stage_name}"
    )
    print(
        stage["description"]
    )
    print("=" * 70)

    started_at = utc_now()

    start = time.perf_counter()

    process = subprocess.run(
        stage["command"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    duration = (
        time.perf_counter()
        - start
    )

    finished_at = utc_now()

    log_path = (
        LOG_DIR
        / f"{stage_name}.log"
    )

    with open(
        log_path,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            f"Stage: {stage_name}\n"
        )

        file.write(
            f"Started: {started_at}\n"
        )

        file.write(
            f"Finished: {finished_at}\n"
        )

        file.write(
            f"Return code: {process.returncode}\n"
        )

        file.write(
            f"Duration seconds: {duration:.6f}\n"
        )

        file.write(
            "\n===== STDOUT =====\n"
        )

        file.write(
            process.stdout or ""
        )

        file.write(
            "\n===== STDERR =====\n"
        )

        file.write(
            process.stderr or ""
        )

    # Also show subprocess output in terminal.
    if process.stdout:
        print(process.stdout)

    if process.stderr:
        print(
            process.stderr,
            file=sys.stderr,
        )

    status = (
        "SUCCESS"
        if process.returncode == 0
        else "FAILED"
    )

    result = {
        "stage": stage_name,
        "description": stage["description"],
        "status": status,
        "return_code": process.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(
            duration,
            6,
        ),
        "log_file": str(
            log_path.relative_to(
                PROJECT_ROOT
            )
        ),
    }

    if status == "SUCCESS":

        print(
            f"[SUCCESS] {stage_name} "
            f"completed in {duration:.2f} seconds."
        )

    else:

        print(
            f"[FAILED] {stage_name} "
            f"returned code {process.returncode}."
        )

    return result


# ============================================================
# Pipeline execution
# ============================================================

def execute_pipeline(
    skip_ingestion=False,
    skip_tests=False,
):
    """
    Execute pipeline stages sequentially.

    A failed stage prevents downstream stages from running.
    """

    ensure_directories()

    pipeline_started_at = utc_now()
    pipeline_start = time.perf_counter()

    selected_stages = []

    for stage in PIPELINE_STAGES:

        if (
            skip_ingestion
            and stage["name"] == "ingestion"
        ):
            continue

        if (
            skip_tests
            and stage["name"] == "regression_tests"
        ):
            continue

        selected_stages.append(stage)

    run_summary = {
        "pipeline": "HydroMet-ETL",
        "stage": (
            "Week 11 - Orchestration and Handover"
        ),
        "pipeline_started_at": (
            pipeline_started_at
        ),
        "pipeline_finished_at": None,
        "duration_seconds": None,
        "status": "RUNNING",
        "skip_ingestion": skip_ingestion,
        "skip_tests": skip_tests,
        "stages": [],
    }

    # Write initial RUNNING state.
    safe_write_json(
        RUN_SUMMARY_PATH,
        run_summary,
    )

    for stage in selected_stages:

        result = run_stage(stage)

        run_summary["stages"].append(
            result
        )

        # Persist progress after every stage.
        safe_write_json(
            RUN_SUMMARY_PATH,
            run_summary,
        )

        if result["status"] != "SUCCESS":

            pipeline_duration = (
                time.perf_counter()
                - pipeline_start
            )

            run_summary[
                "pipeline_finished_at"
            ] = utc_now()

            run_summary[
                "duration_seconds"
            ] = round(
                pipeline_duration,
                6,
            )

            run_summary[
                "status"
            ] = "FAILED"

            run_summary[
                "failed_stage"
            ] = result["stage"]

            safe_write_json(
                RUN_SUMMARY_PATH,
                run_summary,
            )

            print("\n" + "=" * 70)
            print("PIPELINE FAILED")
            print("=" * 70)

            print(
                "Failed stage:",
                result["stage"],
            )

            print(
                "Downstream stages were not executed."
            )

            print(
                "Inspect log:",
                result["log_file"],
            )

            return 1

    pipeline_duration = (
        time.perf_counter()
        - pipeline_start
    )

    run_summary[
        "pipeline_finished_at"
    ] = utc_now()

    run_summary[
        "duration_seconds"
    ] = round(
        pipeline_duration,
        6,
    )

    run_summary[
        "status"
    ] = "SUCCESS"

    safe_write_json(
        RUN_SUMMARY_PATH,
        run_summary,
    )

    print("\n" + "=" * 70)
    print("HYDROMET-ETL PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"Status: SUCCESS"
    )

    print(
        f"Stages executed: "
        f"{len(run_summary['stages'])}"
    )

    print(
        f"Total duration: "
        f"{pipeline_duration:.2f} seconds"
    )

    print(
        f"Run summary: "
        f"{RUN_SUMMARY_PATH}"
    )

    return 0


# ============================================================
# CLI
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Run the HydroMet-ETL pipeline."
        )
    )

    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help=(
            "Skip NASA POWER ingestion and use "
            "the existing validated dataset."
        ),
    )

    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help=(
            "Skip the final regression-test stage."
        ),
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    print("=" * 70)
    print("HydroMet-ETL Pipeline Orchestrator")
    print("=" * 70)

    print(
        f"Project root: {PROJECT_ROOT}"
    )

    print(
        f"Skip ingestion: "
        f"{args.skip_ingestion}"
    )

    print(
        f"Skip tests: "
        f"{args.skip_tests}"
    )

    return execute_pipeline(
        skip_ingestion=args.skip_ingestion,
        skip_tests=args.skip_tests,
    )


if __name__ == "__main__":
    raise SystemExit(main())
