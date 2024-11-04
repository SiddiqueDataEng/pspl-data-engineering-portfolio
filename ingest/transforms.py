"""
PySpark transformation utilities for the PSPL Data Engineering Portfolio.

This module provides the ``clean_dataframe`` function used in the Bronze→Silver
cleaning step. Extracting it here makes it importable by the test suite
(tests/test_transformations.py) without executing the full notebook.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StringType,
    DateType,
    TimestampType,
    BooleanType,
    IntegerType,
    LongType,
    DoubleType,
)


def clean_dataframe(sdf: DataFrame) -> DataFrame:
    """
    Apply generic Silver-layer cleaning to a PySpark DataFrame.

    Steps applied in order:
    1. Drop fully duplicate rows via ``dropDuplicates()``.
    2. Replace empty strings (``''``) with ``null`` for every STRING column.
    3. Cast columns to their correct Silver types where the column name matches
       a known pattern (dates, booleans, numerics).  Integral ``survey_date`` /
       ``*_date`` / ``registration_date`` / etc. values from JSON are treated as
       **Unix epoch milliseconds** (pandas → Spark often infers BIGINT).  Columns
       that do not match any pattern are left unchanged.

    The type-cast rules are intentionally generic so the function works on any
    of the nine Bronze DataFrames without requiring a per-dataset schema dict.

    Parameters
    ----------
    sdf:
        Input PySpark DataFrame (typically a Bronze Delta table).

    Returns
    -------
    DataFrame
        Cleaned PySpark DataFrame ready for Silver write.
    """
    # ------------------------------------------------------------------
    # Step 1 — drop fully duplicate rows
    # ------------------------------------------------------------------
    sdf = sdf.dropDuplicates()

    # ------------------------------------------------------------------
    # Step 2 — replace empty strings with null in all STRING columns
    # ------------------------------------------------------------------
    string_cols = [
        field.name
        for field in sdf.schema.fields
        if isinstance(field.dataType, StringType)
    ]
    for col_name in string_cols:
        sdf = sdf.withColumn(
            col_name,
            F.when(F.col(col_name) == "", None).otherwise(F.col(col_name)),
        )

    # ------------------------------------------------------------------
    # Step 3 — cast columns to correct Silver types by name pattern
    # ------------------------------------------------------------------
    # Date columns: any column whose name ends with _date or equals
    # registration_date, last_payment_date, last_verification, disbursement_date
    date_suffixes = ("_date", "_verification")
    date_exact = {"registration_date", "last_payment_date", "last_verification",
                  "disbursement_date"}

    # Timestamp columns
    timestamp_exact = {"last_updated"}

    # Boolean columns
    boolean_exact = {"is_eligible", "is_disabled", "is_unaccompanied_minor",
                     "has_disability"}

    # Integer columns
    integer_exact = {"quantity", "reorder_level", "metric_value"}

    # Long / BIGINT columns
    long_exact = {"amount"}

    # Double columns
    double_exact = {"poverty_score", "vulnerability_score",
                    "amount_committed", "amount_disbursed",
                    "amount_usd", "amount_pkr"}

    for field in sdf.schema.fields:
        col_name = field.name
        current_type = type(field.dataType)

        # Determine target type
        target_type = None

        if col_name in date_exact or any(col_name.endswith(s) for s in date_suffixes):
            if current_type not in (DateType,):
                target_type = DateType()
        elif col_name in timestamp_exact:
            if current_type not in (TimestampType,):
                target_type = TimestampType()
        elif col_name in boolean_exact:
            if current_type not in (BooleanType,):
                target_type = BooleanType()
        elif col_name in integer_exact:
            if current_type not in (IntegerType,):
                target_type = IntegerType()
        elif col_name in long_exact:
            if current_type not in (LongType,):
                target_type = LongType()
        elif col_name in double_exact:
            if current_type not in (DoubleType,):
                target_type = DoubleType()

        if target_type is not None:
            if isinstance(field.dataType, (LongType, IntegerType)):
                if isinstance(target_type, DateType):
                    # Epoch milliseconds (common for JSON → pandas → Spark BIGINT)
                    secs = F.col(col_name).cast("double") / F.lit(1000.0)
                    sdf = sdf.withColumn(col_name, F.to_date(F.from_unixtime(secs)))
                    continue
                if isinstance(target_type, TimestampType):
                    sdf = sdf.withColumn(
                        col_name,
                        F.to_timestamp(F.col(col_name).cast("double") / F.lit(1000.0)),
                    )
                    continue
            sdf = sdf.withColumn(col_name, F.col(col_name).cast(target_type))

    return sdf
