#Requires -Version 5.1
<#
.SYNOPSIS
  Starts local Airflow via Docker Compose, resolving docker.exe when it is not on PATH.

.DESCRIPTION
  Docker Desktop often installs to "Program Files\Docker\Docker\resources\bin\docker.exe"
  but the current PowerShell session may not see an updated PATH until you restart the terminal.
  This script merges Machine/User PATH from the registry, searches default install locations,
  optionally starts Docker Desktop if the engine is down, then runs:
    docker compose -f docker-compose.airflow.yml up

.EXAMPLE
  .\scripts\run-airflow-docker.ps1
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Merge-PathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
    $extra = (@($wingetLinks, $machine, $user) | Where-Object { $_ -and $_.Trim() }) -join ";"
    if ($extra) {
        $env:Path = $extra.TrimEnd(";") + ";" + $env:Path
    }
}

function Resolve-DockerExe {
    $found = Get-Command docker -ErrorAction SilentlyContinue
    if ($found) {
        return $found.Source
    }
    Merge-PathFromRegistry
    $found = Get-Command docker -ErrorAction SilentlyContinue
    if ($found) {
        return $found.Source
    }
    $candidates = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Docker\Docker\resources\bin\docker.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Docker\Docker\resources\bin\docker.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe")
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            return $p
        }
    }
    return $null
}

function Wait-DockerDaemon {
    param([string] $DockerExe, [int] $MaxWaitSeconds = 420)
    $deadline = [DateTime]::UtcNow.AddSeconds($MaxWaitSeconds)
    $nextMsg = [DateTime]::UtcNow
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-DockerEngineUp -DockerExe $DockerExe) {
            return $true
        }
        if ([DateTime]::UtcNow -ge $nextMsg) {
            $left = [math]::Max(0, [int]($deadline - [DateTime]::UtcNow).TotalSeconds)
            Write-Host "  Still waiting for Docker engine (${left}s max)..." -ForegroundColor DarkGray
            $nextMsg = [DateTime]::UtcNow.AddSeconds(30)
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Test-DockerEngineUp {
    param([string] $DockerExe)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        & $DockerExe @("info") 1>$null 2>$null
        return ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Resolve-DockerDesktopExeNearCli {
    param([string] $DockerExe)
    $cur = Split-Path -Parent $DockerExe
    for ($i = 0; $i -lt 8; $i++) {
        $guess = Join-Path $cur "Docker Desktop.exe"
        if (Test-Path -LiteralPath $guess) {
            return $guess
        }
        $parent = Split-Path -Parent $cur
        if (-not $parent -or $parent -eq $cur) {
            break
        }
        $cur = $parent
    }
    return $null
}

function Resolve-DockerDesktopExe {
    $candidates = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Docker\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe")
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            return $p
        }
    }
    return $null
}

$dockerExe = Resolve-DockerExe
if (-not $dockerExe) {
    Write-Error @"
docker.exe not found.

Install Docker Desktop from https://www.docker.com/products/docker-desktop/ then either:
  - Close and reopen PowerShell (or Cursor), or
  - Run this script again: .\scripts\run-airflow-docker.ps1
"@
    exit 1
}

Write-Host "Using Docker: $dockerExe" -ForegroundColor DarkGray

if (-not (Test-DockerEngineUp -DockerExe $dockerExe)) {
    $desktop = Resolve-DockerDesktopExe
    if (-not $desktop) {
        $desktop = Resolve-DockerDesktopExeNearCli -DockerExe $dockerExe
    }
    if ($desktop) {
        Write-Host "Docker engine not responding. Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process -FilePath $desktop
        if (-not (Wait-DockerDaemon -DockerExe $dockerExe)) {
            Write-Error "Docker engine did not become ready within ~7 minutes after starting Docker Desktop. Finish any first-run steps (WSL, license), wait until Docker shows ""Engine running"", then run: .\scripts\run-airflow-docker.ps1"
            exit 1
        }
    } else {
        Write-Error "Docker engine is not running and Docker Desktop.exe was not found under Program Files or Local App Programs. Start Docker Desktop manually, then retry."
        exit 1
    }
}

$composeFile = Join-Path $Root "docker-compose.airflow.yml"
if (-not (Test-Path -LiteralPath $composeFile)) {
    Write-Error "Missing $composeFile"
    exit 1
}

Write-Host "Starting Airflow (Ctrl+C to stop). UI: http://localhost:8080" -ForegroundColor Cyan
& $dockerExe @("compose", "-f", $composeFile, "up")
exit $LASTEXITCODE
