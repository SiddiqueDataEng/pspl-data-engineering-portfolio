#Requires -Version 5.1
<#
.SYNOPSIS
  Creates a local Python virtual environment and installs project dependencies.

.DESCRIPTION
  Prefers Python 3.11 or 3.10 (recommended for PySpark in this repo), then tries
  other py launcher versions, then falls back to `python` on PATH.

  From the repository root:
    .\setup.ps1
    .\setup.ps1 -Force          # delete existing .venv and recreate
    .\setup.ps1 -Python py -3.10  # explicit interpreter (must support -m venv)

  If you see "running scripts is disabled on this system", use either:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\setup.ps1 -Force -Python 'py -3.11'
  or a one-liner (no policy change stored on disk):
    powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Force -Python 'py -3.11'

.PARAMETER Force
  Remove an existing .venv directory before creating a new environment.

.PARAMETER Python
  Command used to invoke Python for venv creation (default: auto-detect).
  Example: py -3.11, py -3.10, python
#>
[CmdletBinding()]
param(
    [switch] $Force,
    [string] $Python = ""
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$VenvDir = Join-Path $Root ".venv"
$Req = Join-Path $Root "requirements.txt"

function Test-VenvPython {
    param([string] $ExePath)
    if (-not (Test-Path -LiteralPath $ExePath)) { return $false }
    $ver = & $ExePath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    return [bool]$ver
}

function Resolve-PythonLauncher {
    # Prefer pinned runtimes; try plain `python` before `py -3` so PATH does not lose to a generic 3.14+ default.
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3.11") },
        @{ Cmd = "py"; Args = @("-3.10") },
        @{ Cmd = "py"; Args = @("-3.12") },
        @{ Cmd = "python"; Args = @() },
        @{ Cmd = "py"; Args = @("-3") }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Cmd -ErrorAction SilentlyContinue)) { continue }
        $invokeArgs = @($c.Args + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"))
        $oldEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & $c.Cmd @invokeArgs 2>$null | Out-Null
        } catch {
            continue
        } finally {
            $ErrorActionPreference = $oldEap
        }
        if ($LASTEXITCODE -eq 0) {
            return @{ Cmd = $c.Cmd; Args = $c.Args }
        }
    }
    return $null
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Python venv + pip install (Windows)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path -LiteralPath $Req)) {
    Write-Error "Missing requirements.txt at $Req"
    exit 1
}

if ($Force -and (Test-Path -LiteralPath $VenvDir)) {
    Write-Host "[0/3] Removing existing .venv (-Force)..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $VenvDir -Recurse -Force
}

$pyCmd = $null
$pyArgs = @()

if ($Python) {
    $parts = $Python.Trim() -split '\s+', 2
    $pyCmd = $parts[0]
    if ($parts.Count -gt 1 -and $parts[1]) {
        $pyArgs = ($parts[1] -split '\s+')
    }
    Write-Host "[1/3] Using explicit Python: $Python" -ForegroundColor Yellow
} else {
    Write-Host "[1/3] Detecting Python 3.10+ (prefer 3.11 / 3.10)..." -ForegroundColor Yellow
    $resolved = Resolve-PythonLauncher
    if (-not $resolved) {
        Write-Error "No Python 3.10+ found. Install Python or use: .\setup.ps1 -Python 'py -3.11'"
        exit 1
    }
    $pyCmd = $resolved.Cmd
    $pyArgs = $resolved.Args
    Write-Host "        Selected: $pyCmd $($pyArgs -join ' ')" -ForegroundColor Green
}

if (-not (Test-Path -LiteralPath $VenvDir)) {
    Write-Host "[2/3] Creating virtual environment at .venv ..." -ForegroundColor Yellow
    $venvArgs = @($pyArgs + @("-m", "venv", $VenvDir))
    & $pyCmd @venvArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "venv creation failed (exit $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
} else {
    Write-Host "[2/3] Using existing .venv (omit -Force to keep; use -Force to recreate)." -ForegroundColor Yellow
}

$venvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-VenvPython -ExePath $venvPython)) {
    Write-Error "Expected interpreter missing: $venvPython"
    exit 1
}

$verStr = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "        venv Python: $verStr" -ForegroundColor Green

$verTuple = & $venvPython -c "import sys; print(sys.version_info[0], sys.version_info[1])"
$maj, $min = $verTuple -split '\s+'
if ([int]$maj -gt 3 -or ([int]$maj -eq 3 -and [int]$min -ge 13)) {
    Write-Host ""
    Write-Warning "Python 3.13+ often breaks pinned wheels (e.g. pandas/pyspark) in requirements.txt. Prefer 3.11 or 3.10: py install 3.11 then .\setup.ps1 -Force -Python 'py -3.11'"
    Write-Host ""
}

Write-Host "[3/3] Upgrading pip and installing requirements.txt ..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
# Prefer wheels on Windows so matplotlib/numpy do not require MSVC to build from sdist.
& $venvPython -m pip install --prefer-binary -r $Req
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host ""
Write-Host "Activate the environment:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "PySpark needs JDK 11 or 17 and JAVA_HOME. If Java is not set up yet:" -ForegroundColor Cyan
Write-Host "  See .\setup_java17.ps1 (run elevated if using winget)." -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  docs\getting-started.html - copy/paste commands" -ForegroundColor White
Write-Host '  .\scripts\run-component.ps1 STEP  - one of: datagenerator, ingest, spark-notebook, dbt-run, ...' -ForegroundColor White
Write-Host ""
