#Requires -Version 5.1
<#
.SYNOPSIS
  dbt run only (from dbt/).

.DESCRIPTION
  Sets DELTA_LAKE_PATH. Example: .\scripts\run-dbt-run.ps1 --select stg_beneficiaries
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
    & $DbtExe run @ScriptArgs
} finally {
    Pop-Location
}
exit $LASTEXITCODE
