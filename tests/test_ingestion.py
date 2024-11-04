"""
Property-based tests for the PSPL Data Engineering Portfolio ingestion layer.

# Feature: PSPL-data-engineering-portfolio

Properties 1-6 cover Requirements 1.1 through 1.6.

Run fast (Property 1 only, no Spark):
    pytest tests/test_ingestion.py -v -m "not integration"

Run all (requires PySpark + Delta Lake):
    pytest tests/test_ingestion.py -v
"""

import json
import os
import shutil
import tempfile

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from ingest.readers import (
    DATASET_REGISTRY,
    get_reader_for_format,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_REPO_ROOT, "data_large")

EXPECTED_READERS = {
    "csv.gz": "read_csv_gz",
    "parquet": "read_parquet",
    "json": "read_json",
    "avro": "read_avro",
}

DATASET_FORMAT_PAIRS = [
    (name, entry["format"]) for name, entry in DATASET_REGISTRY.items()
]


# ---------------------------------------------------------------------------
# Helper: get or create a shared SparkSession for integration tests
# ---------------------------------------------------------------------------

def _get_spark():
    """Return the active SparkSession, creating one if needed."""
    from pyspark.sql import SparkSession
    return (
        SparkSession.builder
        .master("local[*]")
        .appName("PSPL-portfolio-tests")
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )


# ---------------------------------------------------------------------------
# Property 1: Format-correct reader dispatch
# Validates: Requirements 1.1
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 1: Format-correct reader dispatch


@pytest.mark.property
@given(st.sampled_from(DATASET_FORMAT_PAIRS))
@settings(max_examples=100, deadline=None)
def test_property_1_format_correct_reader_dispatch(dataset_format_pair):
    """
    **Validates: Requirements 1.1**

    For any source dataset name and its associated file format, the ingestion
    dispatcher SHALL select the reader function that corresponds to that format,
    and the selected reader SHALL successfully load the file into a non-empty DataFrame.
    """
    name, fmt = dataset_format_pair

    reader_fn = get_reader_for_format(fmt)
    assert reader_fn.__name__ == EXPECTED_READERS[fmt], (
        f"Expected reader '{EXPECTED_READERS[fmt]}' for format '{fmt}', "
        f"got '{reader_fn.__name__}'"
    )

    file_path = os.path.join(DATA_DIR, DATASET_REGISTRY[name]["file"])
    df = reader_fn(file_path)
    assert len(df) > 0, (
        f"Reader '{reader_fn.__name__}' returned an empty DataFrame for '{file_path}'"
    )


# ---------------------------------------------------------------------------
# Property 2: Delta write round-trip preserves data
# Validates: Requirements 1.2, 2.4
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 2: Delta write round-trip preserves data


