#Requires -Version 5.1
<#
.SYNOPSIS
  dbt docs generate + dbt docs serve (blocks until Ctrl+C).

.DESCRIPTION
  Sets DELTA_LAKE_PATH. Opens local docs server (default http://localhost:8080 for dbt — may
  conflict with Airflow; stop Airflow first or change dbt port in dbt_project if needed).

  From repo root: .\scripts\run-dbt-docs.ps1
  Example port: .\scripts\run-dbt-docs.ps1 --port 8085
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ScriptArgs
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_pipeline-common.ps1"
$Root = Get-PipelineRepoRoot
Set-Location $Root

Set-PipelineDeltaLakeEnv
$DbtExe = Get-PipelineDbtExe
Push-Location (Join-Path $Root "dbt")
try {
    & $DbtExe docs generate
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $DbtExe docs serve @ScriptArgs
} finally {
    Pop-Location
}
exit $LASTEXITCODE
