"""Helpers for running against Terminal-Bench's native harness."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
TERMINAL_BENCH_ROOT = REPO_ROOT / "terminal-bench"
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def ensure_terminal_bench_importable() -> None:
    repo_str = str(TERMINAL_BENCH_ROOT)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def maybe_reexec_python312() -> None:
    """Re-exec into the benchmark runtime interpreter when needed."""
    if sys.version_info >= (3, 12):
        return

    candidates: list[str] = []
    if VENV_PYTHON.exists():
        candidates.append(str(VENV_PYTHON))

    python312 = shutil.which("python3.12")
    if python312:
        candidates.append(python312)

    if not candidates:
        raise RuntimeError(
            "Terminal-Bench requires Python 3.12+. Install python3.12 or create .venv."
        )

    os.execvp(candidates[0], [candidates[0], "-m", "ktb.cli", *sys.argv[1:]])
