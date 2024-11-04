#Requires -Version 5.1
<#
.SYNOPSIS
  Deletes generated artifacts so you can re-run the pipeline from a clean state.

.DESCRIPTION
  Cross-platform logic lives in scripts/reset_project.py (also used by Airflow).

  Scopes:
    Full              - data_large, delta_lake, DuckDB, dbt target+packages+logs, spark scratch,
                        executed notebooks, sample chart PNGs, Streamlit caches
    Datagenerator     - clears data_large/ only
    MedallionFull     - entire delta_lake + .spark_scratch + executed notebook + sample PNGs
    MedallionBronze   - delta_lake/bronze only
    MedallionSilver   - delta_lake/silver + sample PNGs
    MedallionGold     - pspl.duckdb + dbt target + dbt logs (marts / gold layer)
    DbtSql            - dbt target + dbt logs only (keep DuckDB; re-run dbt run)
    Streamlit         - dashboard __pycache__, repo .streamlit if present

  From repo root (use Bypass if execution policy blocks scripts):
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\reset-project.ps1 -Scope Full
    .\scripts\reset-project.ps1 -Scope MedallionSilver
    .\scripts\reset-project.ps1 -Scope Full -IncludeAirflowHome

.PARAMETER IncludeAirflowHome
  Also removes airflow/airflow_home (Airflow metadata). Off by default.

.EXAMPLE
  .\scripts\reset-project.ps1 -Scope MedallionGold
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        "Full",
        "Datagenerator",
        "MedallionFull",
        "MedallionBronze",
        "MedallionSilver",
        "MedallionGold",
        "DbtSql",
        "Streamlit"
    )]
    [string] $Scope,
    [switch] $IncludeAirflowHome
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$PythonExe = if (Test-Path -LiteralPath $venvPy) { $venvPy } else { "python" }

$script = Join-Path $Root "scripts\reset_project.py"
if (-not (Test-Path -LiteralPath $script)) {
    Write-Error "Missing $script"
    exit 1
}

$pyArgs = @($script, "--scope", $Scope)
if ($IncludeAirflowHome) {
    $pyArgs += "--include-airflow-home"
}

Write-Host ("Reset scope: " + $Scope) -ForegroundColor Cyan
& $PythonExe @pyArgs
exit $LASTEXITCODE
