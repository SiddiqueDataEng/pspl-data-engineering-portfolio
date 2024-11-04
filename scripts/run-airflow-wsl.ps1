#Requires -Version 5.1
<#
.SYNOPSIS
  Starts Airflow standalone inside WSL2 (supported alternative to native Windows).

.DESCRIPTION
  Uses a Linux venv at .venv-wsl/ (separate from Windows .venv).
  UI: http://localhost:8080

.PARAMETER Distro
  WSL distribution name (default: WSL default distro).

.EXAMPLE
  .\scripts\run-airflow-wsl.ps1
  .\scripts\run-airflow-wsl.ps1 -Distro Ubuntu
#>
[CmdletBinding()]
param(
    [string] $Distro = ""
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_airflow-preflight.ps1"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    Write-Error "wsl.exe not found. Enable WSL: wsl --install"
    exit 1
}

$wslInfo = Test-WslAvailable
if (-not $wslInfo.Ok) {
    Write-Error "WSL is not available. Run: wsl --install"
    exit 1
}
$useDistro = if ($Distro) { $Distro } else { $wslInfo.Distro }
$wslPath = Convert-WindowsPathToWsl -WindowsPath $Root -Distro $useDistro
if (-not $wslPath) {
    Write-Error "Could not convert repo path to WSL path: $Root"
    exit 1
}

$shScript = Join-Path $Root "scripts\airflow-wsl.sh"
if (-not (Test-Path -LiteralPath $shScript)) {
    Write-Error "Missing $shScript"
    exit 1
}

if ($useDistro) {
    Write-Host ("WSL distro: " + $useDistro) -ForegroundColor DarkGray
}
Write-Host "WSL repo path: $wslPath" -ForegroundColor DarkGray
Write-Host "Starting Airflow in WSL (standalone). UI: http://localhost:8080" -ForegroundColor Cyan

$distroArgs = @()
if ($useDistro) {
    $distroArgs = @("-d", $useDistro)
}

# Escape single quotes for bash -lc
$escaped = $wslPath.Replace("'", "'\''")
$inner = "cd '$escaped' && sed -i 's/\r$//' scripts/airflow-wsl.sh 2>/dev/null || true && bash scripts/airflow-wsl.sh"

& wsl.exe @distroArgs bash -lc "$inner"
exit $LASTEXITCODE
