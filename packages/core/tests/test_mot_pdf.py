"""Tests for the Ministry of Tourism PDF parser (hermetic — uses extracted text)."""

from __future__ import annotations

import pandas as pd

from ave_core.contracts import validate_arrivals
from ave_core.ingest.mot_pdf import monthly_series_from_reports, parse_report

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


def test_monthly_series_is_tidy_sorted_and_contract_valid() -> None:
    df = monthly_series_from_reports([AUG_2025, JUL_2025])
    assert list(df["ds"]) == [pd.Timestamp("2025-07-01"), pd.Timestamp("2025-08-01")]
    assert list(df["y"]) == [180_000.0, 192_058.0]
    # Must satisfy the published-artifact data contract.
    validate_arrivals(df)
