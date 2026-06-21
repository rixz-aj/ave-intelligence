"""Evaluation — the seasonal-naive baseline and forecast accuracy metrics.

The baseline defines MASE = 1.0; no model ships unless it beats it. Rolling-origin
backtesting (Phase 1) lives here too; metrics are embedded in every forecast artifact.
"""

from __future__ import annotations

from ave_core.eval.baseline import mase, seasonal_naive, smape

__all__ = ["seasonal_naive", "mase", "smape"]
