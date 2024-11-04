#Requires -Version 5.1
<#
.SYNOPSIS
  dbt test only (from dbt/).

.DESCRIPTION
  Sets DELTA_LAKE_PATH. Example: .\scripts\run-dbt-test.ps1 --select source:silver
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
    & $DbtExe test @ScriptArgs
} finally {
    Pop-Location
}
exit $LASTEXITCODE
