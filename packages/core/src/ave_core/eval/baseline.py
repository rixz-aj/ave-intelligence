"""Seasonal-naive baseline + scale-free accuracy metrics.

`seasonal_naive` is the reference every model must beat (MASE < 1.0). MASE is scaled
by the in-sample seasonal-naive error, so it's comparable across series of different
magnitudes — the honest way to report tourism-forecast accuracy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def seasonal_naive(y: pd.Series, horizon: int, m: int = 12) -> pd.Series:
    """Forecast `horizon` steps by repeating the last seasonal cycle of length `m`.

    `y` must have a monthly (month-start) DatetimeIndex. Returns a Series indexed by
    the next `horizon` month-starts, named 'yhat'.
    """
    if len(y) < m:
        raise ValueError(f"need at least m={m} observations, got {len(y)}")
    last_cycle = np.asarray(y, dtype=float)[-m:]
    reps = int(np.ceil(horizon / m))
    forecast = np.tile(last_cycle, reps)[:horizon]
    last_ds = pd.Timestamp(y.index[-1])
    future_index = pd.date_range(last_ds + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    return pd.Series(forecast, index=future_index, name="yhat")


def mase(y_true: pd.Series, y_pred: pd.Series, y_train: pd.Series, m: int = 12) -> float:
    """Mean Absolute Scaled Error. < 1.0 means better than the seasonal-naive baseline."""
    train = np.asarray(y_train, dtype=float)
    if len(train) <= m:
        raise ValueError(f"training series too short for m={m}")
    scale = float(np.mean(np.abs(train[m:] - train[:-m])))
    if scale == 0.0:
        return float("inf")
    error = float(np.mean(np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))))
    return error / scale


def smape(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Symmetric Mean Absolute Percentage Error (%). Range 0–200; lower is better."""
    actual = np.asarray(y_true, dtype=float)
    forecast = np.asarray(y_pred, dtype=float)
    denominator = np.abs(actual) + np.abs(forecast)
    ratio = np.where(denominator == 0.0, 0.0, 2.0 * np.abs(forecast - actual) / denominator)
    return float(np.mean(ratio) * 100.0)
