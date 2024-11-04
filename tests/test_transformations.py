"""
Property-based tests for the PSPL Data Engineering Portfolio transformation layer.

# Feature: PSPL-data-engineering-portfolio

Properties 7-8 cover Requirements 2.3 and 2.7.

Run (requires PySpark):
    pytest tests/test_transformations.py -v

Skip slow integration tests:
    pytest tests/test_transformations.py -v -m "not integration"
"""

import sys

import pandas as pd
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import Phase
import hypothesis.strategies as st
from pyspark.sql.types import StringType, StructField, StructType

from ingest.transforms import clean_dataframe


# ---------------------------------------------------------------------------
# Helper: get or create a shared SparkSession
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


# Explicit schema for 3-column string DataFrames.
_SCHEMA_3COL = StructType([
    StructField("col_a", StringType(), nullable=True),
    StructField("col_b", StringType(), nullable=True),
    StructField("col_c", StringType(), nullable=True),
])

_SCHEMA_2COL = StructType([
    StructField("col_a", StringType(), nullable=True),
    StructField("col_b", StringType(), nullable=True),
])


# ---------------------------------------------------------------------------
# Shared strategies — use printable ASCII only to avoid cloudpickle issues
# with exotic Unicode on Python 3.14.  No None values: we inject empty
# strings explicitly in the test body so we control the setup.
# ---------------------------------------------------------------------------

_safe_text = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=20,
)

# 3-column row strategy (for Property 7)
_string_row_3col = st.fixed_dictionaries(
    {
        "col_a": _safe_text,
        "col_b": _safe_text,
        "col_c": _safe_text,
    }
)
_string_df_3col = st.lists(_string_row_3col, min_size=1, max_size=50).map(
    lambda rows: pd.DataFrame(rows, columns=["col_a", "col_b", "col_c"])
)

# 2-column row strategy (for Property 8)
_string_row_2col = st.fixed_dictionaries(
    {
        "col_a": _safe_text,
        "col_b": _safe_text,
    }
)
_string_df_2col = st.lists(_string_row_2col, min_size=1, max_size=100).map(
    lambda rows: pd.DataFrame(rows, columns=["col_a", "col_b"])
)


def _pdf_to_spark(spark, pdf, schema):
    """Convert a pandas DataFrame to a PySpark DataFrame via createDataFrame
    using a list of Row tuples rather than the pandas path.

    The pandas→Spark path goes through PySpark's RDD serializer (cloudpickle),
    which overflows the stack on Python 3.14 when the test-function closure is
    large.  Passing plain Python tuples uses the JVM-side Row constructor
    directly and avoids cloudpickle entirely.
    """
    from pyspark.sql import Row
    rows = [tuple(r) for r in pdf.itertuples(index=False, name=None)]
    return spark.createDataFrame(rows, schema=schema)


# ---------------------------------------------------------------------------
# Property 7: Cleaning invariants
# Validates: Requirements 2.3
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 7: Cleaning invariants


@pytest.mark.property
@pytest.mark.integration
@given(data=st.data())
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    phases=[Phase.explicit, Phase.reuse, Phase.generate],
)
def test_property_7_cleaning_invariants(data):
    """
    **Validates: Requirements 2.3**

    For any Bronze DataFrame after applying the Silver cleaning function:
    (a) no fully duplicate rows SHALL exist,
    (b) no empty string values SHALL exist in any column,
    (c) row count after cleaning is <= row count before cleaning.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.types import StringType

    pdf = data.draw(_string_df_3col)

    # Inject duplicate rows
    duplicate_rows = pdf.iloc[[0] * min(3, len(pdf))]
    pdf = pd.concat([pdf, duplicate_rows], ignore_index=True)

    # Inject empty strings into string columns
    for col in pdf.columns:
        if pdf[col].dtype == object:
            mask = pdf[col].notna()
            n_to_replace = max(1, int(mask.sum() * 0.2)) if mask.sum() > 0 else 0
            if n_to_replace > 0:
                indices = pdf[mask].sample(n=n_to_replace, random_state=42).index
                pdf.loc[indices, col] = ""

    spark = _get_spark()
    # Use tuple-based createDataFrame to avoid cloudpickle recursion on
    # Python 3.14 (the pandas→RDD path serializes the test-function closure).
    sdf = _pdf_to_spark(spark, pdf, _SCHEMA_3COL)
    row_count_before = sdf.count()

    cleaned_sdf = clean_dataframe(sdf)
    row_count_after = cleaned_sdf.count()

    # (c) Row count after cleaning <= before
    assert row_count_after <= row_count_before, (
        f"Cleaning increased row count: before={row_count_before}, after={row_count_after}"
    )

    # (b) No empty strings remain
    string_cols = [
        field.name for field in cleaned_sdf.schema.fields
        if isinstance(field.dataType, StringType)
    ]
    for col_name in string_cols:
        empty_count = cleaned_sdf.filter(F.col(col_name) == "").count()
        assert empty_count == 0, (
            f"Column '{col_name}' still has {empty_count} empty string(s) after cleaning"
        )

    # (a) No duplicate rows remain
    deduped_count = cleaned_sdf.dropDuplicates().count()
    assert deduped_count == row_count_after, (
        f"Duplicate rows remain: cleaned={row_count_after}, distinct={deduped_count}"
    )


# ---------------------------------------------------------------------------
# Property 8: Silver row count monotonicity
# Validates: Requirements 2.7
# ---------------------------------------------------------------------------

# Feature: PSPL-data-engineering-portfolio, Property 8: Silver row count monotonicity


@pytest.mark.property
@pytest.mark.integration
@given(data=st.data())
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    phases=[Phase.explicit, Phase.reuse, Phase.generate],
)
def test_property_8_silver_row_count_monotonicity(data):
    """
    **Validates: Requirements 2.7**

    For any Bronze DataFrame, the Silver row count SHALL be <= the Bronze row count.
    Cleaning only removes rows via deduplication, never adds rows.
    """
    pdf = data.draw(_string_df_2col)

    # Inject ~20% duplicates
    n_dupes = max(1, len(pdf) // 5)
    dupe_rows = pdf.sample(n=n_dupes, replace=True, random_state=0)
    pdf = pd.concat([pdf, dupe_rows], ignore_index=True)

    spark = _get_spark()
    # Use tuple-based createDataFrame to avoid cloudpickle recursion on
    # Python 3.14 (the pandas→RDD path serializes the test-function closure).
    sdf = _pdf_to_spark(spark, pdf, _SCHEMA_2COL)
    bronze_count = sdf.count()

    silver_sdf = clean_dataframe(sdf)
    silver_count = silver_sdf.count()

    assert silver_count <= bronze_count, (
        f"Silver count ({silver_count}) > Bronze count ({bronze_count}). "
        f"Cleaning must never add rows."
    )
