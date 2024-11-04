# Thin launcher so you can run: .\run-sql-kpis.ps1 (from repo root; PowerShell requires .\ for local scripts)
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "scripts\run-sql-kpis.ps1")
exit $LASTEXITCODE
