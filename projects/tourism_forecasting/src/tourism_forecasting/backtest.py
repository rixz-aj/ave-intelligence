"""Rolling-origin (expanding-window) backtest — the honesty engine.

For each recent origin we train on everything up to that point, forecast forward, and score
against the held-out actuals. We report MASE (vs the seasonal-naive baseline — the number
that decides whether a model ships), sMAPE, and pinball loss (band calibration). The COVID
window is reported separately so a recovery bounce never flatters the headline score.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ave_core.eval.baseline import mase, smape

from . import config
from .models.base import Forecaster

ModelFactory = Callable[[], Forecaster]


@dataclass(frozen=True)
class BacktestResult:
    mase: float
    smape: float
    pinball: float
    folds: int
    mase_ex_shocks: float
    n_points: int

    def as_artifact_block(self, baseline: str = "seasonal_naive") -> dict[str, object]:
        return {
            "baseline": baseline,
            "mase": round(self.mase, 4),
            "smape": round(self.smape, 4),
            "pinball": round(self.pinball, 4),
            "folds": self.folds,
        }


def _pinball(actual: float, quantile_pred: float, q: float) -> float:
    delta = actual - quantile_pred
    return float(max(q * delta, (q - 1.0) * delta))


def rolling_origin_backtest(
    y: pd.Series,
    make_model: ModelFactory,
    *,
    levels: Sequence[int] = config.BAND_LEVELS,
    n_origins: int = config.BACKTEST_N_ORIGINS,
    min_train: int = config.BACKTEST_MIN_TRAIN,
    max_h: int = config.BACKTEST_MAX_H,
) -> BacktestResult:
    """Expanding-window backtest, refit at every origin."""
    n = len(y)
    first_origin = max(min_train, n - n_origins)
    origins = range(first_origin, n)  # train y[:o], evaluate from o onward

    per_origin_mase: list[float] = []
    all_actual: list[float] = []
    all_pred: list[float] = []
    all_ds: list[pd.Timestamp] = []
    pinball_terms: list[float] = []

    for o in origins:
        train = y.iloc[:o]
        steps = min(max_h, n - o)
        if steps < 1:
            continue
        actual = y.iloc[o : o + steps]
        model = make_model().fit(train)
        fc = model.forecast(steps, levels).iloc[:steps]

        yhat = fc["yhat"].to_numpy(dtype=float)
        truth = actual.to_numpy(dtype=float)
        per_origin_mase.append(mase(actual, pd.Series(yhat, index=actual.index), train))
        all_actual.extend(truth.tolist())
        all_pred.extend(yhat.tolist())
        all_ds.extend(list(actual.index))

        for level in levels:
            lo_q, hi_q = (100 - level) / 200.0, 1.0 - (100 - level) / 200.0
            lower = fc[f"lower_{level}"].to_numpy(dtype=float)
            upper = fc[f"upper_{level}"].to_numpy(dtype=float)
            for a, lo, hi in zip(truth, lower, upper, strict=True):
                pinball_terms.append(_pinball(a, lo, lo_q))
                pinball_terms.append(_pinball(a, hi, hi_q))

    actual_s = pd.Series(all_actual)
    pred_s = pd.Series(all_pred)
    ds_idx = pd.DatetimeIndex(all_ds)
    in_shock = np.zeros(len(ds_idx), dtype=bool)
    for start, end in config.INTERVENTION_WINDOWS:
        in_shock |= (ds_idx >= start) & (ds_idx <= end)
    ex = ~in_shock
    mase_ex = (
        float(np.mean(np.abs(actual_s[ex].to_numpy() - pred_s[ex].to_numpy())) / _seasonal_scale(y))
        if ex.any()
        else float("nan")
    )

    return BacktestResult(
        mase=float(np.mean(per_origin_mase)),
        smape=smape(actual_s, pred_s),
        pinball=float(np.mean(pinball_terms)) if pinball_terms else float("nan"),
        folds=len(per_origin_mase),
        mase_ex_shocks=mase_ex,
        n_points=len(all_actual),
    )


def _seasonal_scale(y: pd.Series, m: int = config.SEASONAL_PERIOD) -> float:
    """Whole-sample seasonal-naive MAE — the scale for the ex-COVID MASE summary."""
    values = y.to_numpy(dtype=float)
    return float(np.mean(np.abs(values[m:] - values[:-m])))
