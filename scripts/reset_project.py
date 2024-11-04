#!/usr/bin/env python3
"""
Cross-platform reset of generated portfolio artifacts.

Used by ``reset-project.ps1`` and Airflow DAGs. Does not delete source code, .venv,
or git metadata.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Repo root = parent of scripts/
REPO_ROOT = Path(__file__).resolve().parent.parent

RESET_SCOPES = (
    "Full",
    "Datagenerator",
    "MedallionFull",
    "MedallionBronze",
    "MedallionSilver",
    "MedallionGold",
    "DbtSql",
    "Streamlit",
    "PipelineBuild",
)


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _unlink_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()
        _log(f"Removed file {path}")


def _rmtree_if_exists(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=False)
        _log(f"Removed directory {path}")


def _clear_dir_contents(path: Path) -> None:
    """Remove all children of *path*; keep *path* as an empty directory."""
    if not path.is_dir():
        return
    for child in list(path.iterdir()):
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=False)
        else:
            child.unlink(missing_ok=True)
        _log(f"Removed {child}")


def _remove_globs(dir_path: Path, patterns: tuple[str, ...]) -> None:
    if not dir_path.is_dir():
        return
    for pat in patterns:
        for p in dir_path.glob(pat):
            if p.is_file():
                p.unlink(missing_ok=True)
                _log(f"Removed file {p}")


def _remove_executed_notebooks(repo: Path) -> None:
    nb = repo / "notebooks"
    if not nb.is_dir():
        return
    for p in nb.glob("*_executed.ipynb"):
        p.unlink(missing_ok=True)
        _log(f"Removed {p}")


def _remove_dbt_artifacts(repo: Path, *, include_packages: bool) -> None:
    _rmtree_if_exists(repo / "dbt" / "target")
    _rmtree_if_exists(repo / "dbt" / "logs")
    if include_packages:
        _rmtree_if_exists(repo / "dbt" / "dbt_packages")


def _remove_airflow_home(repo: Path) -> None:
    _rmtree_if_exists(repo / "airflow" / "airflow_home")


def _remove_spark_scratch(repo: Path) -> None:
    _rmtree_if_exists(repo / ".spark_scratch")


def _remove_streamlit_caches(repo: Path) -> None:
    dash = repo / "dashboard"
    cache = dash / "__pycache__"
    _rmtree_if_exists(cache)
    st = repo / ".streamlit"
    _rmtree_if_exists(st)
    _remove_globs(dash, ("*.pyc",))


def reset(repo: Path, scope: str, *, include_airflow_home: bool = False) -> None:
    repo = repo.resolve()
    if scope == "Full":
        _clear_dir_contents(repo / "data_large")
        _rmtree_if_exists(repo / "delta_lake")
        _remove_spark_scratch(repo)
        _unlink_if_exists(repo / "pspl.duckdb")
        _remove_dbt_artifacts(repo, include_packages=True)
        _remove_executed_notebooks(repo)
        _remove_globs(repo / "docs" / "sample_outputs", ("*.png",))
        _remove_streamlit_caches(repo)
        if include_airflow_home:
            _remove_airflow_home(repo)
        return

    if scope == "Datagenerator":
        _clear_dir_contents(repo / "data_large")
        return

    if scope == "MedallionFull":
        _rmtree_if_exists(repo / "delta_lake")
        _remove_spark_scratch(repo)
        _remove_executed_notebooks(repo)
        _remove_globs(repo / "docs" / "sample_outputs", ("*.png",))
        return

    if scope == "MedallionBronze":
        _rmtree_if_exists(repo / "delta_lake" / "bronze")
        return

    if scope == "MedallionSilver":
        _rmtree_if_exists(repo / "delta_lake" / "silver")
        _remove_globs(repo / "docs" / "sample_outputs", ("*.png",))
        return

    if scope == "MedallionGold":
        _unlink_if_exists(repo / "pspl.duckdb")
        _remove_dbt_artifacts(repo, include_packages=False)
        return

    if scope == "DbtSql":
        _remove_dbt_artifacts(repo, include_packages=False)
        return

    if scope == "Streamlit":
        _remove_streamlit_caches(repo)
        return

    if scope == "PipelineBuild":
        _rmtree_if_exists(repo / "delta_lake")
        _unlink_if_exists(repo / "pspl.duckdb")
        _remove_dbt_artifacts(repo, include_packages=True)
        _remove_spark_scratch(repo)
        return

    raise ValueError(f"Unknown scope: {scope!r}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Remove generated artifacts for a clean re-run (see --scope).",
    )
    p.add_argument(
        "--scope",
        choices=RESET_SCOPES,
        required=True,
        help=(
            "Full=all generated data and build outputs. "
            "Medallion* = Delta layers under delta_lake/. "
            "MedallionGold=DuckDB+dbt target/logs. DbtSql=dbt target/logs only. "
            "PipelineBuild=legacy clean (delta+duckdb+dbt target+packages)."
        ),
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (default: parent of scripts/).",
    )
    p.add_argument(
        "--include-airflow-home",
        action="store_true",
        help="Also delete airflow/airflow_home (scheduler DB, logs). Use with care.",
    )
    args = p.parse_args(argv)
    try:
        reset(
            args.repo_root,
            args.scope,
            include_airflow_home=args.include_airflow_home,
        )
    except OSError as exc:
        _log(f"ERROR: {exc}")
        return 1
    _log(f"Reset complete (scope={args.scope}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
