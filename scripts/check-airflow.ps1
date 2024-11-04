#Requires -Version 5.1
<#
.SYNOPSIS
  Diagnoses Airflow setup (venv, Docker, WSL, DAGs) without starting a long-running server.

.EXAMPLE
  .\scripts\check-airflow.ps1
#>
$ErrorActionPreference = "Continue"
. "$PSScriptRoot\_airflow-preflight.ps1"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$ok = $true
Write-Host "=== Airflow preflight ===" -ForegroundColor Cyan

if (Test-IsNativeWindows) {
    Write-Host "[OS] Native Windows - use Docker or WSL for scheduler/UI (not .venv standalone)." -ForegroundColor Yellow
} else {
    Write-Host "[OS] POSIX-like - native standalone may work." -ForegroundColor Green
}

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$airflowExe = Join-Path $Root ".venv\Scripts\airflow.exe"
if (Test-Path -LiteralPath $airflowExe) {
    Write-Host "[venv-win] airflow.exe found (CLI / DAG lint on Windows)" -ForegroundColor Green
    $ah = Join-Path $Root "airflow\airflow_home"
    New-Item -ItemType Directory -Path $ah -Force | Out-Null
    Set-AirflowWindowsSafeEnv -AirflowHome $ah -DagsFolder (Join-Path $Root "airflow\dags") -RepoRoot $Root
    & $airflowExe version 2>&1 | ForEach-Object { Write-Host "           $_" }
} else {
    Write-Host "[venv-win] airflow.exe missing - optional: .\scripts\install-airflow.ps1" -ForegroundColor Yellow
}

$docker = Test-DockerCliAvailable
if ($docker.Ok) {
    Write-Host ("[docker] CLI: " + $docker.Exe) -ForegroundColor Green
    & $docker.Exe version 2>&1 | Select-Object -First 1 | ForEach-Object { Write-Host "         $_" }
} else {
    Write-Host "[docker] CLI not found" -ForegroundColor Yellow
    if (Test-IsNativeWindows) { $ok = $false }
}

$wsl = Test-WslAvailable
if ($wsl.Ok) {
    if ($wsl.Distro) {
        Write-Host ("[wsl]    distro: " + $wsl.Distro) -ForegroundColor Green
    }
    $wslPath = Convert-WindowsPathToWsl -WindowsPath $Root -Distro $wsl.Distro
    Write-Host ("[wsl]    repo -> " + $wslPath) -ForegroundColor Green
    $escaped = $wslPath.Replace("'", "'\''")
    $wslPy = & wsl.exe bash -lc "test -x '$escaped/.venv-wsl/bin/python' && echo yes || echo no" 2>&1
    if ($wslPy -match "yes") {
        Write-Host "[wsl]    .venv-wsl exists (run .\scripts\run-airflow-wsl.ps1 to start)" -ForegroundColor Green
    } else {
        Write-Host "[wsl]    .venv-wsl will be created on first run-airflow-wsl.ps1" -ForegroundColor DarkGray
    }
} else {
    Write-Host "[wsl]    not available (wsl --install)" -ForegroundColor Yellow
    if (Test-IsNativeWindows -and -not $docker.Ok) { $ok = $false }
}

$dags = Join-Path $Root "airflow\dags"
if (Test-Path -LiteralPath $dags) {
    $pyCount = (Get-ChildItem -Path $dags -Filter "*.py" -ErrorAction SilentlyContinue).Count
    Write-Host ("[dags]   $pyCount Python file(s) in airflow\dags") -ForegroundColor Green
} else {
    Write-Host "[dags]   missing $dags" -ForegroundColor Red
    $ok = $false
}

Write-Host ""
if ($ok) {
    Write-Host "OK. Start Airflow on Windows:" -ForegroundColor Green
    Write-Host "  .\scripts\run-airflow-with-setup.ps1 -Mode Docker" -ForegroundColor White
    Write-Host "  .\scripts\run-airflow-with-setup.ps1 -Mode Wsl" -ForegroundColor White
    Write-Host "  .\scripts\run-airflow-with-setup.ps1          (Auto: Docker then WSL)" -ForegroundColor DarkGray
    exit 0
}
Write-Host "Install Docker Desktop and/or WSL, then run check again." -ForegroundColor Yellow
exit 1
