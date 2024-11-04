#Requires -Version 5.1
<#
.SYNOPSIS
  Bronze ingest only — PySpark writes Delta tables under delta_lake/bronze/.

.DESCRIPTION
  Sets JAVA_HOME (Temurin 17 if unset), HADOOP_HOME + winutils, DELTA_LAKE_PATH.
  From repo root: .\scripts\run-ingest.ps1
  Forward ingest.py args: .\scripts\run-ingest.ps1 --dataset beneficiaries
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

Initialize-PipelineSparkWindows
Set-PipelineDeltaLakeEnv

$PythonExe = Get-PipelinePython
Set-PipelinePySparkPython -PythonExe $PythonExe
Write-Host ("Using Python: " + $PythonExe) -ForegroundColor DarkGray
& $PythonExe (Join-Path $Root "ingest\ingest.py") @ScriptArgs
exit $LASTEXITCODE
