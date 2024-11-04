# =============================================================================
# setup_java17.ps1
# Installs Eclipse Temurin JDK 17 via winget and configures JAVA_HOME
# Run from an elevated (Administrator) PowerShell prompt:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\setup_java17.ps1
# =============================================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Java 17 Setup for PySpark (Windows)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Step 1 - Check current Java
# ---------------------------------------------------------------------------
Write-Host "[1/4] Checking current Java..." -ForegroundColor Yellow
$javaOut = (java -version 2>&1 | ForEach-Object { "$_" }) -join "`n"
Write-Host $javaOut.Trim()

if ($javaOut -match '"(8|11|17)\.') {
    Write-Host "Already on a compatible Java version. Nothing to do." -ForegroundColor Green
    exit 0
}
Write-Host "Java 25 detected - incompatible with PySpark 3.5.1" -ForegroundColor Red
Write-Host ""

# ---------------------------------------------------------------------------
# Step 2 - Install Temurin 17 via winget
# ---------------------------------------------------------------------------
Write-Host "[2/4] Installing Eclipse Temurin JDK 17 via winget..." -ForegroundColor Yellow
Write-Host "      (This may take 2-3 minutes)" -ForegroundColor Gray

winget install --id EclipseAdoptium.Temurin.17.JDK --silent --accept-package-agreements --accept-source-agreements --override "ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome"
$wingetExit = $LASTEXITCODE
Write-Host ""

# 0 = success, -1978335189 (0x80073D06) = already installed
if ($wingetExit -eq 0 -or $wingetExit -eq -1978335189) {
    Write-Host "Temurin 17 installed (or already present)" -ForegroundColor Green
} else {
    Write-Host "winget install failed with exit code: $wingetExit" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual fallback - download the MSI directly:" -ForegroundColor Yellow
    Write-Host "  https://adoptium.net/temurin/releases/?version=17" -ForegroundColor White
    Write-Host "  Choose: Windows x64 MSI" -ForegroundColor White
    Write-Host "  During install: check 'Set JAVA_HOME variable' and 'Add to PATH'" -ForegroundColor White
    exit 1
}

# ---------------------------------------------------------------------------
# Step 3 - Set JAVA_HOME and update PATH
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Configuring JAVA_HOME..." -ForegroundColor Yellow

# Temurin 17 installs under Program Files\Eclipse Adoptium\jdk-17.*
$temurinBase = "C:\Program Files\Eclipse Adoptium"
$jdk17Path = $null

if (Test-Path $temurinBase) {
    $jdk17Path = Get-ChildItem -Path $temurinBase -Filter "jdk-17*" -Directory -ErrorAction SilentlyContinue |
                 Sort-Object Name -Descending |
                 Select-Object -First 1 -ExpandProperty FullName
}

if (-not $jdk17Path) {
    $candidates = @(
        "C:\Program Files\Eclipse Adoptium\jdk-17.0.13.11-hotspot",
        "C:\Program Files\Microsoft\jdk-17.0.13.11-hotspot",
        "C:\Program Files\Java\jdk-17"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $jdk17Path = $c; break }
    }
}

if ($jdk17Path) {
    Write-Host "  Found JDK 17 at: $jdk17Path" -ForegroundColor White

    [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $jdk17Path, "Machine")

    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $jdk17Bin = "$jdk17Path\bin"
    if ($machinePath -notlike "*$jdk17Bin*") {
        [System.Environment]::SetEnvironmentVariable("Path", "$jdk17Bin;$machinePath", "Machine")
        Write-Host "  Added $jdk17Bin to system PATH" -ForegroundColor White
    }

    $env:JAVA_HOME = $jdk17Path
    $env:Path = "$jdk17Bin;" + $env:Path

    Write-Host "JAVA_HOME set to: $jdk17Path" -ForegroundColor Green
} else {
    Write-Host "Could not locate JDK 17 directory automatically." -ForegroundColor Yellow
    Write-Host "Set JAVA_HOME manually after the installer completes." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Step 4 - Verify PySpark
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Verifying PySpark with Java 17..." -ForegroundColor Yellow

$pyTestFile = [System.IO.Path]::GetTempFileName() + ".py"
$pyCode = 'import os' + "`n"
$pyCode += 'print("JAVA_HOME =", os.environ.get("JAVA_HOME", "(not set)"))' + "`n"
$pyCode += 'from pyspark.sql import SparkSession' + "`n"
$pyCode += 'spark = SparkSession.builder.master("local[1]").appName("verify").getOrCreate()' + "`n"
$pyCode += 'spark.sparkContext.setLogLevel("ERROR")' + "`n"
$pyCode += 'count = spark.range(5).count()' + "`n"
$pyCode += 'spark.stop()' + "`n"
$pyCode += 'print("PySpark OK - spark.range(5).count() =", count)' + "`n"

Set-Content -Path $pyTestFile -Value $pyCode -Encoding UTF8

$pyOut = python $pyTestFile 2>&1 | Out-String
Write-Host $pyOut

if ($pyOut -match "PySpark OK") {
    Write-Host "PySpark is working correctly with Java 17!" -ForegroundColor Green
} else {
    Write-Host "PySpark test did not confirm success." -ForegroundColor Yellow
    Write-Host "Open a NEW terminal (to pick up the new JAVA_HOME) and run:" -ForegroundColor Yellow
    Write-Host "  python test_pyspark.py" -ForegroundColor White
}

Remove-Item $pyTestFile -ErrorAction SilentlyContinue

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Open a NEW terminal before running tests." -ForegroundColor Yellow
Write-Host "The current terminal may still have Java 25 in its PATH." -ForegroundColor Yellow
Write-Host ""
Write-Host "Then run:" -ForegroundColor White
Write-Host "  pytest tests/ -v -m not integration   # fast tests (no Spark)" -ForegroundColor Cyan
Write-Host "  pytest tests/ -v                       # all tests including Spark" -ForegroundColor Cyan
Write-Host "  python ingest/ingest.py                # run ingestion pipeline" -ForegroundColor Cyan
Write-Host ""