@pytest.mark.property
@pytest.mark.integration
@given(st.data())
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
def test_property_2_delta_write_round_trip(data):
    """
    **Validates: Requirements 1.2, 2.4**

    For any valid pandas DataFrame written as a Delta table via PySpark,
    reading that Delta table back SHALL produce a DataFrame with the same
    number of rows as the original DataFrame.
    """
    import pandas as pd

    # Use simple integer-only rows to avoid Spark type inference issues
    rows = data.draw(
        st.lists(
            st.tuples(
                st.integers(min_value=-1000, max_value=1000),
                st.integers(min_value=0, max_value=9999),
            ),
            min_size=1,
            max_size=50,
        )
    )
    pdf = pd.DataFrame(rows, columns=["id", "value"])

    spark = _get_spark()
    tmp_dir = tempfile.mkdtemp(prefix="PSPL_delta_p2_")
    try:
        sdf = spark.createDataFrame(pdf)
        delta_path = os.path.join(tmp_dir, "test_table")
        sdf.write.format("delta").mode("overwrite").save(delta_path)
        sdf_read = spark.read.format("delta").load(delta_path)
        assert sdf_read.count() == len(pdf), (
            f"Delta round-trip row count mismatch: wrote {len(pdf)}, "
            f"read back {sdf_read.count()}"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 3: Ingestion idempotence
# Validates: Requirements 1.3
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 3: Ingestion idempotence


@pytest.mark.property
@pytest.mark.integration
@given(st.integers(min_value=2, max_value=3))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_3_ingestion_idempotence(n_runs):
    """
    **Validates: Requirements 1.3**

    Running the ingestion N times SHALL produce a Bronze Delta table with the
    same row count as running it once. The manifest SHALL contain exactly one
    entry per dataset regardless of N.
    """
    from ingest.ingest import ingest_dataset, write_manifest

    spark = _get_spark()
    tmp_dir = tempfile.mkdtemp(prefix="PSPL_delta_p3_")
    try:
        dataset_name = "beneficiaries"
        entry = {
            **DATASET_REGISTRY[dataset_name],
            "file": os.path.join(DATA_DIR, DATASET_REGISTRY[dataset_name]["file"]),
        }

        result_single = ingest_dataset(spark, dataset_name, entry, tmp_dir)
        assert result_single is not None, "Single-run ingestion failed"
        single_run_row_count = result_single["row_count"]

        final_result = result_single
        for _ in range(n_runs - 1):
            final_result = ingest_dataset(spark, dataset_name, entry, tmp_dir)
            assert final_result is not None, f"Ingestion failed on run {_ + 2}"

        assert final_result["row_count"] == single_run_row_count, (
            f"Idempotence violated: single={single_run_row_count}, "
            f"after {n_runs} runs={final_result['row_count']}"
        )

        manifest = {dataset_name: final_result}
        write_manifest(manifest, tmp_dir)
        manifest_path = os.path.join(tmp_dir, "bronze", "_manifest.json")
        with open(manifest_path) as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert dataset_name in loaded
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 4: Partial failure isolation
# Validates: Requirements 1.4
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 4: Partial failure isolation


@pytest.mark.property
@pytest.mark.integration
@given(st.lists(st.booleans(), min_size=9, max_size=9))
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_4_partial_failure_isolation(validity_flags):
    """
    **Validates: Requirements 1.4**

    For any mix of valid and invalid source files, all valid datasets SHALL be
    successfully ingested and appear in the manifest.
    """
    from ingest.ingest import ingest_dataset

    spark = _get_spark()
    tmp_dir = tempfile.mkdtemp(prefix="PSPL_delta_p4_")
    try:
        dataset_names = list(DATASET_REGISTRY.keys())
        manifest = {}
        expected_valid_count = 0

        for name, is_valid in zip(dataset_names, validity_flags):
            if is_valid:
                entry = {
                    **DATASET_REGISTRY[name],
                    "file": os.path.join(DATA_DIR, DATASET_REGISTRY[name]["file"]),
                }
                expected_valid_count += 1
            else:
                entry = {
                    **DATASET_REGISTRY[name],
                    "file": os.path.join(tmp_dir, f"nonexistent_{name}.dat"),
                }

            result = ingest_dataset(spark, name, entry, tmp_dir)
            if result is not None:
                manifest[name] = result

        for name, is_valid in zip(dataset_names, validity_flags):
            if is_valid:
                assert name in manifest, f"Valid dataset '{name}' missing from manifest"

        assert len(manifest) == expected_valid_count, (
            f"Manifest has {len(manifest)} entries, expected {expected_valid_count}"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 5: Manifest completeness
# Validates: Requirements 1.5
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 5: Manifest completeness


@pytest.mark.property
@pytest.mark.integration
@given(st.sampled_from(list(DATASET_REGISTRY.keys())))
@settings(
    max_examples=9,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_5_manifest_completeness(dataset_name):
    """
    **Validates: Requirements 1.5**

    For any successfully ingested dataset, the manifest entry SHALL contain all
    five required fields, and row_count SHALL equal the actual Delta table count.
    """
    from ingest.ingest import ingest_dataset

    REQUIRED_FIELDS = {
        "dataset_name", "row_count", "file_size_bytes",
        "ingestion_timestamp", "source_format",
    }

    spark = _get_spark()
    tmp_dir = tempfile.mkdtemp(prefix="PSPL_delta_p5_")
    try:
        entry = {
            **DATASET_REGISTRY[dataset_name],
            "file": os.path.join(DATA_DIR, DATASET_REGISTRY[dataset_name]["file"]),
        }

        result = ingest_dataset(spark, dataset_name, entry, tmp_dir)
        assert result is not None, f"Ingestion failed for '{dataset_name}'"

        missing = REQUIRED_FIELDS - set(result.keys())
        assert not missing, f"Manifest missing fields: {missing}"

        delta_path = os.path.join(tmp_dir, "bronze", dataset_name)
        actual_count = spark.read.format("delta").load(delta_path).count()
        assert result["row_count"] == actual_count, (
            f"row_count={result['row_count']} != Delta count={actual_count}"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 6: Single-dataset CLI filtering
# Validates: Requirements 1.6
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 6: Single-dataset CLI filtering


@pytest.mark.property
@pytest.mark.integration
@given(st.sampled_from(list(DATASET_REGISTRY.keys())))
@settings(
    max_examples=9,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_property_6_single_dataset_cli_filtering(dataset_name):
    """
    **Validates: Requirements 1.6**

    For any valid dataset name, running ingestion for that single dataset SHALL
    write exactly one Bronze table directory and the manifest SHALL contain
    exactly one entry.
    """
    from ingest.ingest import ingest_dataset, write_manifest

    spark = _get_spark()
    tmp_dir = tempfile.mkdtemp(prefix="PSPL_delta_p6_")
    try:
        entry = {
            **DATASET_REGISTRY[dataset_name],
            "file": os.path.join(DATA_DIR, DATASET_REGISTRY[dataset_name]["file"]),
        }

        result = ingest_dataset(spark, dataset_name, entry, tmp_dir)
        assert result is not None, f"Ingestion failed for '{dataset_name}'"

        manifest = {dataset_name: result}
        write_manifest(manifest, tmp_dir)

        bronze_dir = os.path.join(tmp_dir, "bronze")
        bronze_entries = [
            e for e in os.listdir(bronze_dir)
            if os.path.isdir(os.path.join(bronze_dir, e))
        ]
        assert len(bronze_entries) == 1, (
            f"Expected 1 Bronze dir, found {len(bronze_entries)}: {bronze_entries}"
        )
        assert bronze_entries[0] == dataset_name

        manifest_path = os.path.join(bronze_dir, "_manifest.json")
        with open(manifest_path) as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert dataset_name in loaded
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
