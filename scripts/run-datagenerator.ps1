#Requires -Version 5.1
<#
.SYNOPSIS
  Runs datagenerator.py — writes synthetic datasets under data_large/.

.DESCRIPTION
  From repo root:
    .\scripts\run-datagenerator.ps1
  Extra args are forwarded to Python (e.g. none today; reserved for future CLI).

  Requires .venv (network if Kaggle enrichment runs).
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

$PythonExe = Get-PipelinePython
Write-Host ("Using Python: " + $PythonExe) -ForegroundColor DarkGray
& $PythonExe (Join-Path $Root "datagenerator.py") @ScriptArgs
exit $LASTEXITCODE
