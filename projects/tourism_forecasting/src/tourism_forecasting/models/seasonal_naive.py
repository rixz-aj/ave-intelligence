"""Seasonal-naive baseline forecaster — the MASE = 1.0 reference every model must beat.

Point forecast repeats the last seasonal cycle (`ave_core.eval.seasonal_naive`); prediction
intervals come from the in-sample seasonal-difference residuals, widening by √(cycles-ahead).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm

from ave_core.eval.baseline import seasonal_naive

from .. import config, features


class SeasonalNaiveForecaster:
    name = "seasonal_naive"

    def __init__(self, m: int = config.SEASONAL_PERIOD) -> None:
        self.m = m

    def fit(self, y: pd.Series) -> SeasonalNaiveForecaster:
        self.y = y
        diffs = y.to_numpy(dtype=float)[self.m :] - y.to_numpy(dtype=float)[: -self.m]
        self._sigma = float(np.std(diffs, ddof=1))
        return self

    def forecast(self, horizon: int, levels: Sequence[int]) -> pd.DataFrame:
        point = seasonal_naive(self.y, horizon, self.m).to_numpy(dtype=float)
        idx = features.future_index(self.y, horizon)
        out = pd.DataFrame({"yhat": point}, index=idx)
        cycles_ahead = np.array([math.floor(h / self.m) + 1 for h in range(horizon)], dtype=float)
        se = self._sigma * np.sqrt(cycles_ahead)
        for level in levels:
            z = float(norm.ppf(0.5 + level / 200.0))
            out[f"lower_{level}"] = np.clip(point - z * se, 0.0, None)
            out[f"upper_{level}"] = point + z * se
        out["yhat"] = np.clip(out["yhat"], 0.0, None)
        return out
