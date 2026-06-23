"""SARIMAX forecaster — clean single series, interpretable, analytic prediction intervals.

Fits in log1p space (multiplicative seasonality, non-negative back-transform) with COVID
intervention dummies as exogenous regressors, so the 2020 collapse is absorbed rather than
fitted through. A seasonal (airline-style) order captures the strong yearly cycle.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .. import config, features

ORDER = (1, 1, 1)
SEASONAL_ORDER = (0, 1, 1, config.SEASONAL_PERIOD)


class SarimaxForecaster:
    name = "sarima"

    def __init__(
        self,
        order: tuple[int, int, int] = ORDER,
        seasonal_order: tuple[int, int, int, int] = SEASONAL_ORDER,
    ) -> None:
        self.order = order
        self.seasonal_order = seasonal_order

    def fit(self, y: pd.Series) -> SarimaxForecaster:
        self.y = y
        endog = np.log1p(y.astype(float))
        exog = features.intervention_dummies(y.index)
        exog = exog.loc[:, (exog != 0.0).any(axis=0)]  # drop columns with no support in train
        self._exog_cols = list(exog.columns)
        exog_arg = exog if self._exog_cols else None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._res = SARIMAX(
                endog,
                exog=exog_arg,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
        return self

    def forecast(self, horizon: int, levels: Sequence[int]) -> pd.DataFrame:
        idx = features.future_index(self.y, horizon)
        if self._exog_cols:
            future_exog = features.intervention_dummies(idx).reindex(
                columns=self._exog_cols, fill_value=0.0
            )
        else:
            future_exog = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self._res.get_forecast(steps=horizon, exog=future_exog)
        mean_log = forecast.predicted_mean.to_numpy(dtype=float)
        out = pd.DataFrame({"yhat": np.clip(np.expm1(mean_log), 0.0, None)}, index=idx)
        for level in levels:
            ci = forecast.conf_int(alpha=1.0 - level / 100.0).to_numpy(dtype=float)
            out[f"lower_{level}"] = np.clip(np.expm1(ci[:, 0]), 0.0, None)
            out[f"upper_{level}"] = np.clip(np.expm1(ci[:, 1]), 0.0, None)
        return out
