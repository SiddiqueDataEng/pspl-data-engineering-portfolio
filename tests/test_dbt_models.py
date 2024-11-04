"""
dbt model structural tests.

Feature: PSPL-data-engineering-portfolio
"""

import json
import pathlib
import re
import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_column_tests(column: dict) -> list[str]:
    """Return a flat list of test names for a column entry.

    dbt supports two keys:
      - ``tests:``      (dbt < 1.8)
      - ``data_tests:`` (dbt >= 1.8)

    Each entry can be a plain string (e.g. ``- not_null``) or a dict whose
    first key is the test name (e.g. ``- unique: {config: ...}``).
    """
    raw = column.get("data_tests") or column.get("tests") or []
    names: list[str] = []
    for entry in raw:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict):
            names.extend(entry.keys())
    return names


def _is_pk_column(col_name: str, col_tests: list[str]) -> bool:
    """Return True if the column should be treated as a primary key.

    Criteria (any one is sufficient):
      1. Name ends with ``_key`` (surrogate/renamed PKs are always PKs)
      2. Column already has a ``unique`` test (explicit PK declaration)

    Note: columns ending with ``_id`` may be foreign keys (e.g. beneficiary_id
    in stg_payments), so they are only treated as PKs when they carry an
    explicit ``unique`` test.
    """
    if col_name.endswith("_key"):
        return True
    if "unique" in col_tests:
        return True
    return False


# ---------------------------------------------------------------------------
# Property 9 – dbt primary key test coverage
# Validates: Requirements 3.6
# ---------------------------------------------------------------------------

