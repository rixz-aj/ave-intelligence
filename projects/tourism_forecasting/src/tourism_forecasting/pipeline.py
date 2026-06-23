"""End-to-end forecasting pipeline.

    load arrivals (published v2)
      -> rolling-origin backtest every model (seasonal-naive baseline + SARIMA/Prophet/XGBoost)
      -> pick the model with the best MASE (must beat the baseline, MASE < 1.0)
      -> refit the winner on all data, forecast 12 months with 80/95 bands
      -> return forecast frame + embedded backtest block (publishing is done by the script)

Run: `uv run python -m tourism_forecasting.pipeline` (prints the backtest scoreboard).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import config
from .backtest import BacktestResult, rolling_origin_backtest
from .data import load_arrivals
from .models import (
    Forecaster,
    ProphetForecaster,
    SarimaxForecaster,
    SeasonalNaiveForecaster,
    XGBForecaster,
)

ModelFactory = Callable[[], Forecaster]

# Candidate models. seasonal_naive is the baseline reference (always scored, never "wins").
CANDIDATES: dict[str, ModelFactory] = {
    "seasonal_naive": SeasonalNaiveForecaster,
    "sarima": SarimaxForecaster,
    "prophet": ProphetForecaster,
    "xgboost": XGBForecaster,
}


@dataclass(frozen=True)
class PipelineOutput:
    winner: str
    scoreboard: dict[str, BacktestResult]
    forecast: pd.DataFrame  # indexed by future month-start: yhat + lower_/upper_{level}
    backtest_block: dict[str, object]


def run(published_root: Path = Path("published")) -> PipelineOutput:
    y = load_arrivals(published_root)

    scoreboard: dict[str, BacktestResult] = {}
    for name, factory in CANDIDATES.items():
        scoreboard[name] = rolling_origin_backtest(y, factory)

    # Winner = best MASE among the real models (exclude the baseline itself).
    ranked = sorted(
        (n for n in scoreboard if n != "seasonal_naive"), key=lambda n: scoreboard[n].mase
    )
    winner = ranked[0]
    if scoreboard[winner].mase >= 1.0:
        raise SystemExit(
            f"no model beats the seasonal-naive baseline (best={winner} "
            f"MASE={scoreboard[winner].mase:.3f}); refusing to publish."
        )

    model = CANDIDATES[winner]().fit(y)
    forecast = model.forecast(config.HORIZON_MONTHS, config.BAND_LEVELS)
    backtest_block = scoreboard[winner].as_artifact_block()
    return PipelineOutput(winner, scoreboard, forecast, backtest_block)


def _format_scoreboard(out: PipelineOutput) -> str:
    lines = ["", "model           MASE    MASE(ex-COVID)  sMAPE   pinball  folds", "-" * 58]
    for name, r in sorted(out.scoreboard.items(), key=lambda kv: kv[1].mase):
        star = "  <- winner" if name == out.winner else ""
        lines.append(
            f"{name:14s} {r.mase:6.3f}   {r.mase_ex_covid:7.3f}      "
            f"{r.smape:6.2f}  {r.pinball:7.0f}  {r.folds:3d}{star}"
        )
    return "\n".join(lines)


def main() -> int:
    out = run()
    print(_format_scoreboard(out))
    print(
        f"\nWinner: {out.winner}. 12-month forecast "
        f"{out.forecast.index[0]:%Y-%m} → {out.forecast.index[-1]:%Y-%m}:"
    )
    preview = out.forecast[["yhat", "lower_80", "upper_80"]].round(0)
    print(preview.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
