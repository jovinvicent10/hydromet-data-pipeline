from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# ============================================================
# HydroMet-ETL
# DSAI 6226 - Unit 6
# Data Quality as Code
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "nasa_power_tanzania_daily.csv"
)

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
)


REQUIRED_COLUMNS = [
    "date",
    "location",
    "latitude",
    "longitude",
    "source",
    "T2M",
    "T2M_MIN",
    "T2M_MAX",
    "RH2M",
    "PRECTOTCORR",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
]


METEOROLOGICAL_COLUMNS = [
    "T2M",
    "T2M_MIN",
    "T2M_MAX",
    "RH2M",
    "PRECTOTCORR",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
]


EXPECTED_BASELINE = {
    "rows": 73048,
    "locations": 8,
    "dates": 9131,
    "start_date": "2001-01-01",
    "end_date": "2025-12-31",
    "source": "NASA_POWER",
}


@dataclass
class QualityResult:
    rule_name: str
    category: str
    severity: str
    status: str
    affected_rows: int
    description: str


def sha256_file(path: Path) -> str:
    """
    Calculate SHA-256 fingerprint of a file.
    """
    sha = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha.update(chunk)

    return sha.hexdigest()


def add_result(
    results: list[QualityResult],
    rule_name: str,
    category: str,
    severity: str,
    affected_rows: int,
    description: str,
) -> None:

    status = "PASS" if affected_rows == 0 else (
        "WARNING" if severity == "WARNING" else "FAIL"
    )

    results.append(
        QualityResult(
            rule_name=rule_name,
            category=category,
            severity=severity,
            status=status,
            affected_rows=int(affected_rows),
            description=description,
        )
    )


