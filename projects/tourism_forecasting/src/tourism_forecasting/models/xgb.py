"""XGBoost forecaster — a global gradient-boosted challenger with quantile bands.

Direct multi-horizon: a separate model per (horizon, quantile), each predicting h steps ahead
from origin-anchored lag/rolling/calendar features (no recursion → no compounding error). Bands
come from quantile-loss models; per-point quantiles are sorted to prevent crossing. Works in
log1p space so forecasts stay non-negative and seasonality is multiplicative.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from .. import features

_LAGS = (1, 2, 3, 12, 13)
_MIN_ANCHOR = 12  # need lag-13 history
_PARAMS = dict(
    n_estimators=200,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    min_child_weight=2.0,
    reg_lambda=1.0,
    random_state=0,
    n_jobs=0,
)


def _quantiles(levels: Sequence[int]) -> list[float]:
    qs = {0.5}
    for level in levels:
        qs.add((100 - level) / 200.0)
        qs.add(1.0 - (100 - level) / 200.0)
    return sorted(qs)


def _feature_row(t: np.ndarray, anchor: int, target_month: int, target_covid: float) -> list[float]:
    angle = 2.0 * np.pi * (target_month - 1) / 12.0
    return [
        *[t[anchor - (lag - 1)] for lag in _LAGS],
        float(np.mean(t[anchor - 2 : anchor + 1])),
        float(np.mean(t[anchor - 11 : anchor + 1])),
        float(np.sin(angle)),
        float(np.cos(angle)),
        target_covid,
    ]


class XGBForecaster:
    name = "xgboost"

    def fit(self, y: pd.Series) -> XGBForecaster:
        self.y = y
        self._t = np.log1p(y.to_numpy(dtype=float))
        self._index = pd.DatetimeIndex(y.index)
        self._covid = features.covid_flag(self._index).to_numpy(dtype=float)
        return self

    def _train_for_horizon(self, h: int, quantiles: Sequence[float]) -> dict[float, XGBRegressor]:
        t, n = self._t, len(self._t)
        rows: list[list[float]] = []
        targets: list[float] = []
        for i in range(_MIN_ANCHOR + h, n):
            anchor = i - h
            rows.append(_feature_row(t, anchor, int(self._index[i].month), float(self._covid[i])))
            targets.append(float(t[i]))
        x_train = np.asarray(rows, dtype=float)
        y_train = np.asarray(targets, dtype=float)
        models: dict[float, XGBRegressor] = {}
        for q in quantiles:
            model = XGBRegressor(objective="reg:quantileerror", quantile_alpha=q, **_PARAMS)
            model.fit(x_train, y_train)
            models[q] = model
        return models

    def forecast(self, horizon: int, levels: Sequence[int]) -> pd.DataFrame:
        quantiles = _quantiles(levels)
        idx = features.future_index(self.y, horizon)
        anchor = len(self._t) - 1
        rows = {q: np.empty(horizon) for q in quantiles}
        for h in range(1, horizon + 1):
            models = self._train_for_horizon(h, quantiles)
            feat = np.asarray(
                [_feature_row(self._t, anchor, int(idx[h - 1].month), 0.0)], dtype=float
            )
            preds = sorted(float(models[q].predict(feat)[0]) for q in quantiles)  # no crossing
            for q, value in zip(quantiles, preds, strict=True):
                rows[q][h - 1] = value
        out = pd.DataFrame({"yhat": np.clip(np.expm1(rows[0.5]), 0.0, None)}, index=idx)
        for level in levels:
            lo_q, hi_q = (100 - level) / 200.0, 1.0 - (100 - level) / 200.0
            out[f"lower_{level}"] = np.clip(np.expm1(rows[lo_q]), 0.0, None)
            out[f"upper_{level}"] = np.clip(np.expm1(rows[hi_q]), 0.0, None)
        return out
