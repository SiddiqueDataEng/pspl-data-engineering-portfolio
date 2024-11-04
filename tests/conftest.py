"""
Shared pytest fixtures for the PSPL Data Engineering Portfolio test suite.
"""

import os
import shutil
import tempfile

import duckdb
import pytest

# ---------------------------------------------------------------------------
# Windows PySpark environment setup
# Set HADOOP_HOME and JAVA_HOME before any SparkSession is created.
# PySpark on Windows requires winutils.exe in %HADOOP_HOME%\bin.
# ---------------------------------------------------------------------------

def _configure_pyspark_env() -> None:
    """Ensure JAVA_HOME and HADOOP_HOME are set for PySpark on Windows."""
    import platform
    if platform.system() != "Windows":
        return

    # JAVA_HOME: prefer the env var already set; fall back to Temurin 17
    if not os.environ.get("JAVA_HOME"):
        temurin_base = r"C:\Program Files\Eclipse Adoptium"
        if os.path.isdir(temurin_base):
            candidates = sorted(
                [d for d in os.listdir(temurin_base) if d.startswith("jdk-17")],
                reverse=True,
            )
            if candidates:
                os.environ["JAVA_HOME"] = os.path.join(temurin_base, candidates[0])

    # HADOOP_HOME: prefer the env var already set; fall back to ~/hadoop
    if not os.environ.get("HADOOP_HOME"):
        default_hadoop = os.path.join(os.path.expanduser("~"), "hadoop")
        if os.path.isdir(default_hadoop):
            os.environ["HADOOP_HOME"] = default_hadoop

    # Ensure %JAVA_HOME%\bin and %HADOOP_HOME%\bin are on PATH
    java_home = os.environ.get("JAVA_HOME", "")
    hadoop_home = os.environ.get("HADOOP_HOME", "")
    path_parts = os.environ.get("PATH", "").split(os.pathsep)

    prepend = []
    if java_home and os.path.join(java_home, "bin") not in path_parts:
        prepend.append(os.path.join(java_home, "bin"))
    if hadoop_home and os.path.join(hadoop_home, "bin") not in path_parts:
        prepend.append(os.path.join(hadoop_home, "bin"))

    if prepend:
        os.environ["PATH"] = os.pathsep.join(prepend + path_parts)


_configure_pyspark_env()


# ---------------------------------------------------------------------------
# SparkSession fixture (session-scoped — one Spark instance per test run)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def spark():
    """
    Create a local SparkSession configured for Delta Lake.

    Uses the same configuration as ``ingest.ingest.build_spark_session()``:
    - Maven package: io.delta:delta-spark_2.12:3.2.0
    - Delta SQL extensions enabled
    - DeltaCatalog registered as the default catalog

    Yields the session and stops it after the entire test session completes.
    """
    from pyspark.sql import SparkSession

    DELTA_PACKAGE = "io.delta:delta-spark_2.12:3.2.0"

    session = (
        SparkSession.builder
        .master("local[*]")
        .appName("PSPL-portfolio-tests")
        .config("spark.jars.packages", DELTA_PACKAGE)
        .config(
            "spark.sql.extensions",
            "io.delta.sql.DeltaSparkSessionExtension",
        )
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("WARN")

    yield session

    session.stop()


# ---------------------------------------------------------------------------
# Temporary Delta path fixture (function-scoped — fresh dir per test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def tmp_delta_path():
    """
    Create a temporary directory for Delta table writes.

    Yields the directory path as a string and removes the directory
    (and all its contents) after each test.
    """
    tmp_dir = tempfile.mkdtemp(prefix="PSPL_delta_test_")
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# DuckDB in-memory connection fixture (function-scoped — fresh conn per test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def duckdb_conn():
    """
    Create an in-memory DuckDB connection.

    Yields the connection and closes it after each test.
    """
    conn = duckdb.connect(database=":memory:")
    yield conn
    conn.close()
