"""Tests for the Ministry of Tourism PDF parser (hermetic — uses extracted text)."""

from __future__ import annotations

import pandas as pd

from ave_core.contracts import validate_arrivals
from ave_core.ingest.mot_pdf import (
    discover_report_urls,
    monthly_series_from_reports,
    parse_report,
)

# Real layout-extracted lines from the Aug 2025 MoT monthly report (pdftotext -layout).
AUG_2025 = """
August 2025
Table 1: TOURIST ARRIVALS BY NATIONALITY, January - August 2025
                                      2024     2025 Change   2025           2024      2025    % Change          2025      2025
TOTAL TOURIST ARRIVALS                      176,175   192,058        9.0   100.0 1,359,232   1,486,926        9.4         100.0
"""

JUL_2025 = """
July 2025
Table 1: TOURIST ARRIVALS BY NATIONALITY, January - July 2025
TOTAL TOURIST ARRIVALS                      170,000   180,000        5.9   100.0 1,183,057   1,294,868        9.5         100.0
"""


def test_parse_report_extracts_current_month_total() -> None:
    parsed = parse_report(AUG_2025)
    assert parsed["period"] == pd.Timestamp("2025-08-01")
    assert parsed["arrivals"] == 192_058
    assert parsed["prior_year_month"] == 176_175
    assert parsed["ytd"] == 1_486_926


# Older (2021-era) reports have no standalone month line — the period is in the
# Table-1 title range, where the LAST month is the report's current month.
FEB_2021_OLD = """
2021
TOURIST ARRIVALS BY NATIONALITY, January - February 2021
TOTAL TOURIST ARRIVALS                  149,785   96,882   -35.3   100.0   323,132   188,985   -41.5   100.0
"""


def test_parse_report_handles_old_range_title_format() -> None:
    parsed = parse_report(FEB_2021_OLD)
    assert parsed["period"] == pd.Timestamp("2021-02-01")
    assert parsed["arrivals"] == 96_882
    assert parsed["ytd"] == 188_985


# April 2021's prior-year column is April 2020 = 13 (borders closed) — non-comma. Column
# parsing must read the current month (91,200), not slide over to the prior-year YTD.
APR_2021_COVID_PRIOR = """
2021
TOURIST ARRIVALS BY NATIONALITY, January - April 2021
TOTAL TOURIST ARRIVALS   13   91,200   NA   100.0   382,775   389,770   1.8   100.0
"""


def test_parse_report_handles_near_zero_covid_prior_year_column() -> None:
    parsed = parse_report(APR_2021_COVID_PRIOR)
    assert parsed["period"] == pd.Timestamp("2021-04-01")
    assert parsed["arrivals"] == 91_200
    assert parsed["prior_year_month"] == 13
    assert parsed["ytd"] == 389_770


def test_discover_report_urls_dedupes_and_absolutizes() -> None:
    html = (
        '<a href="/dms/document/aaaa1111.pdf">January 2025</a>'
        '<a href="/dms/document/bbbb2222.pdf">February 2025</a>'
        '<a href="/dms/document/aaaa1111.pdf">dup link</a>'
    )
    assert discover_report_urls(html, base_url="https://x") == [
        "https://x/dms/document/aaaa1111.pdf",
        "https://x/dms/document/bbbb2222.pdf",
    ]


def test_monthly_series_is_tidy_sorted_and_contract_valid() -> None:
    df = monthly_series_from_reports([AUG_2025, JUL_2025])
    assert list(df["ds"]) == [pd.Timestamp("2025-07-01"), pd.Timestamp("2025-08-01")]
    assert list(df["y"]) == [180_000.0, 192_058.0]
    # Must satisfy the published-artifact data contract.
    validate_arrivals(df)
