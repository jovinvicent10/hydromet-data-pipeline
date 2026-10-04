# Reproduce isolated lab evidence with the existing PostgreSQL installation.
# Requires the established cached data and existing Python virtual environment.
$ErrorActionPreference = 'Stop'
$labRepo = Split-Path -Parent $PSScriptRoot
$labCluster = Join-Path $labRepo 'data\processed\lab_evidence\postgres_cluster'
$labPgBin = 'C:\Program Files\PostgreSQL\18\bin'
$labPython = Join-Path $labRepo '.venv\Scripts\python.exe'
Push-Location $labRepo
try {
    if (-not (Test-Path -LiteralPath (Join-Path $labCluster 'PG_VERSION'))) {
        & (Join-Path $labPgBin 'initdb.exe') -D $labCluster -U hydromet_lab --auth=trust --no-locale -E UTF8
        if ($LASTEXITCODE -ne 0) { throw 'Lab cluster initialization failed' }
    }
    & (Join-Path $labPgBin 'pg_isready.exe') -h 127.0.0.1 -p 55433
    if ($LASTEXITCODE -ne 0) {
        # Do not use Start-Process -Wait: Windows can wait for the server child.
        $labStartArgs = @('-D', ('"' + $labCluster + '"'), '-l', ('"' + (Join-Path $labCluster 'server.log') + '"'), '-o', '"-h 127.0.0.1 -p 55433"', '-w', 'start')
        Start-Process -FilePath (Join-Path $labPgBin 'pg_ctl.exe') -ArgumentList $labStartArgs -WindowStyle Hidden
        for ($labAttempt = 0; $labAttempt -lt 30; $labAttempt++) {
            Start-Sleep -Milliseconds 500
            & (Join-Path $labPgBin 'pg_isready.exe') -h 127.0.0.1 -p 55433
            if ($LASTEXITCODE -eq 0) { break }
        }
        if ($LASTEXITCODE -ne 0) { throw 'Lab server did not become ready' }
    }
    & $labPython -m src.labs.complete_labs --section all
    if ($LASTEXITCODE -ne 0) { throw 'Lab evidence run failed; inspect outputs/evidence and local logs' }
}
finally {
    # Stop only the specifically named temporary cluster, never the service.
    if (Test-Path -LiteralPath (Join-Path $labCluster 'postmaster.pid')) {
        & (Join-Path $labPgBin 'pg_ctl.exe') -D $labCluster -w stop -m fast
    }
    Pop-Location
}
