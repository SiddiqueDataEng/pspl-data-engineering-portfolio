"""
Main ingestion script for the PSPL Data Engineering Portfolio.

Reads nine source datasets using format-specific Python readers (pandas/pyarrow/fastavro),
converts each to a PySpark DataFrame, and writes Bronze Delta tables.

Usage:
    python ingest/ingest.py [--dataset DATASET_NAME] [--data-dir PATH] [--delta-dir PATH]

On Windows, prefer the wrapper so Java, HADOOP_HOME, and winutils are set::

    .\\scripts\\run-ingest.ps1

Raw ``python ingest/ingest.py`` validates Java and, on Windows, defaults
``HADOOP_HOME`` to ``%USERPROFILE%\\hadoop`` and downloads ``winutils.exe`` when missing
(same behaviour as ``run-ingest.ps1``). Use Python 3.10-3.12 from ``.venv``.
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Ensure the ingest package is importable when run as a script from any cwd
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from ingest.readers import DATASET_REGISTRY, get_reader_for_format  # noqa: E402
from ingest.spark_preflight import (  # noqa: E402
    ensure_pyspark_uses_current_interpreter,
    validate_local_spark_prerequisites,
    warn_if_unsupported_python,
)
from ingest.spark_runtime_paths import configure_spark_local_dirs, stop_spark_quietly  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


# ---------------------------------------------------------------------------
# SparkSession
# ---------------------------------------------------------------------------

def build_spark_session():
    """
    Create and return a local SparkSession configured for Delta Lake.

    The Maven package ``io.delta:delta-spark_2.12:3.2.0`` is fetched
    automatically by Spark on first run.
    """
    validate_local_spark_prerequisites()
    py_exe = ensure_pyspark_uses_current_interpreter()
    logger.info("PySpark workers will use: %s", py_exe)

    try:
        from py4j.protocol import Py4JJavaError
    except ImportError:
        Py4JJavaError = Exception  # type: ignore[misc, assignment]

    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise RuntimeError(
            "PySpark is not installed. Activate the project .venv "
            "(see setup.ps1) and install requirements.txt."
        ) from exc

    DELTA_PACKAGE = "io.delta:delta-spark_2.12:3.2.0"

    try:
        bldr = (
            SparkSession.builder
            .master("local[2]")
            .appName("PSPL-bronze-ingest")
            .config("spark.pyspark.python", py_exe)
            .config("spark.pyspark.driver.python", py_exe)
            .config("spark.jars.packages", DELTA_PACKAGE)
            .config(
                "spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension",
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
        )
        spark = configure_spark_local_dirs(bldr, _PARENT_DIR).getOrCreate()
    except Py4JJavaError as exc:
        cause = getattr(exc, "java_exception", None)
        detail = str(cause) if cause is not None else str(exc)
        raise RuntimeError(
            "Spark failed to start the JVM (JavaSparkContext). "
            "Typical fixes: install JDK 17, set JAVA_HOME, on Windows set HADOOP_HOME + "
            "winutils (use .\\scripts\\run-ingest.ps1), use Python 3.10-3.12. "
            f"Underlying Java error: {detail}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Unexpected error while creating SparkSession. "
            "See traceback in logs; verify Java, PySpark version, and network for Maven jars."
        ) from exc

    spark.sparkContext.setLogLevel("WARN")
    return spark


# ---------------------------------------------------------------------------
# DataFrame helpers
# ---------------------------------------------------------------------------

def pandas_to_spark(spark, pdf):
    """Convert a pandas DataFrame to a PySpark DataFrame."""
    return spark.createDataFrame(pdf)


def write_bronze(sdf, name: str, delta_dir: str) -> None:
    """
    Write *sdf* as a Delta table to ``{delta_dir}/bronze/{name}/``.

    Uses overwrite mode so the operation is idempotent.
    """
    path = os.path.join(delta_dir, "bronze", name)
    (
        sdf.write
        .format("delta")
        .mode("overwrite")
        .save(path)
    )
    logger.info("Wrote Bronze Delta table → %s", path)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def write_manifest(manifest_dict: dict, delta_dir: str) -> None:
    """Serialise *manifest_dict* to ``{delta_dir}/bronze/_manifest.json``."""
    manifest_path = os.path.join(delta_dir, "bronze", "_manifest.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest_dict, fh, indent=2, default=str)
    logger.info("Manifest written → %s", manifest_path)


# ---------------------------------------------------------------------------
# Per-dataset ingestion
# ---------------------------------------------------------------------------

def ingest_dataset(spark, name: str, registry_entry: dict, delta_dir: str) -> dict | None:
    """
    Ingest a single dataset and write it as a Bronze Delta table.

    Parameters
    ----------
    spark:
        Active SparkSession.
    name:
        Dataset name (key in DATASET_REGISTRY).
    registry_entry:
        Dict with keys ``file``, ``format``, ``reader_fn``.
    delta_dir:
        Root directory for Delta tables (e.g. ``delta_lake/``).

    Returns
    -------
    dict | None
        Manifest entry on success, or ``None`` on failure (error logged to stderr).
    """
    try:
        file_path = registry_entry["file"]  # already the full path (set by main)
        fmt = registry_entry["format"]
        reader_fn = get_reader_for_format(fmt)

        logger.info("Reading %s from %s …", name, file_path)
        pdf = reader_fn(file_path)

        row_count = len(pdf)
        file_size_bytes = os.path.getsize(file_path)

        logger.info("Converting %s (%d rows) to Spark DataFrame …", name, row_count)
        sdf = pandas_to_spark(spark, pdf)

        write_bronze(sdf, name, delta_dir)

        return {
            "dataset_name": name,
            "row_count": row_count,
            "file_size_bytes": file_size_bytes,
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_format": fmt,
        }

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Ingest failed for dataset %s (%s)",
            name,
            registry_entry.get("file", "unknown"),
        )
        return None


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    warn_if_unsupported_python(logger)
    if sys.version_info >= (3, 14):
        venv_py = os.path.join(_PARENT_DIR, ".venv", "Scripts", "python.exe")
        if sys.platform != "win32":
            venv_py = os.path.join(_PARENT_DIR, ".venv", "bin", "python")
        print(
            "ERROR: This interpreter is Python 3.14+, which PySpark in this project does not support.\n"
            f"  You ran: {sys.executable}\n"
            "  Do one of the following:\n"
            f"  1) Use the project venv (after setup): \"{venv_py}\" ingest/ingest.py\n"
            "  2) Windows: .\\scripts\\run-ingest.ps1   (sets Java + Spark paths; use Bypass if scripts are blocked)\n"
            "  3) Recreate .venv with 3.11: Set-ExecutionPolicy -Scope Process Bypass; "
            ".\\setup.ps1 -Force -Python 'py -3.11'",
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Ingest PSPL source datasets into Bronze Delta tables.",
    )
    parser.add_argument(
        "--dataset",
        metavar="DATASET_NAME",
        default=None,
        help="Ingest a single named dataset (default: all datasets).",
    )
    parser.add_argument(
        "--data-dir",
        default="data_large/",
        metavar="PATH",
        help="Directory containing source data files (default: data_large/).",
    )
    parser.add_argument(
        "--delta-dir",
        default="delta_lake/",
        metavar="PATH",
        help="Root directory for Delta Lake output (default: delta_lake/).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Validate --data-dir exists
    # ------------------------------------------------------------------
    if not os.path.isdir(args.data_dir):
        print(
            f"ERROR: data directory '{args.data_dir}' does not exist.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Validate --dataset if provided
    # ------------------------------------------------------------------
    if args.dataset is not None and args.dataset not in DATASET_REGISTRY:
        known = ", ".join(sorted(DATASET_REGISTRY.keys()))
        print(
            f"usage error: unknown dataset '{args.dataset}'. "
            f"Known datasets: {known}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Build the list of datasets to process
    # ------------------------------------------------------------------
    if args.dataset:
        datasets_to_run = {args.dataset: DATASET_REGISTRY[args.dataset]}
    else:
        datasets_to_run = dict(DATASET_REGISTRY)

    # Resolve full file paths now (registry stores bare filenames)
    resolved_registry = {}
    for name, entry in datasets_to_run.items():
        resolved_registry[name] = {
            **entry,
            "file": os.path.join(args.data_dir, entry["file"]),
        }

    missing_files = [
        (n, e["file"])
        for n, e in resolved_registry.items()
        if not os.path.isfile(e["file"])
    ]
    if missing_files:
        for n, fp in missing_files:
            print(f"ERROR: missing source file for '{n}': {fp}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Build SparkSession
    # ------------------------------------------------------------------
    spark = None
    try:
        logger.info("Initialising SparkSession …")
        try:
            spark = build_spark_session()
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        # ------------------------------------------------------------------
        # Ingest each dataset
        # ------------------------------------------------------------------
        manifest: dict = {}
        for name, entry in resolved_registry.items():
            result = ingest_dataset(spark, name, entry, args.delta_dir)
            if result is not None:
                manifest[name] = result

        # ------------------------------------------------------------------
        # Write manifest
        # ------------------------------------------------------------------
        write_manifest(manifest, args.delta_dir)

        expected = len(resolved_registry)
        got = len(manifest)
        logger.info("Done. %d/%d datasets ingested.", got, expected)

        if got < expected:
            missing = sorted(set(resolved_registry) - set(manifest))
            print(
                f"ERROR: incomplete ingest ({got}/{expected}). Failed: {', '.join(missing)}",
                file=sys.stderr,
            )
            sys.exit(2)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception:
        print("FATAL: unhandled exception during ingest:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    finally:
        if spark is not None:
            stop_spark_quietly(spark, logger=logger)


if __name__ == "__main__":
    main()
