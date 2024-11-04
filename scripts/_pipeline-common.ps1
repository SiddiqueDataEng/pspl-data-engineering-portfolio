# Dot-source from other scripts in this folder: . "$PSScriptRoot\_pipeline-common.ps1"
# Shared repo root, Python, Spark-on-Windows prep, DELTA_LAKE_PATH, and dbt path.

function Get-PipelineRepoRoot {
    return (Split-Path -Parent $PSScriptRoot)
}

function Get-PipelinePython {
    $root = Get-PipelineRepoRoot
    $venvPy = Join-Path $root ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPy) {
        return $venvPy
    }
    Write-Warning "No .venv found. Run: .\setup.ps1 -Python 'py -3.11'"
    return "python"
}

function Set-PipelinePySparkPython {
    param([string] $PythonExe)
    $env:PYSPARK_PYTHON = $PythonExe
    $env:PYSPARK_DRIVER_PYTHON = $PythonExe
}

function Get-PipelineDbtExe {
    $root = Get-PipelineRepoRoot
    $dbt = Join-Path $root ".venv\Scripts\dbt.exe"
    if (Test-Path -LiteralPath $dbt) {
        return $dbt
    }
    return "dbt"
}

function Set-PipelineDeltaLakeEnv {
    $root = Get-PipelineRepoRoot
    $env:DELTA_LAKE_PATH = (Join-Path $root "delta_lake").Replace("\", "/")
    Write-Host ("DELTA_LAKE_PATH: " + $env:DELTA_LAKE_PATH) -ForegroundColor DarkGray
}

function Set-PipelineJavaHomeIfUnset {
    if ($env:JAVA_HOME -and (Test-Path -LiteralPath $env:JAVA_HOME)) {
        return
    }
    $adopt = "C:\Program Files\Eclipse Adoptium"
    if (-not (Test-Path -LiteralPath $adopt)) {
        return
    }
    $jdk = Get-ChildItem -LiteralPath $adopt -Filter "jdk-17*" -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $jdk) {
        return
    }
    $env:JAVA_HOME = $jdk.FullName
    $bin = Join-Path $jdk.FullName "bin"
    $env:Path = $bin + ";" + $env:Path
    Write-Host ("JAVA_HOME set to " + $env:JAVA_HOME) -ForegroundColor Yellow
}

function Ensure-PipelineWinutils {
    if (-not $env:HADOOP_HOME) {
        $env:HADOOP_HOME = Join-Path $env:USERPROFILE "hadoop"
    }
    $binDir = Join-Path $env:HADOOP_HOME "bin"
    if (-not (Test-Path -LiteralPath $binDir)) {
        New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    }
    $winutils = Join-Path $binDir "winutils.exe"
    if (-not (Test-Path -LiteralPath $winutils)) {
        Write-Host "Downloading winutils.exe for local Spark..." -ForegroundColor Yellow
        $url = "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/winutils.exe"
        try {
            Invoke-WebRequest -Uri $url -OutFile $winutils -UseBasicParsing
        } catch {
            Write-Error ("Could not download winutils.exe from {0}: {1}" -f $url, $_)
            exit 1
        }
    }
    if (-not (Test-Path -LiteralPath $winutils)) {
        Write-Error "winutils.exe missing under $binDir. See https://github.com/cdarlint/winutils"
    }
    $env:Path = $binDir + ";" + $env:Path
    Write-Host ("HADOOP_HOME: " + $env:HADOOP_HOME) -ForegroundColor DarkGray
}

function Assert-PipelineJavaHome {
    <#
    .SYNOPSIS
      Fails fast if Spark cannot find a JDK (avoids opaque Py4JJavaError from PySpark).
    #>
    if ($env:JAVA_HOME -and (Test-Path -LiteralPath $env:JAVA_HOME)) {
        $javaExe = Join-Path $env:JAVA_HOME "bin\java.exe"
        if (Test-Path -LiteralPath $javaExe) {
            return
        }
    }
    Write-Error (
        "JAVA_HOME is missing or invalid. Install Eclipse Temurin JDK 17, set JAVA_HOME to the JDK folder " +
        "(e.g. C:\Program Files\Eclipse Adoptium\jdk-17.x.x-hotspot), add %JAVA_HOME%\bin to PATH, then retry. " +
        "Or run: .\setup_java17.ps1"
    )
    exit 1
}

function Initialize-PipelineSparkWindows {
    Set-PipelineJavaHomeIfUnset
    Assert-PipelineJavaHome
    Ensure-PipelineWinutils
}
