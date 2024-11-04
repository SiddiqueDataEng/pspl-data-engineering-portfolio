# Ingestion Pipeline Runbook

This runbook covers how to run the Bronze ingestion pipeline end-to-end, ingest individual datasets, verify output, and recover from failures.

**Validates: Requirements 5.5**

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Check with `python --version` |
| Java | 11+ | Required by PySpark/Delta Lake; check with `java -version` |
| pip dependencies | — | See `requirements.txt` |

Install Python dependencies from the repo root:

```bash
pip install -r requirements.txt
```

> On first run, PySpark will automatically download the Delta Lake Maven package (`io.delta:delta-spark_2.12:3.2.0`) from Maven Central. This requires an internet connection and may take a minute.

---

## Environment Setup

### JAVA_HOME

PySpark requires `JAVA_HOME` to point to a Java 11+ installation.

**macOS / Linux:**

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 11)   # macOS with java_home utility
# or set it explicitly:
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64  # Debian/Ubuntu example
```

**Windows (PowerShell):**

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-11.0.x-hotspot"
```

Verify the setting:

```bash
echo $JAVA_HOME
java -version
```

### DELTA_LAKE_PATH

`DELTA_LAKE_PATH` controls where Bronze Delta tables are written. The script defaults to `delta_lake/` relative to the working directory, but you can override it:

```bash
export DELTA_LAKE_PATH=/path/to/your/delta_lake   # optional override
```

When using the default, run the script from the repository root so that `delta_lake/` resolves correctly.

---

## Running the Full Ingestion

From the repository root, run:

```bash
python ingest/ingest.py
```

This reads all nine source files from `data_large/` and writes Bronze Delta tables to `delta_lake/bronze/`. Progress is logged to stderr. A successful run ends with a line like:

```
INFO ingest.ingest — Done. 9/9 datasets ingested.
```

### Optional flags

| Flag | Default | Description |
|---|---|---|
| `--data-dir PATH` | `data_large/` | Directory containing source files |
| `--delta-dir PATH` | `delta_lake/` | Root directory for Delta Lake output |
| `--dataset NAME` | *(all)* | Ingest a single named dataset |

Example with explicit paths:

```bash
python ingest/ingest.py --data-dir /mnt/data/PSPL --delta-dir /mnt/delta
```

---

## Running a Single-Dataset Ingestion

Use `--dataset` to ingest one dataset without touching the others:

```bash
python ingest/ingest.py --dataset beneficiaries
```

Valid dataset names (must match exactly):

| Name | Source file | Format |
|---|---|---|
| `beneficiaries` | `beneficiaries.csv.gz` | CSV (gzip) |
| `payments` | `payments.parquet` | Parquet |
| `surveys` | `surveys.json` | JSON (newline-delimited) |
| `inventory` | `inventory.avro` | Avro |
| `complaints` | `complaints.csv.gz` | CSV (gzip) |
| `donor_reports` | `donor_reports.parquet` | Parquet |
| `afghan_refugees` | `afghan_refugees.json` | JSON (newline-delimited) |
| `refugee_assistance` | `refugee_assistance.avro` | Avro |
| `refugee_protection` | `refugee_protection.csv.gz` | CSV (gzip) |

Passing an unknown name prints the list of valid names and exits with code 1:

```
usage error: unknown dataset 'foo'. Known datasets: afghan_refugees, beneficiaries, ...
```

---

## Verifying Output via the Manifest

After ingestion, the script writes a run manifest to:

```
delta_lake/bronze/_manifest.json
```

### Reading the manifest

```bash
cat delta_lake/bronze/_manifest.json
```

Or with Python for formatted output:

```bash
python -c "import json; print(json.dumps(json.load(open('delta_lake/bronze/_manifest.json')), indent=2))"
```

### What to check

A successful full ingestion produces **9 entries** in the manifest — one per dataset. Each entry looks like:

```json
{
  "dataset_name": "beneficiaries",
  "row_count": 50000,
  "file_size_bytes": 3523010,
  "ingestion_timestamp": "2026-05-12T19:22:09.128121+00:00",
  "source_format": "csv.gz"
}
```

### Expected row counts

| Dataset | Expected rows |
|---|---|
| `beneficiaries` | 50,000 |
| `payments` | 100,000 |
| `surveys` | 200,000 |
| `inventory` | 5,000 |
| `complaints` | 10,000 |
| `donor_reports` | 2,000 |
| `afghan_refugees` | 30,000 |
| `refugee_assistance` | 45,000 |
| `refugee_protection` | 9,000 |

Confirm all 9 entries are present and `row_count` matches the expected values above. If a dataset is missing from the manifest, it failed during ingestion — see the error recovery section below.

---

## Error Recovery

### A dataset fails during ingestion

The script logs errors to stderr and continues processing remaining datasets. A failed dataset is **not written to the manifest**.

1. Check stderr output for the error line:

   ```
   ERROR: beneficiaries — data_large/beneficiaries.csv.gz — [error message]
   ```

2. Common causes:
   - **File not found**: Confirm the file exists in `data_large/` (or the path passed to `--data-dir`).
   - **Parse error**: The source file may be corrupted. Re-download or regenerate it with `python datagenerator.py`.
   - **Java/Spark error**: Confirm `JAVA_HOME` is set and `java -version` returns 11+.

3. Once the root cause is resolved, re-run only the failed dataset:

   ```bash
   python ingest/ingest.py --dataset beneficiaries
   ```

   This overwrites the Bronze table for that dataset and updates the manifest entry without affecting other datasets.

### Manifest has fewer than 9 entries

Count entries in the manifest:

```bash
python -c "import json; d=json.load(open('delta_lake/bronze/_manifest.json')); print(len(d), 'entries:', list(d.keys()))"
```

For each missing dataset, follow the steps above to re-run it individually.

### SparkSession fails to start

If Spark cannot start (e.g., `JAVA_HOME` not set, port conflict), the script exits before writing any Delta tables. Fix the environment issue and re-run the full ingestion — all writes are idempotent (overwrite mode), so re-running is safe.

---

## Makefile Shortcut

The repository `Makefile` includes an `ingest` target:

```bash
make ingest
```

This is equivalent to `python ingest/ingest.py` run from the repository root.
