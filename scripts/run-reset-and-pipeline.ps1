#Requires -Version 5.1
<#
.SYNOPSIS
  Full reset, regenerate data, and run the end-to-end pipeline (smoke test).

.DESCRIPTION
  1) reset-project.ps1 -Scope Full
  2) run-datagenerator.ps1
  3) run-full-pipeline.ps1 (ingest, silver notebook, dbt, KPI SQL)

  From repo root:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\run-reset-and-pipeline.ps1

  Expect several minutes (Spark + large synthetic datasets).
#>
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$Root = Split-Path -Parent $here
Set-Location $Root

Write-Host "=== [1/3] Full reset ===" -ForegroundColor Cyan
& (Join-Path $here "reset-project.ps1") -Scope Full
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== [2/3] Data generator ===" -ForegroundColor Cyan
& (Join-Path $here "run-datagenerator.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== [3/3] Full pipeline ===" -ForegroundColor Cyan
& (Join-Path $here "run-full-pipeline.ps1")
exit $LASTEXITCODE
