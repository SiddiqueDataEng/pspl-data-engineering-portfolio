"""
Spark / JVM prerequisites for local PySpark + Delta (especially on Windows).

Used by ``ingest.ingest`` before importing PySpark so failures are actionable.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from typing import Optional

_WINUTILS_URL = (
    "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/winutils.exe"
)


def _is_windows() -> bool:
    return sys.platform == "win32"


def ensure_pyspark_uses_current_interpreter() -> str:
    """
  Force PySpark Python workers to use the same interpreter as the driver.

  If ``PYSPARK_PYTHON`` points at another Python (e.g. 3.14 on PATH while the
  driver is 3.11 in ``.venv``), workers crash with ``Connection reset`` /
  ``Python worker exited unexpectedly``.
    """
    exe = os.path.abspath(sys.executable)
    os.environ["PYSPARK_PYTHON"] = exe
    os.environ["PYSPARK_DRIVER_PYTHON"] = exe
    return exe


def _java_bin_candidates() -> list[str]:
    """Return possible ``java`` executable paths to probe (JAVA_HOME first, then PATH)."""
    out: list[str] = []
    java_home = (os.environ.get("JAVA_HOME") or "").strip().strip('"')
    if java_home:
        exe = os.path.join(java_home, "bin", "java.exe" if _is_windows() else "java")
        out.append(exe)
    which = shutil.which("java")
    if which:
        out.append(which)
    # de-dupe preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def describe_java_env() -> str:
    """Human-readable summary of JAVA_HOME / java on PATH (for error messages)."""
    jh = (os.environ.get("JAVA_HOME") or "").strip() or "(not set)"
    which = shutil.which("java") or "(not on PATH)"
    return f"JAVA_HOME={jh!r}; java on PATH={which!r}"


def _prepend_to_path(dir_path: str) -> None:
    """Put *dir_path* at the front of PATH for this process if not already present."""
    cur = os.environ.get("PATH", "")
    parts = [p for p in cur.split(os.pathsep) if p]
    norm_target = os.path.normcase(os.path.abspath(dir_path))
    for p in parts:
        try:
            if os.path.normcase(os.path.abspath(p)) == norm_target:
                return
        except OSError:
            continue
    os.environ["PATH"] = dir_path + os.pathsep + cur


def _ensure_windows_hadoop_winutils() -> None:
    """
    Match ``scripts/_pipeline-common.ps1`` behaviour: default ``HADOOP_HOME``,
    download ``winutils.exe`` if missing, prepend ``%HADOOP_HOME%\\bin`` to PATH.

    Mutates ``os.environ`` for the current process only.
    """
    log = logging.getLogger(__name__)
    hadoop = (os.environ.get("HADOOP_HOME") or "").strip()
    if not hadoop:
        profile = (os.environ.get("USERPROFILE") or "").strip()
        if not profile:
            raise RuntimeError(
                "USERPROFILE is not set; cannot default HADOOP_HOME for Spark on Windows."
            )
        hadoop = os.path.join(profile, "hadoop")
        os.environ["HADOOP_HOME"] = hadoop

    bin_dir = os.path.join(hadoop, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    winutils = os.path.join(bin_dir, "winutils.exe")
    if not os.path.isfile(winutils):
        log.info("Downloading winutils.exe for local Spark (first run) ...")
        try:
            urllib.request.urlretrieve(_WINUTILS_URL, winutils)
        except OSError as exc:
            raise RuntimeError(
                "Could not download winutils.exe (needed for Spark on Windows). "
                f"Download manually from {_WINUTILS_URL!r} and save as {winutils!r}. "
                f"Underlying error: {exc}"
            ) from exc
    if not os.path.isfile(winutils) or os.path.getsize(winutils) < 1000:
        raise RuntimeError(
            f"winutils.exe is missing or invalid at {winutils!r}. "
            "Delete the file and retry, or install manually (see scripts/_pipeline-common.ps1)."
        )
    _prepend_to_path(bin_dir)


def find_working_java_exe() -> Optional[str]:
    """Return the first ``java`` that runs ``-version``, or None."""
    for candidate in _java_bin_candidates():
        if not os.path.isfile(candidate):
            continue
        try:
            subprocess.run(
                [candidate, "-version"],
                check=True,
                capture_output=True,
                timeout=30,
            )
            return candidate
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def validate_local_spark_prerequisites() -> None:
    """
    Ensure a JVM is available before PySpark is imported.

    On Windows, also ensures ``HADOOP_HOME`` / ``winutils.exe`` (same defaults as
    ``run-ingest.ps1``) so ``python ingest/ingest.py`` works without manual env vars.

    Raises:
        RuntimeError: If no working Java is found or Windows winutils setup fails.
    """
    if _is_windows():
        _ensure_windows_hadoop_winutils()

    java_exe = find_working_java_exe()
    if not java_exe:
        hint = (
            "Install JDK 17 (e.g. Eclipse Temurin), set JAVA_HOME to the JDK root, "
            "and ensure %JAVA_HOME%\\bin is on PATH."
            if _is_windows()
            else "Install JDK 17, set JAVA_HOME, and ensure `java` is on PATH."
        )
        raise RuntimeError(
            "No working Java runtime found for Spark. "
            f"{describe_java_env()}. {hint}"
        )


def warn_if_unsupported_python(logger) -> None:
    """Log a strong warning when Python is outside PySpark-tested ranges."""
    v = sys.version_info[:2]
    if v >= (3, 14):
        logger.error(
            "Python %s.%s is likely unsupported by PySpark; use 3.10-3.12 "
            "(recreate .venv: .\\setup.ps1 -Python 'py -3.11').",
            v[0],
            v[1],
        )
    elif v not in ((3, 10), (3, 11), (3, 12), (3, 13)):
        logger.warning(
            "Python %s.%s may not be fully supported by PySpark; prefer 3.10-3.12.",
            v[0],
            v[1],
        )