@pytest.mark.property
def test_dbt_primary_key_test_coverage():
    """
    Property 9: dbt primary key test coverage

    For every column in every dbt model that is identified as a primary key
    (name ends with ``_key`` / ``_id``, or already carries a ``unique`` test),
    both ``not_null`` AND ``unique`` tests must be declared.

    Feature: PSPL-data-engineering-portfolio, Property 9: dbt primary key test coverage
    Validates: Requirements 3.6
    """
    schema_files = list(pathlib.Path("dbt/models").rglob("schema.yml"))

    assert schema_files, (
        "No schema.yml files found under dbt/models/. "
        "Ensure the dbt project is present."
    )

    violations: list[str] = []

    for schema_path in sorted(schema_files):
        with schema_path.open() as fh:
            content = yaml.safe_load(fh)

        if not content or "models" not in content:
            continue

        for model in content["models"]:
            model_name = model.get("name", "<unnamed>")
            columns = model.get("columns") or []

            for col in columns:
                col_name = col.get("name", "")
                col_tests = _get_column_tests(col)

                if not _is_pk_column(col_name, col_tests):
                    continue

                missing: list[str] = []
                if "not_null" not in col_tests:
                    missing.append("not_null")
                if "unique" not in col_tests:
                    missing.append("unique")

                if missing:
                    violations.append(
                        f"{schema_path} | model '{model_name}' | "
                        f"column '{col_name}' is missing tests: {missing}"
                    )

    assert not violations, (
        "Primary key columns are missing required tests (not_null + unique):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Property 10 – dbt ref/source macro exclusivity
# Validates: Requirements 3.9
# ---------------------------------------------------------------------------

@pytest.mark.property
def test_dbt_ref_source_macro_exclusivity():
    """
    Property 10: dbt ref/source macro exclusivity

    For any dbt model SQL file in the models/ directory, all table references
    SHALL use ref() or source() macros. No hardcoded schema-qualified table
    names (e.g., silver.beneficiaries) SHALL appear in any model SQL.

    Feature: PSPL-data-engineering-portfolio, Property 10: dbt ref/source macro exclusivity
    Validates: Requirements 3.9
    """
    sql_files = list(pathlib.Path("dbt/models").rglob("*.sql"))

    assert sql_files, (
        "No .sql files found under dbt/models/. "
        "Ensure the dbt project is present."
    )

    violations: list[str] = []

    # Pattern to detect hardcoded schema-qualified table names in FROM/JOIN clauses.
    # A hardcoded reference looks like: FROM schema.table or JOIN schema.table
    # where the reference is NOT wrapped in {{ ref(...) }} or {{ source(...) }}.
    #
    # Strategy:
    # 1. Remove all {{ ref(...) }} and {{ source(...) }} macro calls.
    # 2. Remove Jinja template blocks {{ ... }} and {% ... %}.
    # 3. Look for FROM/JOIN followed by schema.table patterns.
    #    This avoids false positives from column references (alias.column).

    for sql_path in sorted(sql_files):
        with sql_path.open() as fh:
            content = fh.read()

        # Remove Jinja macro calls: {{ ref('...') }}, {{ source('...', '...') }}
        content_cleaned = re.sub(r'\{\{[^}]+\}\}', '', content)
        # Remove Jinja block tags: {% ... %}
        content_cleaned = re.sub(r'\{%[^%]+%\}', '', content_cleaned)
        # Remove SQL comments (single-line)
        content_cleaned = re.sub(r'--[^\n]*', '', content_cleaned)
        # Remove SQL block comments
        content_cleaned = re.sub(r'/\*.*?\*/', '', content_cleaned, flags=re.DOTALL)

        # Look for FROM or JOIN followed by a schema-qualified table name.
        # Pattern: (FROM|JOIN) <whitespace> identifier.identifier
        # This catches hardcoded references like: FROM silver.beneficiaries
        hardcoded_refs = re.finditer(
            r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\b',
            content_cleaned,
            re.IGNORECASE
        )

        for match in hardcoded_refs:
            qualified_name = match.group(1)
            violations.append(
                f"{sql_path} | Hardcoded schema-qualified table reference: '{qualified_name}'"
            )

    assert not violations, (
        "dbt models contain hardcoded schema-qualified table names. "
        "All table references must use ref() or source() macros:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Property 15 – Mart model column documentation completeness
# Validates: Requirements 5.4
# ---------------------------------------------------------------------------

@pytest.mark.property
def test_mart_column_documentation_completeness():
    """
    Property 15: Mart model column documentation completeness

    For any column in any mart model, a non-empty description SHALL exist
    in the dbt catalog (catalog.json) after running dbt docs generate.

    Feature: PSPL-data-engineering-portfolio, Property 15: Mart model column documentation completeness
    Validates: Requirements 5.4
    """
    catalog_path = pathlib.Path("dbt/target/catalog.json")

    if not catalog_path.exists():
        pytest.skip(
            "dbt/target/catalog.json not found. "
            "Run 'cd dbt && dbt docs generate' first."
        )

    with catalog_path.open() as fh:
        catalog = json.load(fh)

    # Catalog structure:
    # {
    #   "nodes": {
    #     "model.pspl.mart_payment_kpis": {
    #       "columns": {
    #         "district": {
    #           "name": "district",
    #           "description": "...",
    #           ...
    #         },
    #         ...
    #       }
    #     }
    #   }
    # }

    violations: list[str] = []

    # List of mart models to check
    mart_models = [
        "mart_payment_kpis",
        "mart_donor_budget_vs_actual",
        "mart_refugee_assistance_summary",
        "mart_protection_caseload",
    ]

    nodes = catalog.get("nodes", {})

    for mart_name in mart_models:
        # Find the node in the catalog
        # Node key format: "model.{project_name}.{model_name}"
        node_key = f"model.pspl.{mart_name}"
        
        if node_key not in nodes:
            violations.append(
                f"Mart model '{mart_name}' not found in catalog. "
                f"Expected key: '{node_key}'"
            )
            continue

        node = nodes[node_key]
        columns = node.get("columns", {})

        if not columns:
            violations.append(
                f"Mart model '{mart_name}' has no columns in catalog"
            )
            continue

        for col_name, col_data in columns.items():
            description = col_data.get("description", "").strip()
            
            if not description:
                violations.append(
                    f"Mart model '{mart_name}' | "
                    f"column '{col_name}' has no description"
                )

    assert not violations, (
        "Mart model columns are missing documentation:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
