#Requires -Version 5.1
<#
.SYNOPSIS
  Removes generated Delta tables, DuckDB file, and dbt build folders (Windows equivalent of `make clean`).

.DESCRIPTION
  Delegates to scripts/reset_project.py with scope PipelineBuild (same artifacts as the legacy clean).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$PythonExe = if (Test-Path -LiteralPath $venvPy) { $venvPy } else { "python" }
$script = Join-Path $Root "scripts\reset_project.py"
if (-not (Test-Path -LiteralPath $script)) {
    Write-Error "Missing $script"
    exit 1
}

& $PythonExe $script --scope PipelineBuild
exit $LASTEXITCODE
