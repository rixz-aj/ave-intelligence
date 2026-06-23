"""Load the published monthly arrivals series into a modelling-ready pandas Series."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import config


def load_arrivals(
    published_root: Path = Path("published"), version: int = config.SERIES_VERSION
) -> pd.Series:
    """Return monthly arrivals as a float Series indexed by month-start (freq 'MS').

    Reads the committed series artifact (the same bytes the website consumes), so the
    model trains on exactly the published data.
    """
    path = published_root / "series" / config.METRIC / config.GEO / f"v{version}.json"
    artifact = json.loads(path.read_text())
    points = artifact["points"]
    index = pd.to_datetime([p["ds"] for p in points])
    series = pd.Series(
        [float(p["y"]) for p in points], index=index, name=config.METRIC, dtype=float
    )
    series = series.sort_index()
    series.index = pd.DatetimeIndex(series.index, freq="MS")
    return series
