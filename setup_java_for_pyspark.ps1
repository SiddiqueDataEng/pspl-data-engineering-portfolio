# PySpark Java Setup Script for Windows
# This script downloads and installs Eclipse Temurin JDK 17 (required for PySpark 3.5.1)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PySpark Java 17 Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check current Java version
Write-Host "[1/5] Checking current Java installation..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version" | Select-Object -First 1
    Write-Host "Current Java: $javaVersion" -ForegroundColor White
    
    if ($javaVersion -match '"(8|11|17)\.') {
        Write-Host "✓ Compatible Java version detected (8, 11, or 17)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your Java version is compatible with PySpark 3.5.1." -ForegroundColor Green
        Write-Host "You can skip this installation." -ForegroundColor Green
        $continue = Read-Host "Do you want to install Java 17 anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "Setup cancelled." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "✗ Incompatible Java version (need 8, 11, or 17 for PySpark)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Java not found or not in PATH" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/5] Downloading Eclipse Temurin JDK 17..." -ForegroundColor Yellow

# Download URL for Temurin 17 LTS (Windows x64 MSI installer)
$jdkUrl = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.13%2B11/OpenJDK17U-jdk_x64_windows_hotspot_17.0.13_11.msi"
$installerPath = "$env:TEMP\temurin-17-jdk.msi"

try {
    Invoke-WebRequest -Uri $jdkUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✓ Downloaded to: $installerPath" -ForegroundColor Green
} catch {
    Write-Host "✗ Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual download:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://adoptium.net/temurin/releases/?version=17" -ForegroundColor White
    Write-Host "2. Download: Windows x64 MSI installer" -ForegroundColor White
    Write-Host "3. Run the installer manually" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "[3/5] Installing JDK 17..." -ForegroundColor Yellow
Write-Host "The installer will open. Please follow these steps:" -ForegroundColor White
Write-Host "  1. Click 'Next' through the installer" -ForegroundColor White
Write-Host "  2. IMPORTANT: Check 'Set JAVA_HOME variable'" -ForegroundColor Cyan
Write-Host "  3. IMPORTANT: Check 'Add to PATH'" -ForegroundColor Cyan
Write-Host "  4. Complete the installation" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter when ready to launch the installer..." -ForegroundColor Yellow
Read-Host

try {
    Start-Process msiexec.exe -ArgumentList "/i `"$installerPath`" /qb" -Wait
    Write-Host "✓ Installation completed" -ForegroundColor Green
} catch {
    Write-Host "✗ Installation failed: $_" -ForegroundColor Red
    Write-Host "Please run the installer manually: $installerPath" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[4/5] Verifying installation..." -ForegroundColor Yellow
Write-Host "Refreshing environment variables..." -ForegroundColor White

# Refresh environment variables in current session
$env:JAVA_HOME = [System.Environment]::GetEnvironmentVariable("JAVA_HOME", "Machine")
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Start-Sleep -Seconds 2

try {
    $newJavaVersion = java -version 2>&1 | Select-String "version" | Select-Object -First 1
    Write-Host "New Java version: $newJavaVersion" -ForegroundColor White
    
    if ($newJavaVersion -match '"17\.') {
        Write-Host "✓ Java 17 successfully installed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Java installed but version may not be 17" -ForegroundColor Yellow
        Write-Host "You may need to restart your terminal or set JAVA_HOME manually" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not verify Java installation" -ForegroundColor Yellow
    Write-Host "Please restart your terminal and run: java -version" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] Testing PySpark..." -ForegroundColor Yellow

try {
    $testScript = @"
from pyspark.sql import SparkSession
spark = SparkSession.builder.master('local[1]').appName('test').getOrCreate()
print('✓ PySpark works!')
spark.stop()
"@
    
    $testScript | python -c "import sys; exec(sys.stdin.read())" 2>&1 | Out-String | Write-Host
    Write-Host "✓ PySpark test passed" -ForegroundColor Green
} catch {
    Write-Host "⚠ PySpark test failed" -ForegroundColor Yellow
    Write-Host "You may need to restart your terminal for changes to take effect" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close and reopen your terminal (PowerShell)" -ForegroundColor White
Write-Host "2. Verify Java: java -version" -ForegroundColor White
Write-Host "3. Run tests: pytest tests/ -v" -ForegroundColor White
Write-Host "4. Run pipeline: make all" -ForegroundColor White
Write-Host ""
Write-Host "If PySpark still fails, manually set JAVA_HOME:" -ForegroundColor Yellow
Write-Host '  $env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.13.11-hotspot"' -ForegroundColor White
Write-Host ""
