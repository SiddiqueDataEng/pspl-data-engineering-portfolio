#Requires -Version 5.1
<#
.SYNOPSIS
  Installs Apache Airflow into the project .venv using official constraint files.

.DESCRIPTION
  Run from the repository root after .\setup.ps1 so .venv exists.
  Uses constraints-2.10.4 matching your venv Python minor version (3.10-3.12).

  On Windows, Airflow is installed for DAG validation only; run the scheduler/UI via Docker:
    .\scripts\run-airflow-with-setup.ps1

.EXAMPLE
  .\scripts\install-airflow.ps1
#>
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_airflow-preflight.ps1"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Error "Missing $VenvPython. Run .\setup.ps1 first."
    exit 1
}

$minorPair = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$constraintUrl = "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-$minorPair.txt"
Write-Host "Installing apache-airflow==2.10.4 with constraints for Python $minorPair" -ForegroundColor Cyan
Write-Host "Constraint URL: $constraintUrl" -ForegroundColor DarkGray

& $VenvPython -m pip install "apache-airflow==2.10.4" --constraint $constraintUrl
if ($LASTEXITCODE -ne 0) {
    Write-Error "Airflow install failed. If you see dependency conflicts, use a dedicated venv for Airflow or upgrade conflicting pins in requirements.txt."
    exit $LASTEXITCODE
}

Write-Host "Reconciling packages shared with Jupyter/dbt (typing-extensions, psutil) ..." -ForegroundColor DarkGray
& $VenvPython -m pip install "typing_extensions>=4.14.1" "psutil>=7"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Post-install pip reconcile failed; run .\scripts\check-airflow.ps1"
}

Write-Host ""
Write-Host "Airflow CLI installed in .venv." -ForegroundColor Green
if (Test-IsNativeWindows) {
    Write-Host "On Windows, start the scheduler + UI with Docker or WSL:" -ForegroundColor Yellow
    Write-Host "  .\scripts\run-airflow-with-setup.ps1 -Mode Docker" -ForegroundColor White
    Write-Host "  .\scripts\run-airflow-with-setup.ps1 -Mode Wsl" -ForegroundColor White
    Write-Host "  .\scripts\check-airflow.ps1" -ForegroundColor DarkGray
} else {
    Write-Host "Start with: .\scripts\run-airflow-with-setup.ps1 -Native" -ForegroundColor Green
}
