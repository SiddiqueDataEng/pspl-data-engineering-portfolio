#Requires -Version 5.1
<#
.SYNOPSIS
  Runs every .sql file in sql/ against pspl.duckdb (Windows equivalent of make sql-kpis).

.DESCRIPTION
  From repo root use either .\run-sql-kpis.ps1 or .\scripts\run-sql-kpis.ps1
  (PowerShell does not run bare script names; the .\ prefix is required.)
  Requires DuckDB CLI (https://duckdb.org/docs/installation/). After winget install, PATH
  is merged from the registry so you do not need to restart the shell.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Resolve-DuckdbExe {
    $found = Get-Command duckdb -ErrorAction SilentlyContinue
    if ($found) {
        return $found.Source
    }
    # winget updates User/Machine PATH; prepend so we pick up duckdb without dropping session PATH (e.g. .venv\Scripts)
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
    $extra = (@($wingetLinks, $machine, $user) | Where-Object { $_ -and $_.Trim() }) -join ";"
    if ($extra) {
        $env:Path = $extra.TrimEnd(";") + ";" + $env:Path
    }
    $found = Get-Command duckdb -ErrorAction SilentlyContinue
    if ($found) {
        return $found.Source
    }
    $wingetShim = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\duckdb.exe"
    if (Test-Path -LiteralPath $wingetShim) {
        return $wingetShim
    }
    $pkgRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path -LiteralPath $pkgRoot) {
        $nested = Get-ChildItem -LiteralPath $pkgRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "DuckDB*" -or $_.Name -like "*DuckDB.cli*" }
        foreach ($d in $nested) {
            $exePath = Get-ChildItem -LiteralPath $d.FullName -Filter "duckdb.exe" -Recurse -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($exePath) {
                return $exePath.FullName
            }
        }
    }
    return $null
}

$DuckDb = Join-Path $Root "pspl.duckdb"
if (-not (Test-Path -LiteralPath $DuckDb)) {
    Write-Warning (
        "Missing DuckDB file: $DuckDb. Create it after Silver Delta tables exist: set DELTA_LAKE_PATH to the repo delta_lake folder (forward slashes), run dbt from the dbt folder, or run .\scripts\run-full-pipeline.ps1 from repo root."
    )
    exit 1
}

$duckExe = Resolve-DuckdbExe
if (-not $duckExe) {
    Write-Error "duckdb CLI not found. Install with winget install DuckDB.cli, open a new terminal, or ensure duckdb.exe is on PATH."
    exit 1
}
Write-Host ("Using DuckDB CLI: " + $duckExe) -ForegroundColor DarkGray

Get-ChildItem -Path (Join-Path $Root "sql") -Filter "*.sql" | Sort-Object Name | ForEach-Object {
    Write-Host ("Running " + $_.Name)
    Get-Content -LiteralPath $_.FullName -Raw | & $duckExe $DuckDb
    if ($LASTEXITCODE -ne 0) {
        Write-Error ("duckdb failed on " + $_.Name + " (exit " + $LASTEXITCODE + ")")
        exit $LASTEXITCODE
    }
}
