"""Prophet forecaster — trend changepoints + yearly seasonality, robust to the COVID gap.

Fits log1p(arrivals) with a single COVID indicator regressor; multi-level prediction bands
come from Prophet's posterior predictive samples (so 80% and 95% are mutually consistent).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from .. import features

logging.getLogger("prophet").setLevel(logging.CRITICAL)
logging.getLogger("cmdstanpy").setLevel(logging.CRITICAL)


class ProphetForecaster:
    name = "prophet"

    def fit(self, y: pd.Series) -> ProphetForecaster:
        from prophet import Prophet

        self.y = y
        frame = pd.DataFrame(
            {
                "ds": y.index,
                "y": np.log1p(y.to_numpy(dtype=float)),
                "shock": features.intervention_flag(y.index).to_numpy(dtype=float),
            }
        )
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="additive",
            uncertainty_samples=1000,
        )
        model.add_regressor("shock")
        self._model = model.fit(frame)
        return self

    def forecast(self, horizon: int, levels: Sequence[int]) -> pd.DataFrame:
        idx = features.future_index(self.y, horizon)
        future = pd.DataFrame({"ds": idx, "shock": 0.0})
        samples = self._model.predictive_samples(future)["yhat"]  # (horizon, n_samples), log space
        out = pd.DataFrame({"yhat": np.clip(np.expm1(samples.mean(axis=1)), 0.0, None)}, index=idx)
        for level in levels:
            lo_q, hi_q = (100 - level) / 200.0, 1.0 - (100 - level) / 200.0
            out[f"lower_{level}"] = np.clip(np.expm1(np.quantile(samples, lo_q, axis=1)), 0.0, None)
            out[f"upper_{level}"] = np.clip(np.expm1(np.quantile(samples, hi_q, axis=1)), 0.0, None)
        return out
