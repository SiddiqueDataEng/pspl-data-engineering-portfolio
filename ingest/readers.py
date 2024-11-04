"""
Format-specific reader functions for the PSPL Data Engineering Portfolio.

Each reader accepts a file path and returns a pandas DataFrame.
The DATASET_REGISTRY maps dataset names to their file, format, and reader function.
"""

import pandas as pd
import pyarrow.parquet as pq
import fastavro


def read_csv_gz(path: str) -> pd.DataFrame:
    """Read a gzip-compressed CSV file into a pandas DataFrame."""
    return pd.read_csv(path, compression="gzip")


def read_parquet(path: str) -> pd.DataFrame:
    """Read a Parquet file into a pandas DataFrame via pyarrow."""
    return pq.read_table(path).to_pandas()


def read_json(path: str) -> pd.DataFrame:
    """Read a newline-delimited JSON file into a pandas DataFrame."""
    return pd.read_json(path, lines=True)


def read_avro(path: str) -> pd.DataFrame:
    """Read an Avro file into a pandas DataFrame via fastavro."""
    with open(path, "rb") as f:
        reader = fastavro.reader(f)
        records = list(reader)
    return pd.DataFrame(records)


# Mapping from format string to reader function
_FORMAT_READERS = {
    "csv.gz": read_csv_gz,
    "parquet": read_parquet,
    "json": read_json,
    "avro": read_avro,
}


def get_reader_for_format(fmt: str):
    """
    Return the reader function for the given format string.

    Supported formats: 'csv.gz', 'parquet', 'json', 'avro'

    Raises:
        ValueError: If the format is not recognised.
    """
    if fmt not in _FORMAT_READERS:
        raise ValueError(
            f"Unknown format '{fmt}'. Supported formats: {sorted(_FORMAT_READERS)}"
        )
    return _FORMAT_READERS[fmt]


# Registry of all 9 datasets.
# Each entry maps a dataset name to:
#   file       — filename inside data_large/
#   format     — format string used by get_reader_for_format()
#   reader_fn  — the actual reader function reference
DATASET_REGISTRY = {
    "beneficiaries": {
        "file": "beneficiaries.csv.gz",
        "format": "csv.gz",
        "reader_fn": read_csv_gz,
    },
    "payments": {
        "file": "payments.parquet",
        "format": "parquet",
        "reader_fn": read_parquet,
    },
    "surveys": {
        "file": "surveys.json",
        "format": "json",
        "reader_fn": read_json,
    },
    "inventory": {
        "file": "inventory.avro",
        "format": "avro",
        "reader_fn": read_avro,
    },
    "complaints": {
        "file": "complaints.csv.gz",
        "format": "csv.gz",
        "reader_fn": read_csv_gz,
    },
    "donor_reports": {
        "file": "donor_reports.parquet",
        "format": "parquet",
        "reader_fn": read_parquet,
    },
    "afghan_refugees": {
        "file": "afghan_refugees.json",
        "format": "json",
        "reader_fn": read_json,
    },
    "refugee_assistance": {
        "file": "refugee_assistance.avro",
        "format": "avro",
        "reader_fn": read_avro,
    },
    "refugee_protection": {
        "file": "refugee_protection.csv.gz",
        "format": "csv.gz",
        "reader_fn": read_csv_gz,
    },
}
