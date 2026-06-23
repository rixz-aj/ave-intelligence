"""Deterministic, leakage-free features: the future month index, COVID intervention
dummies, and calendar features. Everything here is known at forecast time."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def future_index(y: pd.Series, horizon: int) -> pd.DatetimeIndex:
    """The next `horizon` month-starts after the last observation."""
    start = pd.Timestamp(y.index[-1]) + pd.offsets.MonthBegin(1)
    return pd.date_range(start, periods=horizon, freq="MS")


def covid_dummies(
    index: pd.DatetimeIndex,
    window: tuple[pd.Timestamp, pd.Timestamp] = config.COVID_WINDOW,
) -> pd.DataFrame:
    """One 0/1 indicator column per month in the COVID window.

    Columns are fixed by the window (not by `index`), so a training frame and a future
    frame always share the same column set — the dummies absorb the 2020 collapse and the
    abnormal 2021 recovery, and are all-zero for ordinary (incl. future) months.
    """
    months = pd.date_range(window[0], window[1], freq="MS")
    index_ts = pd.DatetimeIndex(index)
    data = {f"covid_{m:%Y_%m}": (index_ts == m).astype(float) for m in months}
    return pd.DataFrame(data, index=index_ts)


def covid_flag(index: pd.DatetimeIndex) -> pd.Series:
    """A single 0/1 'is this a COVID-disrupted month' indicator (for tree features)."""
    index_ts = pd.DatetimeIndex(index)
    inside = (index_ts >= config.COVID_WINDOW[0]) & (index_ts <= config.COVID_WINDOW[1])
    return pd.Series(inside.astype(float), index=index_ts, name="covid")


def month_fourier(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Cyclic month encoding (sin/cos) — smooth seasonality for tree/linear features."""
    index_ts = pd.DatetimeIndex(index)
    angle = 2.0 * np.pi * (index_ts.month.to_numpy() - 1) / 12.0
    return pd.DataFrame({"month_sin": np.sin(angle), "month_cos": np.cos(angle)}, index=index_ts)
