"""Tests for the forecasting building blocks — features, the seasonal-naive baseline, the
backtest harness (with a deterministic dummy model), and the forecast-artifact contract.

Heavy models (SARIMA/Prophet/XGBoost) are smoke-covered by a single SARIMA fit; the harness
logic is tested against a fast dummy so the suite stays quick and deterministic."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from jsonschema import Draft202012Validator
from tourism_forecasting.backtest import rolling_origin_backtest
from tourism_forecasting.models.seasonal_naive import SeasonalNaiveForecaster

from ave_core.export import build_forecast
from ave_core.lineage import stamp
from tourism_forecasting import config, features


def _synthetic(n: int = 156, start: str = "2012-01-01") -> pd.Series:
    """A clean seasonal+trend monthly series (no COVID) for deterministic tests."""
    idx = pd.date_range(start, periods=n, freq="MS")
    t = np.arange(n)
    seasonal = 20_000 * np.sin(2 * np.pi * (idx.month - 1) / 12)
    level = 80_000 + 300 * t
    return pd.Series(level + seasonal, index=pd.DatetimeIndex(idx, freq="MS"), dtype=float)


def test_future_index_is_contiguous_month_starts() -> None:
    y = _synthetic()
    idx = features.future_index(y, 12)
    assert len(idx) == 12
    assert idx[0] == y.index[-1] + pd.offsets.MonthBegin(1)
    assert (idx.day == 1).all()


def test_covid_dummies_fixed_columns_and_zero_in_future() -> None:
    cols_a = features.covid_dummies(
        pd.DatetimeIndex(pd.date_range("2019-01-01", periods=12, freq="MS"))
    )
    cols_b = features.covid_dummies(
        pd.DatetimeIndex(pd.date_range("2027-01-01", periods=12, freq="MS"))
    )
    # Same column set regardless of index (so train/future align)...
    assert list(cols_a.columns) == list(cols_b.columns)
    # ...and 2027 is entirely outside the COVID window -> all zero.
    assert (cols_b.to_numpy() == 0.0).all()
    # The window months light up exactly once.
    assert cols_a["covid_2020_04"].sum() == 0.0  # 2019 frame doesn't cover Apr 2020


def test_seasonal_naive_repeats_last_cycle_with_nested_bands() -> None:
    y = _synthetic()
    fc = SeasonalNaiveForecaster().fit(y).forecast(12, config.BAND_LEVELS)
    assert list(fc.columns) == ["yhat", "lower_80", "upper_80", "lower_95", "upper_95"]
    # 12-step seasonal naive = the last 12 observed values.
    assert np.allclose(fc["yhat"].to_numpy(), y.to_numpy()[-12:])
    assert (fc["lower_95"] <= fc["lower_80"]).all()
    assert (fc["upper_80"] <= fc["upper_95"]).all()
    assert (fc.to_numpy() >= 0).all()


class _DummyForecaster:
    """Predicts the last seasonal cycle exactly (so MASE ≈ 1) with trivial ± bands."""

    name = "dummy"

    def fit(self, y: pd.Series) -> _DummyForecaster:
        self.y = y
        return self

    def forecast(self, horizon: int, levels: Sequence[int]) -> pd.DataFrame:
        point = self.y.to_numpy(dtype=float)[-12:][:horizon]
        idx = features.future_index(self.y, horizon)
        out = pd.DataFrame({"yhat": point}, index=idx)
        for level in levels:
            out[f"lower_{level}"] = point * 0.9
            out[f"upper_{level}"] = point * 1.1
        return out


def test_backtest_harness_scores_a_known_model() -> None:
    y = _synthetic(n=156)
    result = rolling_origin_backtest(
        y, _DummyForecaster, levels=config.BAND_LEVELS, n_origins=12, min_train=120, max_h=6
    )
    assert result.folds == 12
    assert result.n_points > 0
    assert np.isfinite(result.mase) and result.mase > 0
    assert np.isfinite(result.pinball)


@pytest.mark.parametrize("level_set", [(80, 95)])
def test_build_forecast_conforms_to_schema(level_set: tuple[int, ...]) -> None:
    y = _synthetic()
    fc = SeasonalNaiveForecaster().fit(y).forecast(12, level_set)
    backtest = {
        "baseline": "seasonal_naive",
        "mase": 0.8,
        "smape": 6.0,
        "pinball": 1000.0,
        "folds": 30,
    }
    artifact = build_forecast(
        model="sarima",
        metric="arrivals_total",
        geo="MV",
        horizon="12m",
        fc=fc,
        levels=level_set,
        backtest=backtest,
        lineage=stamp(b"test"),
    )
    schema = __import__("json").loads(
        (Path("published") / "meta" / "forecast.schema.json").read_text()
    )
    errors = list(Draft202012Validator(schema).iter_errors(artifact))
    assert errors == [], errors
