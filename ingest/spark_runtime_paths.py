"""
Stable Spark temp directories (especially on Windows).

Using ``%TEMP%\\spark-*`` often causes ``Failed to delete`` / JAR lock errors on shutdown
when antivirus or Explorer holds handles. Point ``spark.local.dir`` and ``java.io.tmpdir``
at a repo-local ``.spark_scratch`` folder instead.
"""

from __future__ import annotations

import os
import sys
from typing import Any


def resolve_spark_scratch_dir(repo_root: str) -> str:
    """
    Directory for Spark shuffle and JVM temp files.

    If the repo path contains spaces (common on Windows Desktop), use
    ``%LOCALAPPDATA%\\pspl_spark_scratch`` so ``-Djava.io.tmpdir=...`` is not split
    by the JVM launcher (avoids ``ClassNotFoundException: social``).
    """
    repo_abs = os.path.abspath(repo_root)
    if " " in repo_abs and sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        scratch = os.path.join(base, "pspl_spark_scratch")
    else:
        scratch = os.path.join(repo_abs, ".spark_scratch")
    os.makedirs(scratch, exist_ok=True)
    return os.path.abspath(scratch)


def configure_spark_local_dirs(builder: Any, repo_root: str) -> Any:
    """
    Append configs so shuffle/extracted JARs use a stable scratch directory.

    Also sets ``SPARK_LOCAL_DIRS`` for the process (read before the JVM starts).
    """
    scratch_abs = resolve_spark_scratch_dir(repo_root)
    scratch_fwd = scratch_abs.replace("\\", "/")
    os.environ["SPARK_LOCAL_DIRS"] = scratch_abs
    # Quote paths with spaces for the JVM option parser.
    if " " in scratch_fwd:
        jvm_tmp = f'-Djava.io.tmpdir="{scratch_fwd}"'
    else:
        jvm_tmp = f"-Djava.io.tmpdir={scratch_fwd}"
    return (
        builder.config("spark.local.dir", scratch_fwd)
        .config("spark.driver.extraJavaOptions", jvm_tmp)
        .config("spark.executor.extraJavaOptions", jvm_tmp)
    )


def stop_spark_quietly(spark: Any, *, logger: Any = None) -> None:
    """
    Best-effort Spark shutdown for Windows (file locks on temp JAR dirs).

    Logs JVM cleanup IOException class messages at WARNING; exit code of the
    pipeline can still be success if work completed before stop.
    """
    import gc
    import sys
    import time

    try:
        spark.catalog.clearCache()
    except Exception:  # noqa: BLE001
        pass
    gc.collect()
    if sys.platform == "win32":
        time.sleep(2.0)
    try:
        spark.stop()
    except Exception as exc:  # noqa: BLE001
        if logger is not None:
            logger.warning("Spark stop raised (often harmless on Windows): %s", exc)
