#Requires -Version 5.1
<#
.SYNOPSIS
  Installs Airflow if needed, then starts Airflow via Docker or WSL on Windows.

.DESCRIPTION
  On native Windows, Apache Airflow standalone in .venv is NOT supported.
  Use -Mode Docker or -Mode Wsl (both work when installed).

  -Mode Auto (default on Windows): Docker if CLI is available, else WSL.
  -Mode Docker: docker compose -f docker-compose.airflow.yml up
  -Mode Wsl:    airflow standalone inside WSL (.venv-wsl)
  -Mode Native: attempt Windows .venv standalone (usually fails; not recommended)

.PARAMETER Mode
  Auto | Docker | Wsl | Native

.PARAMETER Distro
  WSL distribution when Mode is Wsl (optional).

.PARAMETER SkipInstall
  Skip install-airflow.ps1 when airflow.exe is missing (Docker/WSL only).

.EXAMPLE
  .\scripts\run-airflow-with-setup.ps1
  .\scripts\run-airflow-with-setup.ps1 -Mode Docker
  .\scripts\run-airflow-with-setup.ps1 -Mode Wsl
#>
[CmdletBinding()]
param(
    [ValidateSet("Auto", "Docker", "Wsl", "Native")]
    [string] $Mode = "Auto",
    [string] $Distro = "",
    [switch] $SkipInstall
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$Root = (Resolve-Path (Join-Path $here "..")).Path
Set-Location $Root
. (Join-Path $here "_airflow-preflight.ps1")

$AirflowExe = Join-Path $Root ".venv\Scripts\airflow.exe"
if (-not (Test-Path -LiteralPath $AirflowExe) -and -not $SkipInstall) {
    Write-Host "Installing Airflow CLI into Windows .venv (for check-airflow / DAG lint) ..." -ForegroundColor Yellow
    & (Join-Path $here "install-airflow.ps1")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if (-not (Test-IsNativeWindows)) {
    $Mode = "Native"
}

switch ($Mode) {
    "Auto" {
        if (-not (Test-IsNativeWindows)) {
            break
        }
        $docker = Test-DockerCliAvailable
        $wsl = Test-WslAvailable
        if ($docker.Ok) {
            Write-Host "Auto: using Docker." -ForegroundColor Cyan
            $Mode = "Docker"
        } elseif ($wsl.Ok) {
            Write-Host "Auto: Docker not found; using WSL." -ForegroundColor Cyan
            $Mode = "Wsl"
        } else {
            Write-AirflowWindowsNotSupportedMessage -FailureDetail "Neither Docker CLI nor WSL responded."
            Write-Error "Install Docker Desktop and/or WSL (wsl --install), then retry."
            exit 1
        }
    }
}

switch ($Mode) {
    "Docker" {
        $docker = Test-DockerCliAvailable
        if (-not $docker.Ok) {
            Write-Error "Docker CLI not found. Install Docker Desktop or use: .\scripts\run-airflow-with-setup.ps1 -Mode Wsl"
            exit 1
        }
        Write-Host "Starting Airflow via Docker ..." -ForegroundColor Cyan
        & (Join-Path $here "run-airflow-docker.ps1")
        exit $LASTEXITCODE
    }
    "Wsl" {
        $wsl = Test-WslAvailable
        if (-not $wsl.Ok) {
            Write-Error "WSL not available. Run: wsl --install   or use: .\scripts\run-airflow-with-setup.ps1 -Mode Docker"
            exit 1
        }
        Write-Host "Starting Airflow via WSL ..." -ForegroundColor Cyan
        if ($Distro) {
            & (Join-Path $here "run-airflow-wsl.ps1") -Distro $Distro
        } else {
            & (Join-Path $here "run-airflow-wsl.ps1")
        }
        exit $LASTEXITCODE
    }
    "Native" {
        if ((Test-IsNativeWindows)) {
            Write-Warning "Native Windows standalone is unsupported by Apache Airflow."
        }
        $standaloneArgs = @()
        if (Test-IsNativeWindows) {
            $standaloneArgs = @("-ForceNativeWindows")
        }
        & (Join-Path $here "airflow-standalone.ps1") @standaloneArgs
        exit $LASTEXITCODE
    }
}

# Linux/macOS default: native standalone
$standaloneArgs = @()
& (Join-Path $here "airflow-standalone.ps1") @standaloneArgs
exit $LASTEXITCODE
