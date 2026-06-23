"""The forecaster interface every model implements, so the backtest harness is generic.

Models operate on the ORIGINAL arrivals scale (so MASE and the seasonal-naive baseline are
directly comparable); each model applies its own internal transform (most fit in log1p space
to capture multiplicative seasonality and guarantee non-negative forecasts).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class Forecaster(Protocol):
    """A fit/forecast pair. `forecast` returns a frame indexed by future month-start with a
    `yhat` column plus `lower_{L}`/`upper_{L}` columns for each requested interval level."""

    name: str

    def fit(self, y: pd.Series) -> Forecaster: ...

    def forecast(self, horizon: int, levels: Sequence[int]) -> pd.DataFrame: ...
