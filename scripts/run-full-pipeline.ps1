#Requires -Version 5.1
<#
.SYNOPSIS
  Runs ingest, PySpark notebook execution, dbt run/test, and KPI SQL (Windows-friendly make all).

.DESCRIPTION
  From repository root:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\run-full-pipeline.ps1

  Uses .venv\Scripts\python.exe when present.
  Sets JAVA_HOME (Temurin 17 if unset) and HADOOP_HOME + winutils for Spark on Windows.

  Prerequisites: run .\setup.ps1 first, DuckDB CLI on PATH for the KPI step.
#>
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_pipeline-common.ps1"
$Root = Get-PipelineRepoRoot
Set-Location $Root

Initialize-PipelineSparkWindows

$PythonExe = Get-PipelinePython
$DbtExe = Get-PipelineDbtExe
Set-PipelinePySparkPython -PythonExe $PythonExe

Write-Host ("Using Python: " + $PythonExe) -ForegroundColor DarkGray
Write-Host ("PYSPARK_PYTHON: " + $env:PYSPARK_PYTHON) -ForegroundColor DarkGray

Set-PipelineDeltaLakeEnv

Write-Host "=== [1/4] Bronze ingest (PySpark) ===" -ForegroundColor Cyan
& $PythonExe (Join-Path $Root "ingest\ingest.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error ("Bronze ingest failed with exit code " + $LASTEXITCODE)
    exit $LASTEXITCODE
}

Write-Host "=== [2/4] Silver notebook (nbconvert execute) ===" -ForegroundColor Cyan
$nbDir = Join-Path $Root "notebooks"
$nbIn = Join-Path $nbDir "delta_lake_operations.ipynb"
& $PythonExe -m jupyter nbconvert --to notebook --execute $nbIn --output-dir $nbDir --output "delta_lake_operations_executed.ipynb"
if ($LASTEXITCODE -ne 0) {
    Write-Error ("Notebook execution failed with exit code " + $LASTEXITCODE)
    exit $LASTEXITCODE
}

# Give the Spark JVM / OS a moment to release Windows handles on Delta Lake
# directories before dbt-duckdb opens them (avoids "File is already open").
Write-Host "Waiting 5s for Delta file handles to release before dbt ..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

Write-Host "=== [3/4] dbt run + test ===" -ForegroundColor Cyan
Push-Location (Join-Path $Root "dbt")
& $DbtExe run
$dbtRunExit = $LASTEXITCODE
& $DbtExe test
$dbtTestExit = $LASTEXITCODE
Pop-Location
if ($dbtRunExit -ne 0) {
    Write-Error ("dbt run failed with exit code " + $dbtRunExit)
    exit $dbtRunExit
}
if ($dbtTestExit -ne 0) {
    Write-Error ("dbt test failed with exit code " + $dbtTestExit)
    exit $dbtTestExit
}

Write-Host "=== [4/4] KPI SQL files ===" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "run-sql-kpis.ps1")
if ($LASTEXITCODE -ne 0) {
    Write-Error ("KPI SQL step failed with exit code " + $LASTEXITCODE)
    exit $LASTEXITCODE
}

Write-Host "Pipeline finished." -ForegroundColor Green
