"""Ingest MMA Statistics Database (Viya) series into `data/raw`.

Primary target: series **104 = Total tourist arrivals**. Covariates: 205 bednights,
216 occupancy, 210 average stay. See docs/DATA-SOURCES.md.

⚠️ The JSON API (https://database.mma.gov.mv/api/series?ids=104) is **token-gated** —
it 302-redirects to /viya/mma-login, with no documented self-signup. The reliable
*tokenless* path is the public Viya series page, which embeds its charts' data inline
as Highcharts config. Verified 2026-06-23: the page carries three series at different
frequencies — **annual 1988→present (full)**, **quarterly (~last 60q)** and
**monthly (windowed to ~last 60m)**. The long history is therefore available at
ANNUAL frequency here; the long *monthly* series comes from the MoT PDFs
(`ave_core.ingest.mot_pdf`). This connector scrapes the embedded charts.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from ave_core.contracts import validate_arrivals

# Series id -> tidy metric name used downstream (and in published artifact paths).
SERIES: dict[int, str] = {
    104: "arrivals_total",
    205: "bednights_total",
    216: "occupancy_total",
    210: "avg_stay",
}

VIYA_PAGE_URL = "https://database.mma.gov.mv/viya/series/{series_id}"
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)

# The embedded Highcharts config exposes each chart as `categories: [...]` (the x axis)
# followed by `data: [...]` (the y values), using JS single-quoted string literals.
_CATEGORIES = re.compile(r"categories:\s*(\[[^\]]*\])")
_DATA = re.compile(r"data:\s*(\[\s*-?\d[\d.,\s\-]*\])")  # numeric arrays only
_MONTHS = {
    name: num
    for num, name in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}
_MONTH_LABEL = re.compile(r"^([A-Z][a-z]{2})\s+(\d{4})$")
_QUARTER_LABEL = re.compile(r"^Q([1-4])\s+(\d{4})$")


def fetch_page(series_id: int, *, timeout: int = 60) -> str:
    """Fetch the public Viya series page HTML (no token required)."""
    response = requests.get(
        VIYA_PAGE_URL.format(series_id=series_id),
        headers={"User-Agent": _UA},
        timeout=timeout,
    )
    response.raise_for_status()
    return str(response.text)


def _literal_arrays(pattern: re.Pattern[str], html: str) -> list[tuple[int, list[Any]]]:
    """Parse every array matched by `pattern` with `ast.literal_eval` (handles JS single
    quotes), tagged with its source position. Unparseable matches are skipped."""
    out: list[tuple[int, list[Any]]] = []
    for match in pattern.finditer(html):
        try:
            value = ast.literal_eval(match.group(1))
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, list):
            out.append((match.start(), value))
    return out


def _classify(categories: list[Any]) -> str | None:
    """Infer a series frequency ('A'/'Q'/'M') from its x-axis category labels, else None."""
    if categories and all(isinstance(c, int) and 1900 <= c <= 2100 for c in categories):
        return "A"
    if categories and all(isinstance(c, str) and _QUARTER_LABEL.match(c) for c in categories):
        return "Q"
    if categories and all(isinstance(c, str) and _MONTH_LABEL.match(c) for c in categories):
        return "M"
    return None


def _to_timestamps(categories: list[Any], freq: str) -> list[pd.Timestamp]:
    """Map x-axis category labels to month-start Timestamps for the given frequency."""
    stamps: list[pd.Timestamp] = []
    for cat in categories:
        if freq == "A":
            stamps.append(pd.Timestamp(year=int(cat), month=1, day=1))
        elif freq == "Q":
            match = _QUARTER_LABEL.match(str(cat))
            assert match is not None  # guaranteed by _classify
            quarter, year = int(match.group(1)), int(match.group(2))
            stamps.append(pd.Timestamp(year=year, month=(quarter - 1) * 3 + 1, day=1))
        else:  # 'M'
            match = _MONTH_LABEL.match(str(cat))
            assert match is not None  # guaranteed by _classify
            stamps.append(
                pd.Timestamp(year=int(match.group(2)), month=_MONTHS[match.group(1)], day=1)
            )
    return stamps


def parse_embedded_charts(html: str) -> dict[str, pd.DataFrame]:
    """Extract the embedded charts as tidy DataFrame[ds, y], keyed by frequency.

    Pairs each numeric `data:` array with the nearest preceding `categories:` array of
    equal length (one chart block), classifies it by label format, and returns the
    annual/quarterly/monthly series found on the page.
    """
    category_arrays = _literal_arrays(_CATEGORIES, html)
    charts: dict[str, pd.DataFrame] = {}
    for data_pos, values in _literal_arrays(_DATA, html):
        candidates = [
            (pos, cats)
            for pos, cats in category_arrays
            if pos < data_pos and len(cats) == len(values)
        ]
        if not candidates:
            continue
        _, categories = max(candidates, key=lambda pair: pair[0])  # nearest preceding
        freq = _classify(categories)
        if freq is None:
            continue
        frame = pd.DataFrame(
            {"ds": _to_timestamps(categories, freq), "y": [float(v) for v in values]}
        )
        charts[freq] = frame.drop_duplicates("ds").sort_values("ds").reset_index(drop=True)
    return charts


def fetch_series(series_id: int, freq: str = "A", token: str | None = None) -> pd.DataFrame:
    """Return a tidy, contract-validated DataFrame[ds, y] for one MMA series + frequency.

    The tokenless path scrapes the embedded Viya page charts; `freq` selects which of
    the page's frequencies to return ('A' annual is the long-history one). `token` is
    accepted for forward-compatibility with the gated JSON API but is not yet used.
    """
    charts = parse_embedded_charts(fetch_page(series_id))
    if freq not in charts:
        available = ", ".join(sorted(charts)) or "none"
        raise ValueError(f"frequency {freq!r} not found on Viya page (available: {available})")
    return validate_arrivals(charts[freq])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest MMA Viya series into data/raw")
    parser.add_argument("--series", type=int, default=104, help="MMA series id (default 104)")
    parser.add_argument(
        "--freq", default="A", choices=["A", "Q", "M"], help="frequency (default A)"
    )
    parser.add_argument("--out", type=Path, default=Path("data/raw"), help="output dir")
    parser.add_argument("--token", default=None, help="MMA API Bearer token (currently unused)")
    args = parser.parse_args(argv)

    df = fetch_series(args.series, args.freq, args.token)
    args.out.mkdir(parents=True, exist_ok=True)
    metric = SERIES.get(args.series, str(args.series))
    out = args.out / f"mma_{metric}_{args.freq}.parquet"
    df.to_parquet(out)
    print(f"wrote {out}  ({len(df)} points, {df['ds'].min():%Y-%m} → {df['ds'].max():%Y-%m})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
