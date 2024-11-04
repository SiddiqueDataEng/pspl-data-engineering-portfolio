#Requires -Version 5.1
<#
.SYNOPSIS
  Runs one pipeline component by name (wrapper around individual scripts).

.DESCRIPTION
  From repo root:
    .\scripts\run-component.ps1 datagenerator
    .\scripts\run-component.ps1 ingest
    .\scripts\run-component.ps1 dbt-run --% --select mart_payments

  Valid names:
    datagenerator, ingest, spark-notebook, dbt-run, dbt-test, dbt-docs,
    sql-kpis, dashboard, airflow-docker, airflow-wsl, airflow-standalone, check-airflow,
    reset, airflow-setup-run, reset-and-pipeline

  Reset examples:
    .\scripts\run-component.ps1 reset Full
    .\scripts\run-component.ps1 reset MedallionSilver

  For dbt/ingest flags, prefer the stop-parsing token `--%` before flags, or call the underlying `run-*.ps1` script directly.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        "datagenerator",
        "ingest",
        "spark-notebook",
        "dbt-run",
        "dbt-test",
        "dbt-docs",
        "sql-kpis",
        "dashboard",
        "airflow-docker",
        "airflow-wsl",
        "airflow-standalone",
        "check-airflow",
        "reset",
        "airflow-setup-run",
        "reset-and-pipeline"
    )]
    [string] $Name,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $RemainingArgs
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$forward = @()
if ($RemainingArgs) {
    $forward = @($RemainingArgs)
}

switch ($Name) {
    "datagenerator" { & (Join-Path $here "run-datagenerator.ps1") @forward; break }
    "ingest" { & (Join-Path $here "run-ingest.ps1") @forward; break }
    "spark-notebook" { & (Join-Path $here "run-spark-notebook.ps1") @forward; break }
    "dbt-run" { & (Join-Path $here "run-dbt-run.ps1") @forward; break }
    "dbt-test" { & (Join-Path $here "run-dbt-test.ps1") @forward; break }
    "dbt-docs" { & (Join-Path $here "run-dbt-docs.ps1") @forward; break }
    "sql-kpis" { & (Join-Path $here "run-sql-kpis.ps1") @forward; break }
    "dashboard" { & (Join-Path $here "run-dashboard.ps1") @forward; break }
    "airflow-docker" { & (Join-Path $here "run-airflow-docker.ps1") @forward; break }
    "airflow-wsl" { & (Join-Path $here "run-airflow-wsl.ps1") @forward; break }
    "airflow-standalone" { & (Join-Path $here "airflow-standalone.ps1") @forward; break }
    "check-airflow" { & (Join-Path $here "check-airflow.ps1") @forward; break }
    "reset" {
        if (-not $forward -or $forward.Count -eq 0) {
            Write-Error "Missing scope. Example: .\scripts\run-component.ps1 reset Full"
            exit 1
        }
        & (Join-Path $here "reset-project.ps1") @forward
        break
    }
    "airflow-setup-run" { & (Join-Path $here "run-airflow-with-setup.ps1") @forward; break }
    "reset-and-pipeline" { & (Join-Path $here "run-reset-and-pipeline.ps1") @forward; break }
}
exit $LASTEXITCODE
