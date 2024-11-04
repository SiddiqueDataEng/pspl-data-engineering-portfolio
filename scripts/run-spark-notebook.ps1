#Requires -Version 5.1
<#
.SYNOPSIS
  Executes notebooks/delta_lake_operations.ipynb only (Silver Delta tables).

.DESCRIPTION
  Uses jupyter nbconvert --execute with --output-dir/--output so paths are not doubled
  under notebooks/. Sets Spark-on-Windows env like the full pipeline.
  After this, wait a few seconds before dbt on Windows if you see Delta file lock errors.

  From repo root: .\scripts\run-spark-notebook.ps1
#>
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_pipeline-common.ps1"
$Root = Get-PipelineRepoRoot
Set-Location $Root

Initialize-PipelineSparkWindows

$PythonExe = Get-PipelinePython
Set-PipelinePySparkPython -PythonExe $PythonExe
$nbDir = Join-Path $Root "notebooks"
$nbIn = Join-Path $nbDir "delta_lake_operations.ipynb"
Write-Host ("Using Python: " + $PythonExe) -ForegroundColor DarkGray
# Use --output-dir + basename: passing --output notebooks/... breaks nbconvert (it joins
# paths relative to the notebook folder → notebooks/notebooks/... → FileNotFoundError).
& $PythonExe -m jupyter nbconvert --to notebook --execute $nbIn --output-dir $nbDir --output "delta_lake_operations_executed.ipynb"
exit $LASTEXITCODE
