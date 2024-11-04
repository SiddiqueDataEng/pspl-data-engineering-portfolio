#Requires -Version 5.1
<#
.SYNOPSIS
  Launches the Streamlit KPI dashboard (reads pspl.duckdb at repo root).

.DESCRIPTION
  From repository root (no need to Activate.ps1 if execution policy blocks it):
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\run-dashboard.ps1

  Uses .venv\Scripts\python.exe -m streamlit so the venv is picked up reliably.

  Requires dbt run (after ingest + Silver notebook) so marts exist.
#>
$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# Avoid first-run "enter your email" prompt blocking non-interactive terminals / CI.
$env:CI = "true"
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Missing .venv. From repo root run: .\setup.ps1 -Force -Python 'py -3.11'"
    exit 1
}

$app = Join-Path $Root "dashboard\streamlit_app.py"
if (-not (Test-Path -LiteralPath $app)) {
    Write-Error "Missing Streamlit app at $app"
    exit 1
}
# --server.headless avoids opening a browser when no display; blank stdin skips any stray prompts.
$null | & $python -m streamlit run $app --server.headless true
