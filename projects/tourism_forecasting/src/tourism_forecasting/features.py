"""Deterministic, leakage-free features: the future month index, structural-break
intervention dummies, and calendar features. Everything here is known at forecast time."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def future_index(y: pd.Series, horizon: int) -> pd.DatetimeIndex:
    """The next `horizon` month-starts after the last observation."""
    start = pd.Timestamp(y.index[-1]) + pd.offsets.MonthBegin(1)
    return pd.date_range(start, periods=horizon, freq="MS")


def intervention_dummies(
    index: pd.DatetimeIndex,
    windows: tuple[tuple[pd.Timestamp, pd.Timestamp], ...] = config.INTERVENTION_WINDOWS,
) -> pd.DataFrame:
    """One 0/1 indicator column per month inside any structural-break window.

    Columns are fixed by the windows (not by `index`), so a training frame and a future
    frame always share the same column set — the dummies absorb the 2020 COVID collapse and
    the 2026 Gulf air-bridge shock, and are all-zero for ordinary (incl. future) months.
    """
    index_ts = pd.DatetimeIndex(index)
    data: dict[str, np.ndarray] = {}
    for start, end in windows:
        for month in pd.date_range(start, end, freq="MS"):
            data[f"shock_{month:%Y_%m}"] = (index_ts == month).astype(float)
    return pd.DataFrame(data, index=index_ts)


def intervention_flag(
    index: pd.DatetimeIndex,
    windows: tuple[tuple[pd.Timestamp, pd.Timestamp], ...] = config.INTERVENTION_WINDOWS,
) -> pd.Series:
    """A single 0/1 'is this a structural-break month' indicator (for tree features)."""
    index_ts = pd.DatetimeIndex(index)
    inside = np.zeros(len(index_ts), dtype=float)
    for start, end in windows:
        inside = np.maximum(inside, ((index_ts >= start) & (index_ts <= end)).astype(float))
    return pd.Series(inside, index=index_ts, name="shock")


def month_fourier(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Cyclic month encoding (sin/cos) — smooth seasonality for tree/linear features."""
    index_ts = pd.DatetimeIndex(index)
    angle = 2.0 * np.pi * (index_ts.month.to_numpy() - 1) / 12.0
    return pd.DataFrame({"month_sin": np.sin(angle), "month_cos": np.cos(angle)}, index=index_ts)
