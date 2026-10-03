# ============================================================
# HydroMet-ETL
# Week 11 — Scheduled Pipeline Launcher
# ============================================================
#
# Purpose:
# Run the HydroMet-ETL orchestrator using the project's
# virtual environment.
#
# This script can be called manually or by Windows
# Task Scheduler.
# ============================================================

$ErrorActionPreference = "Stop"

# Determine repository root from this script's location.
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Virtual-environment Python interpreter.
$PythonExe = Join-Path `
    $ProjectRoot `
    ".venv\Scripts\python.exe"

Write-Host "=============================================="
Write-Host "HydroMet-ETL Scheduled Pipeline Launcher"
Write-Host "=============================================="

Write-Host "Project root:"
Write-Host $ProjectRoot

Write-Host ""

# ------------------------------------------------------------
# Validate Python environment
# ------------------------------------------------------------

if (-not (Test-Path $PythonExe)) {

    Write-Error `
        "Virtual-environment Python not found: $PythonExe"

    exit 1
}

# ------------------------------------------------------------
# Move to repository root
# ------------------------------------------------------------

Set-Location $ProjectRoot

Write-Host "Python:"
Write-Host $PythonExe

Write-Host ""
Write-Host "Starting HydroMet-ETL..."
Write-Host ""

# ------------------------------------------------------------
# Execute orchestrator
# ------------------------------------------------------------

& $PythonExe `
    -m `
    src.orchestration.run_pipeline

$ExitCode = $LASTEXITCODE

Write-Host ""

if ($ExitCode -eq 0) {

    Write-Host "HydroMet-ETL completed successfully."

}
else {

    Write-Error `
        "HydroMet-ETL failed with exit code $ExitCode"
}

exit $ExitCode