def check_required_columns(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    add_result(
        results,
        rule_name="required_columns_present",
        category="schema",
        severity="ERROR",
        affected_rows=len(missing_columns),
        description=(
            "All required HydroMet columns must be present. "
            f"Missing columns: {missing_columns}"
        ),
    )


def check_missing_values(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    required_subset = [
        column
        for column in REQUIRED_COLUMNS
        if column in df.columns
    ]

    missing_count = (
        df[required_subset]
        .isna()
        .sum()
        .sum()
    )

    add_result(
        results,
        rule_name="missing_required_values",
        category="completeness",
        severity="ERROR",
        affected_rows=missing_count,
        description=(
            "Required HydroMet fields should not contain "
            "ordinary missing values."
        ),
    )


def check_duplicate_location_date(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    duplicate_count = (
        df.duplicated(
            subset=["location", "date"],
            keep=False,
        ).sum()
    )

    add_result(
        results,
        rule_name="duplicate_location_date",
        category="uniqueness",
        severity="ERROR",
        affected_rows=duplicate_count,
        description=(
            "Each location-date pair must occur only once "
            "in the wide daily dataset."
        ),
    )


def check_coordinates(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    invalid = (
        ~df["latitude"].between(-90, 90)
        | ~df["longitude"].between(-180, 180)
    )

    add_result(
        results,
        rule_name="valid_coordinates",
        category="validity",
        severity="ERROR",
        affected_rows=invalid.sum(),
        description=(
            "Latitude must be between -90 and 90 and "
            "longitude between -180 and 180."
        ),
    )


def check_relative_humidity(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    invalid = ~df["RH2M"].between(0, 100)

    add_result(
        results,
        rule_name="relative_humidity_range",
        category="physical_validity",
        severity="ERROR",
        affected_rows=invalid.sum(),
        description="RH2M must lie between 0 and 100.",
    )


def check_non_negative_variables(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    checks = {
        "PRECTOTCORR": "negative_precipitation",
        "WS2M": "negative_wind_speed",
        "ALLSKY_SFC_SW_DWN": "negative_solar_radiation",
    }

    for column, rule_name in checks.items():

        invalid = df[column] < 0

        add_result(
            results,
            rule_name=rule_name,
            category="physical_validity",
            severity="ERROR",
            affected_rows=invalid.sum(),
            description=f"{column} must not be negative.",
        )


def check_temperature_consistency(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    invalid = (
        (df["T2M_MIN"] > df["T2M"])
        | (df["T2M"] > df["T2M_MAX"])
        | (df["T2M_MIN"] > df["T2M_MAX"])
    )

    add_result(
        results,
        rule_name="temperature_consistency",
        category="consistency",
        severity="ERROR",
        affected_rows=invalid.sum(),
        description=(
            "Temperature fields must satisfy "
            "T2M_MIN <= T2M <= T2M_MAX."
        ),
    )


def check_daily_date_coverage(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    missing_dates = 0

    for _, group in df.groupby("location"):

        dates = pd.DatetimeIndex(group["date"].dropna().unique())

        if len(dates) == 0:
            continue

        expected = pd.date_range(
            dates.min(),
            dates.max(),
            freq="D",
        )

        missing_dates += len(expected.difference(dates))

    add_result(
        results,
        rule_name="daily_date_coverage",
        category="completeness",
        severity="ERROR",
        affected_rows=missing_dates,
        description=(
            "Each location should have continuous daily coverage "
            "between its first and last observation."
        ),
    )


def check_source_consistency(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    unexpected = (
        df["source"]
        .astype(str)
        .ne(EXPECTED_BASELINE["source"])
        .sum()
    )

    add_result(
        results,
        rule_name="source_consistency",
        category="lineage",
        severity="ERROR",
        affected_rows=unexpected,
        description=(
            "Current validated baseline should identify "
            "NASA_POWER as the source."
        ),
    )


def calculate_iqr_flags(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> dict[str, int]:

    iqr_counts: dict[str, int] = {}

    for column in METEOROLOGICAL_COLUMNS:

        series = df[column].dropna()

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        flagged = (
            (df[column] < lower_bound)
            | (df[column] > upper_bound)
        )

        count = int(flagged.sum())

        iqr_counts[column] = count

        results.append(
            QualityResult(
                rule_name=f"iqr_flag_{column}",
                category="statistical_diagnostic",
                severity="WARNING",
                status="PASS" if count == 0 else "WARNING",
                affected_rows=count,
                description=(
                    f"{column} observations outside the "
                    "1.5×IQR diagnostic range. "
                    "These are statistical flags, not "
                    "automatically errors."
                ),
            )
        )

    return iqr_counts


def check_baseline(
    df: pd.DataFrame,
    results: list[QualityResult],
) -> None:

    checks = {
        "baseline_row_count": (
            len(df),
            EXPECTED_BASELINE["rows"],
        ),
        "baseline_location_count": (
            df["location"].nunique(),
            EXPECTED_BASELINE["locations"],
        ),
        "baseline_date_count": (
            df["date"].nunique(),
            EXPECTED_BASELINE["dates"],
        ),
    }

    for rule_name, (actual, expected) in checks.items():

        mismatch = int(actual != expected)

        add_result(
            results,
            rule_name=rule_name,
            category="baseline",
            severity="ERROR",
            affected_rows=mismatch,
            description=(
                f"Expected {expected}; observed {actual}."
            ),
        )

    observed_start = df["date"].min().strftime("%Y-%m-%d")
    observed_end = df["date"].max().strftime("%Y-%m-%d")

    add_result(
        results,
        rule_name="baseline_start_date",
        category="baseline",
        severity="ERROR",
        affected_rows=int(
            observed_start != EXPECTED_BASELINE["start_date"]
        ),
        description=(
            f"Expected start date "
            f"{EXPECTED_BASELINE['start_date']}; "
            f"observed {observed_start}."
        ),
    )

    add_result(
        results,
        rule_name="baseline_end_date",
        category="baseline",
        severity="ERROR",
        affected_rows=int(
            observed_end != EXPECTED_BASELINE["end_date"]
        ),
        description=(
            f"Expected end date "
            f"{EXPECTED_BASELINE['end_date']}; "
            f"observed {observed_end}."
        ),
    )


def validate_hydromet(
    input_path: Path,
    strict_baseline: bool = False,
) -> tuple[dict, pd.DataFrame]:

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {input_path}"
        )

    dataset_sha256 = sha256_file(input_path)

    df = pd.read_csv(input_path)

    if "date" not in df.columns:
        raise ValueError("Required column 'date' is missing.")

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    results: list[QualityResult] = []

    check_required_columns(df, results)

    # Stop early if schema is badly broken.
    missing_required = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_required:
        raise ValueError(
            f"Cannot continue validation. "
            f"Missing columns: {missing_required}"
        )

    check_missing_values(df, results)
    check_duplicate_location_date(df, results)
    check_coordinates(df, results)
    check_relative_humidity(df, results)
    check_non_negative_variables(df, results)
    check_temperature_consistency(df, results)
    check_daily_date_coverage(df, results)
    check_source_consistency(df, results)

    iqr_counts = calculate_iqr_flags(
        df,
        results,
    )

    if strict_baseline:
        check_baseline(
            df,
            results,
        )

    summary_df = pd.DataFrame(
        [asdict(result) for result in results]
    )

    error_failures = summary_df[
        (summary_df["severity"] == "ERROR")
        & (summary_df["status"] == "FAIL")
    ]

    warning_results = summary_df[
        summary_df["status"] == "WARNING"
    ]

    overall_status = (
        "FAIL"
        if not error_failures.empty
        else "PASS"
    )

    report = {
        "pipeline": "HydroMet-ETL",
        "validation_type": "data_quality_as_code",
        "validated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_file": str(
            input_path.relative_to(PROJECT_ROOT)
        )
        if input_path.is_relative_to(PROJECT_ROOT)
        else str(input_path),
        "dataset_sha256": dataset_sha256,
        "overall_status": overall_status,
        "rows": int(len(df)),
        "locations": int(df["location"].nunique()),
        "dates": int(df["date"].nunique()),
        "start_date": (
            df["date"].min().strftime("%Y-%m-%d")
        ),
        "end_date": (
            df["date"].max().strftime("%Y-%m-%d")
        ),
        "source_values": sorted(
            df["source"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
        "error_failures": int(
            len(error_failures)
        ),
        "warning_rules": int(
            len(warning_results)
        ),
        "total_iqr_flags": int(
            sum(iqr_counts.values())
        ),
        "iqr_flags_by_variable": iqr_counts,
        "strict_baseline": strict_baseline,
        "quality_rules": [
            asdict(result)
            for result in results
        ],
    }

    return report, summary_df


def save_outputs(
    report: dict,
    summary_df: pd.DataFrame,
    output_dir: Path,
) -> None:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        output_dir
        / "data_quality_report.json"
    )

    csv_path = (
        output_dir
        / "data_quality_summary.csv"
    )

    json_temp = json_path.with_suffix(
        ".json.tmp"
    )

    csv_temp = csv_path.with_suffix(
        ".csv.tmp"
    )

    with json_temp.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
        )

    summary_df.to_csv(
        csv_temp,
        index=False,
    )

    json_temp.replace(json_path)
    csv_temp.replace(csv_path)

    print()
    print("Quality outputs written:")
    print(f"  {json_path}")
    print(f"  {csv_path}")


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Run HydroMet-ETL data-quality checks."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to HydroMet daily CSV.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for quality reports.",
    )

    parser.add_argument(
        "--strict-baseline",
        action="store_true",
        help=(
            "Validate against the currently "
            "verified 2001-2025 baseline."
        ),
    )

    args = parser.parse_args()

    report, summary_df = validate_hydromet(
        input_path=args.input,
        strict_baseline=args.strict_baseline,
    )

    save_outputs(
        report,
        summary_df,
        args.output_dir,
    )

    print()
    print("=" * 60)
    print("HYDROMET DATA QUALITY RESULT")
    print("=" * 60)

    print(
        f"Overall status : "
        f"{report['overall_status']}"
    )

    print(
        f"Rows           : "
        f"{report['rows']:,}"
    )

    print(
        f"Locations      : "
        f"{report['locations']}"
    )

    print(
        f"Dates          : "
        f"{report['dates']:,}"
    )

    print(
        f"IQR flags      : "
        f"{report['total_iqr_flags']:,}"
    )

    print(
        f"Error failures : "
        f"{report['error_failures']}"
    )

    print(
        f"SHA-256        : "
        f"{report['dataset_sha256']}"
    )

    print("=" * 60)

    if report["overall_status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()