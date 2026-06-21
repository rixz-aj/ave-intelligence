"""End-to-end forecasting pipeline (Phase 1 — scaffold).

Wires the ave_core primitives into one reproducible run:

    ingest (MMA 104 + covariates)
      -> contract (validate_arrivals)
      -> features (lags / rolling / calendar / exog)
      -> fit (sarima | prophet | xgboost), with COVID structural-break handling
      -> backtest (rolling-origin: MASE / sMAPE / pinball)
      -> export (forecast JSON + report MDX into published/)

Run: `uv run python -m tourism_forecasting.pipeline`. Each step below is a TODO
anchored to the build brief in CLAUDE.md — implement top to bottom.
"""

from __future__ import annotations


def run() -> int:
    raise NotImplementedError(
        "Phase 1: implement the forecasting pipeline. Start from the seasonal-naive "
        "baseline (ave_core.eval.seasonal_naive), then SARIMA. See CLAUDE.md."
    )


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
