"""Tests for the seasonal-naive baseline and accuracy metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ave_core.eval import mase, seasonal_naive, smape


def _monthly_series(values: list[float]) -> pd.Series:
    index = pd.date_range("2010-01-01", periods=len(values), freq="MS")
    return pd.Series(values, index=index, name="y")


def test_seasonal_naive_repeats_last_cycle() -> None:
    y = _monthly_series([float(i % 12) for i in range(36)])
    forecast = seasonal_naive(y, horizon=12, m=12)
    assert len(forecast) == 12
    # last 12 obs of this synthetic series are exactly 0..11, so the forecast repeats them
    np.testing.assert_allclose(forecast.to_numpy(), np.arange(12.0))
    assert forecast.index[0] == pd.Timestamp("2013-01-01")


def test_seasonal_naive_requires_full_cycle() -> None:
    y = _monthly_series([1.0, 2.0, 3.0])
    try:
        seasonal_naive(y, horizon=6, m=12)
    except ValueError:
        return
    raise AssertionError("expected ValueError for series shorter than m")


def test_mase_zero_for_perfect_forecast() -> None:
    # Training series needs a non-zero seasonal-naive error (a trend gives scale=12),
    # otherwise MASE's scale denominator is 0 and the metric is undefined (inf).
    train = _monthly_series([float(i) for i in range(36)])
    truth = _monthly_series([100.0, 110.0, 120.0])
    assert mase(truth, truth, train, m=12) == 0.0


def test_mase_undefined_for_flat_seasonal_series() -> None:
    # A perfectly periodic series has zero seasonal error → MASE scale is 0 → inf.
    train = _monthly_series([float(i % 12) for i in range(36)])
    truth = _monthly_series([0.0, 1.0, 2.0])
    assert mase(truth, truth, train, m=12) == float("inf")


def test_smape_zero_for_perfect_forecast() -> None:
    truth = _monthly_series([10.0, 20.0, 30.0])
    assert smape(truth, truth) == 0.0
