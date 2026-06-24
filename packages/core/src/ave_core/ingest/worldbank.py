"""Ingest World Bank WDI indicators (free, no key) — the source-country macro covariates
for the demand-model elasticity layer.

The public API returns `[metadata, observations]`; we keep the non-null observations as a
tidy annual DataFrame[ds, y]. Used for source-country real GDP per capita, CPI and exchange
rates (the income and relative-price terms in the tourism-demand ARDL). See docs/DATA-SOURCES.md.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

BASE_URL = "https://api.worldbank.org/v2"

# Indicator codes used by the demand model.
GDP_PER_CAPITA = "NY.GDP.PCAP.KD"  # real GDP per capita, constant USD
CPI = "FP.CPI.TOTL"  # consumer price index
EXCHANGE_RATE = "PA.NUS.FCRF"  # official exchange rate, LCU per USD (period average)


def _parse_wdi(payload: Any) -> pd.DataFrame:
    """Parse a World Bank API JSON payload into a tidy annual DataFrame[ds, y].

    `payload` is the parsed `[metadata, observations]` list. Non-null observations only,
    `ds` a year-start Timestamp, sorted ascending. Returns an empty frame for no data.
    """
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        return pd.DataFrame({"ds": pd.Series(dtype="datetime64[ns]"), "y": pd.Series(dtype=float)})
    records = [
        {"ds": pd.Timestamp(year=int(obs["date"]), month=1, day=1), "y": float(obs["value"])}
        for obs in payload[1]
        if obs.get("value") is not None
    ]
    df = pd.DataFrame(records)
    return df.sort_values("ds").reset_index(drop=True)


def fetch_indicator(iso3: str, indicator: str, *, timeout: int = 30) -> pd.DataFrame:
    """Fetch a WDI indicator for one country (ISO-3) as a tidy annual DataFrame[ds, y]."""
    url = f"{BASE_URL}/country/{iso3}/indicator/{indicator}"
    response = requests.get(url, params={"format": "json", "per_page": "400"}, timeout=timeout)
    response.raise_for_status()
    return _parse_wdi(response.json())
