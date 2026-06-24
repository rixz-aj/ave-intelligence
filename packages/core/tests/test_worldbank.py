"""Hermetic tests for the World Bank WDI parser (no network — fixture payload)."""

from __future__ import annotations

import pandas as pd

from ave_core.ingest.worldbank import _parse_wdi

# Shape of a real WDI response: [metadata, [observations]], newest first, with null gaps.
_PAYLOAD = [
    {"page": 1, "total": 3},
    [
        {"date": "2024", "value": None},
        {"date": "2023", "value": 48500.0},
        {"date": "2022", "value": 47010.5},
        {"date": "2021", "value": 45120.0},
    ],
]


def test_parses_non_null_observations_sorted() -> None:
    df = _parse_wdi(_PAYLOAD)
    assert list(df.columns) == ["ds", "y"]
    assert len(df) == 3  # the null 2024 row is dropped
    assert df["ds"].iloc[0] == pd.Timestamp("2021-01-01")  # ascending
    assert df["ds"].iloc[-1] == pd.Timestamp("2023-01-01")
    assert df["y"].iloc[-1] == 48500.0


def test_empty_payload_returns_empty_frame() -> None:
    for payload in ([{"message": "no data"}, None], [], {"x": 1}):
        df = _parse_wdi(payload)
        assert df.empty
        assert list(df.columns) == ["ds", "y"]
