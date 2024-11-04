#Requires -Version 5.1
<#
.SYNOPSIS
  Runs local Airflow via `airflow standalone` (Linux/macOS/WSL only).

.DESCRIPTION
  On native Windows this mode is NOT supported by Apache Airflow; use
  .\scripts\run-airflow-with-setup.ps1 (Docker) or .\scripts\run-airflow-docker.ps1.

  Sets AIRFLOW_HOME, DAG folder, disables example DAGs and latest-log symlinks.

.EXAMPLE
  .\scripts\airflow-standalone.ps1
#>
[CmdletBinding()]
param(
    [switch] $ForceNativeWindows
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_airflow-preflight.ps1"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Test-IsNativeWindows) {
    if (-not $ForceNativeWindows) {
        Write-AirflowWindowsNotSupportedMessage
        Write-Error "Refusing to run airflow standalone on native Windows. Use .\scripts\run-airflow-docker.ps1 or pass -ForceNativeWindows to attempt anyway."
        exit 1
    }
    Write-Warning "ForceNativeWindows: proceeding despite unsupported platform."
}

$VenvAirflow = Join-Path $Root ".venv\Scripts\airflow.exe"
if (-not (Test-Path -LiteralPath $VenvAirflow)) {
    Write-Error "airflow.exe not found. Run: .\scripts\install-airflow.ps1"
    exit 1
}

$AirflowHome = Join-Path $Root "airflow\airflow_home"
$DagsFolder = Join-Path $Root "airflow\dags"
New-Item -ItemType Directory -Path $AirflowHome -Force | Out-Null

Set-AirflowWindowsSafeEnv -AirflowHome $AirflowHome -DagsFolder $DagsFolder -RepoRoot $Root

Write-Host "AIRFLOW_HOME=$AirflowHome" -ForegroundColor DarkGray
Write-Host "DAGs: $DagsFolder" -ForegroundColor DarkGray
Write-Host "Starting Airflow standalone (Ctrl+C to stop)..." -ForegroundColor Cyan

try {
    & $VenvAirflow standalone
    exit $LASTEXITCODE
} catch {
    if (Test-IsNativeWindows) {
        Write-AirflowWindowsNotSupportedMessage -FailureDetail $_.Exception.Message
    }
    throw
}
