"""Ingest Ministry of Tourism monthly statistics PDFs (the public, no-auth path).

Each monthly report (https://www.tourism.gov.mv/en/statistics/publications) carries a
`TOTAL TOURIST ARRIVALS` row in Table 1 with, in column order:
    [prior-year month, current-year month, change %, share %,
     prior-year YTD, current-year YTD, change %, share %]
and a `<Month> <Year>` header. We extract the current-year monthly total → one tidy
`(ds, y)` point per report; many reports compose the monthly arrivals series.

This is the working Phase-0 source: the MMA Viya API (series 104) is auth-gated
(redirects to login), so the public PDFs are the reliable free path. See
docs/DATA-SOURCES.md. By-market (per-nationality) extraction is a Phase-1 extension.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

# Arrival counts in these reports are always >= 100,000 → always comma-grouped.
# Matching only comma-grouped integers cleanly skips percentages like "9.0"/"100.0".
_COUNT = re.compile(r"\d{1,3}(?:,\d{3})+")
_MONTHS = {
    name: num
    for num, name in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ],
        start=1,
    )
}
_PERIOD = re.compile(r"^\s*([A-Za-z]+)\s+(\d{4})\s*$")


def extract_text(pdf_path: Path) -> str:
    """Extract layout-preserving text from a PDF via poppler's `pdftotext -layout`."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "pdftotext (poppler) not found. Install poppler, or swap in pdfplumber here."
        ) from exc
    return result.stdout


def parse_report(text: str) -> dict[str, object]:
    """Parse one monthly report's text into {period, arrivals, ytd, prior_year_month}.

    `period` is the month-start Timestamp; `arrivals` is the current-year monthly total.
    Raises ValueError if the period header or the TOTAL row can't be located.
    """
    period = _find_period(text)
    total_line = _find_total_line(text)
    counts = [int(tok.replace(",", "")) for tok in _COUNT.findall(total_line)]
    if len(counts) < 2:
        raise ValueError(f"could not parse counts from TOTAL row: {total_line!r}")
    # Comma-grouped counts on the TOTAL row, in column order:
    #   [0] prior-year month, [1] current-year month, [2] prior-year YTD, [3] current-year YTD.
    # (Percentages/shares like 9.0 / 100.0 aren't comma-grouped, so they're excluded.)
    return {
        "period": period,
        "arrivals": counts[1],
        "prior_year_month": counts[0],
        "ytd": counts[3] if len(counts) >= 4 else None,
    }


def monthly_series_from_reports(texts: list[str]) -> pd.DataFrame:
    """Build a tidy, sorted, de-duplicated DataFrame[ds, y] from many report texts."""
    rows = pd.DataFrame([parse_report(t) for t in texts])
    df = pd.DataFrame({"ds": pd.to_datetime(rows["period"]), "y": rows["arrivals"].astype(float)})
    return df.drop_duplicates("ds").sort_values("ds").reset_index(drop=True)


def _find_period(text: str) -> pd.Timestamp:
    for line in text.splitlines():
        match = _PERIOD.match(line)
        if match:
            month = _MONTHS.get(match.group(1).lower())
            if month:
                return pd.Timestamp(year=int(match.group(2)), month=month, day=1)
    raise ValueError("could not find a '<Month> <Year>' period header")


def _find_total_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith("TOTAL TOURIST ARRIVALS"):
            return line
    raise ValueError("could not find the 'TOTAL TOURIST ARRIVALS' row")
