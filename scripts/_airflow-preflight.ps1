# Dot-source from airflow scripts: . "$PSScriptRoot\_airflow-preflight.ps1"

function Test-IsNativeWindows {
    return ($env:OS -match "Windows") -or ([bool]($PSVersionTable.PSEdition -eq "Desktop" -and $IsWindows))
}

function Write-AirflowWindowsNotSupportedMessage {
    param(
        [string] $FailureDetail = ""
    )
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Airflow cannot run in standalone mode on native Windows" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Apache Airflow expects POSIX subprocesses. On Windows, standalone fails when" -ForegroundColor Yellow
    Write-Host "starting the scheduler / webserver / triggerer (typical error: WinError 2," -ForegroundColor Yellow
    Write-Host "FileNotFoundError from subprocess.Popen)." -ForegroundColor Yellow
    Write-Host ""
    if ($FailureDetail) {
        Write-Host "Detail from this run:" -ForegroundColor DarkGray
        Write-Host $FailureDetail -ForegroundColor DarkGray
        Write-Host ""
    }
    Write-Host "Supported options on Windows:" -ForegroundColor Cyan
    Write-Host "  Docker:  .\scripts\run-airflow-docker.ps1" -ForegroundColor White
    Write-Host "  WSL2:    .\scripts\run-airflow-wsl.ps1" -ForegroundColor White
    Write-Host "  Auto:    .\scripts\run-airflow-with-setup.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Other:" -ForegroundColor Cyan
    Write-Host "  - Run pipeline steps without Airflow:" -ForegroundColor White
    Write-Host "      .\scripts\run-reset-and-pipeline.ps1" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Upstream tracking: https://github.com/apache/airflow/issues/10388" -ForegroundColor DarkGray
    Write-Host ""
}

function Set-AirflowWindowsSafeEnv {
    param(
        [string] $AirflowHome,
        [string] $DagsFolder,
        [string] $RepoRoot
    )
    $env:AIRFLOW_HOME = $AirflowHome
    $env:AIRFLOW__CORE__DAGS_FOLDER = $DagsFolder
    $env:AIRFLOW__CORE__LOAD_EXAMPLES = "False"
    # Symlinks for "latest" log dir often fail on Windows without Developer Mode.
    $env:AIRFLOW__LOGGING__CREATE_LATEST_LOG_LINK = "False"
    if ($RepoRoot) {
        $env:PORTFOLIO_REPO_ROOT = $RepoRoot
    }
}

function Get-AirflowRepoRoot {
    if ($PSScriptRoot) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }
    return (Get-Location).Path
}

function Get-WslDistroNames {
    <# Returns Linux distro names from wsl -l -q (one name per line, no table parsing). #>
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $raw = & wsl.exe -l -q 2>&1
    } finally {
        $ErrorActionPreference = $prev
    }
    if (-not $raw) {
        return @()
    }
    $text = if ($raw -is [array]) { ($raw | Out-String) } else { [string]$raw }
    # wsl -l -q may emit UTF-16; strip null bytes if present.
    $text = $text -replace "`0", ""
    $names = @()
    foreach ($line in ($text -split "[\r\n]+")) {
        $name = $line.Trim()
        if ($name) {
            $names += $name
        }
    }
    return $names
}

function Get-PreferredWslDistro {
    <#
    Prefer a real Linux distro over docker-desktop / podman (wslpath there is unreliable).
    #>
    param([string] $Requested = "")
    if ($Requested) {
        return $Requested
    }
    $names = @(Get-WslDistroNames | Where-Object { $_ -notmatch "docker-desktop|podman" })
    foreach ($prefer in @("Ubuntu", "Ubuntu-24.04", "Ubuntu-22.04", "Ubuntu-20.04", "Debian")) {
        if ($names -contains $prefer) { return $prefer }
    }
    if ($names.Count -gt 0) { return $names[0] }
    return ""
}

function Test-WslAvailable {
    $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if (-not $wsl) {
        return @{ Ok = $false; Exe = $null; Distro = "" }
    }
    $distro = Get-PreferredWslDistro
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $ok = $false
    try {
        if ($distro) {
            & wsl.exe -d $distro -e true 2>&1 | Out-Null
            $ok = ($LASTEXITCODE -eq 0)
        }
        if (-not $ok) {
            & wsl.exe -e true 2>&1 | Out-Null
            $ok = ($LASTEXITCODE -eq 0)
            if ($ok -and -not $distro) {
                $distro = Get-PreferredWslDistro
            }
        }
    } finally {
        $ErrorActionPreference = $prev
    }
    return @{ Ok = $ok; Exe = $wsl.Source; Distro = $distro }
}

function Convert-WindowsPathToWsl {
    param(
        [string] $WindowsPath,
        [string] $Distro = ""
    )
    if (-not $WindowsPath) {
        return $null
    }
    $resolved = (Resolve-Path -LiteralPath $WindowsPath).Path
    $distro = Get-PreferredWslDistro -Requested $Distro
    $distroArgs = @()
    if ($distro) { $distroArgs = @("-d", $distro) }

    # Reliable on Windows: /mnt/c/Users/... (avoids docker-desktop wslpath quirks)
    if ($resolved -match "^([A-Za-z]):\\(.*)$") {
        $drive = $Matches[1].ToLower()
        $rest = ($Matches[2] -replace "\\", "/")
        return "/mnt/$drive/$rest"
    }

    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $out = & wsl.exe @distroArgs wslpath -u $resolved 2>&1
        if ($LASTEXITCODE -eq 0 -and $out) {
            return ($out | Select-Object -First 1).ToString().Trim()
        }
    } finally {
        $ErrorActionPreference = $prev
    }
    return $null
}

function Test-DockerCliAvailable {
    $found = Get-Command docker -ErrorAction SilentlyContinue
    if ($found) {
        return @{ Ok = $true; Exe = $found.Source }
    }
    $candidates = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Docker\Docker\resources\bin\docker.exe")
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            return @{ Ok = $true; Exe = $p }
        }
    }
    return @{ Ok = $false; Exe = $null }
}

function Assert-AirflowNativeWindowsAllowed {
    param(
        [switch] $AllowNative
    )
    if (-not (Test-IsNativeWindows)) {
        return
    }
    if ($AllowNative) {
        Write-Host ""
        Write-Warning "You passed -Native: Airflow standalone on Windows is unsupported and will likely fail."
        Write-Host "Prefer: .\scripts\run-airflow-with-setup.ps1   (uses Docker when available)" -ForegroundColor Yellow
        Write-Host ""
        return
    }
    Write-AirflowWindowsNotSupportedMessage
    throw "Airflow standalone is not supported on native Windows. Use .\scripts\run-airflow-docker.ps1 or -Native to attempt anyway."
}
