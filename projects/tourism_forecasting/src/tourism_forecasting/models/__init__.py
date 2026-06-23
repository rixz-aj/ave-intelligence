"""Forecasters — one fit/forecast interface each (see base.Forecaster)."""

from __future__ import annotations

from .base import Forecaster
from .prophet_model import ProphetForecaster
from .sarimax import SarimaxForecaster
from .seasonal_naive import SeasonalNaiveForecaster
from .xgb import XGBForecaster

__all__ = [
    "Forecaster",
    "SeasonalNaiveForecaster",
    "SarimaxForecaster",
    "ProphetForecaster",
    "XGBForecaster",
]
