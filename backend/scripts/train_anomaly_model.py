"""Backward-compatible entry point for the Phase 3 Random Forest trainer."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts.train_random_forest import main, train_model  # noqa: E402

__all__ = ["main", "train_model"]


if __name__ == "__main__":
    raise SystemExit(main())
