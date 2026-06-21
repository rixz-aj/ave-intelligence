"""Ingest Ministry of Tourism monthly statistics PDFs (the public, no-auth path).

Each monthly report (https://www.tourism.gov.mv/en/statistics/publications) carries a
`TOTAL TOURIST ARRIVALS` row in Table 1 with, in column order:
    [prior-year month, current-year month, change %, share %,
     prior-year YTD, current-year YTD, change %, share %]
and the period in either a standalone `<Month> <Year>` line (newer reports) or the
Table-1 title range (older reports). We extract the current-year monthly total → one
tidy `(ds, y)` point per report; many reports compose the monthly arrivals series.

This is the working Phase-0 source: the MMA Viya API (series 104) is auth-gated
(redirects to login), so the public PDFs are the reliable free path. See
docs/DATA-SOURCES.md. By-market (per-nationality) extraction is a Phase-1 extension.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://www.tourism.gov.mv"
_DOC = re.compile(r"/dms/document/[a-f0-9]+\.pdf")
# The TOTAL row is read by COLUMN POSITION (split on whitespace, strip the 3-word label),
# not by pattern-matching numbers. This is robust to near-zero COVID values like "13" and
# to "NA" cells — earlier comma-only matching dropped the non-comma prior-year-month cell
# and shifted every column left.
_LABEL = re.compile(r"\s*TOTAL\s+TOURIST\s+ARRIVALS\s*(.*)", re.IGNORECASE)
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
_MONTH_YEAR = re.compile(r"\b([A-Za-z]+)\s+(\d{4})\b")


def year_listing_url(year: int) -> str:
    """URL of the Ministry of Tourism publications listing for a given year."""
    return f"{BASE_URL}/en/statistics/publications/year-{year}"


def discover_report_urls(listing_html: str, base_url: str = BASE_URL) -> list[str]:
    """Extract absolute /dms/document/*.pdf URLs from a publications listing page.

    Order-preserving and de-duplicated. The month each PDF covers is read from the PDF
    itself (parse_report), so listing order doesn't need to be trusted.
    """
    seen: dict[str, None] = {}
    for path in _DOC.findall(listing_html):
        seen.setdefault(path, None)
    return [base_url + path for path in seen]


def fetch_text(url: str, *, timeout: int = 30) -> str:
    """Download a page as text (used for the listing HTML)."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return str(response.text)


def download_pdf(url: str, dest: Path, *, timeout: int = 60) -> Path:
    """Download a PDF to `dest` (skips if already present, for re-run friendliness)."""
    if not dest.exists():
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)
    return dest


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
    match = _LABEL.match(_find_total_line(text))
    if match is None:  # pragma: no cover - _find_total_line already guarantees the prefix
        raise ValueError("could not isolate the TOTAL row columns")
    # Column order: [0] prior-year month, [1] current-year month, [2] % change, [3] share,
    #               [4] prior-year YTD, [5] current-year YTD, [6] % change, [7] share.
    cols = match.group(1).split()
    if len(cols) < 2:
        raise ValueError(f"unexpected TOTAL row layout: {_find_total_line(text)!r}")
    arrivals = _to_count(cols[1])
    if arrivals is None:
        raise ValueError(f"could not read current-month arrivals from: {cols!r}")
    return {
        "period": period,
        "arrivals": arrivals,
        "prior_year_month": _to_count(cols[0]),
        "ytd": _to_count(cols[5]) if len(cols) > 5 else None,
    }


def _to_count(token: str) -> int | None:
    """Parse a count cell ('176,175', '13') to int; return None for non-counts ('NA', '9.0')."""
    cleaned = token.replace(",", "")
    return int(cleaned) if cleaned.lstrip("-").isdigit() else None


def monthly_series_from_reports(texts: list[str]) -> pd.DataFrame:
    """Build a tidy, sorted, de-duplicated DataFrame[ds, y] from many report texts."""
    rows = pd.DataFrame([parse_report(t) for t in texts])
    df = pd.DataFrame({"ds": pd.to_datetime(rows["period"]), "y": rows["arrivals"].astype(float)})
    return df.drop_duplicates("ds").sort_values("ds").reset_index(drop=True)


def _find_period(text: str) -> pd.Timestamp:
    # Strategy 1: a standalone "<Month> <Year>" line (newer reports, e.g. "August 2025").
    for line in text.splitlines():
        match = _PERIOD.match(line)
        if match and match.group(1).lower() in _MONTHS:
            return pd.Timestamp(
                year=int(match.group(2)), month=_MONTHS[match.group(1).lower()], day=1
            )
    # Strategy 2: the Table-1 title range ("...January - February 2021"). Present in BOTH
    # old and new layouts; the LAST month-year pair is the report's current month.
    for line in text.splitlines():
        if "ARRIVALS BY NATIONALITY" in line.upper():
            pairs = [
                (m.group(1).lower(), m.group(2))
                for m in _MONTH_YEAR.finditer(line)
                if m.group(1).lower() in _MONTHS
            ]
            if pairs:
                month, year = pairs[-1]
                return pd.Timestamp(year=int(year), month=_MONTHS[month], day=1)
    raise ValueError("could not find a period (no '<Month> <Year>' line or Table-1 title)")


def _find_total_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith("TOTAL TOURIST ARRIVALS"):
            return line
    raise ValueError("could not find the 'TOTAL TOURIST ARRIVALS' row")
