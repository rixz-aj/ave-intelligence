"""Offline tests for the MMA Viya embedded-chart scraper.

Uses a tiny fixture mirroring the real page structure (JS single-quoted category
labels, Highcharts `categories:`/`data:` pairs) so the parser is locked without
hitting the network.
"""

from __future__ import annotations

import pandas as pd

from ave_core.ingest import mma_viya

# Mirrors the real Viya page: three charts at different frequencies, plus a decoy
# numeric `data:` array whose length matches no categories block (must be ignored).
_FIXTURE = """
<script>
  Highcharts.chart('monthly', {
    xAxis: { categories: ['May 2021', 'Jun 2021', 'Jul 2021'] },
    plotOptions: { pie: { colors: ['#FF9800', '#FF5722'] } },
    series: [ { showInLegend: false, name: ' ', data: [64613, 56166, 101818] } ]
  });
  Highcharts.chart('quarterly', {
    xAxis: { categories: ['Q2 2011', 'Q3 2011'] },
    series: [ { showInLegend: false, name: ' ', data: [200350, 221205] } ]
  });
  Highcharts.chart('annual', {
    xAxis: { categories: [1988, 1989, 1990, 1991] },
    series: [ { showInLegend: false, name: ' ', data: [155757, 158488, 195156, 196112] } ]
  });
  // decoy: a numeric data array with no equal-length date axis -> skipped
  Highcharts.chart('pie', { series: [ { data: [10, 20, 30, 40, 50, 60, 70] } ] });
</script>
"""


def test_parses_all_three_frequencies() -> None:
    charts = mma_viya.parse_embedded_charts(_FIXTURE)
    assert set(charts) == {"A", "Q", "M"}


def test_annual_axis_maps_years_to_january_first() -> None:
    annual = mma_viya.parse_embedded_charts(_FIXTURE)["A"]
    assert len(annual) == 4
    assert list(annual["y"]) == [155757.0, 158488.0, 195156.0, 196112.0]
    assert annual["ds"].iloc[0] == pd.Timestamp("1988-01-01")
    assert annual["ds"].iloc[-1] == pd.Timestamp("1991-01-01")


def test_monthly_and_quarterly_dates() -> None:
    charts = mma_viya.parse_embedded_charts(_FIXTURE)
    assert charts["M"]["ds"].iloc[0] == pd.Timestamp("2021-05-01")
    assert charts["M"]["ds"].iloc[-1] == pd.Timestamp("2021-07-01")
    # Q2 -> April, Q3 -> July
    assert charts["Q"]["ds"].iloc[0] == pd.Timestamp("2011-04-01")
    assert charts["Q"]["ds"].iloc[-1] == pd.Timestamp("2011-07-01")


def test_decoy_numeric_array_is_ignored() -> None:
    # The 7-element pie data array has no matching categories -> not a chart.
    charts = mma_viya.parse_embedded_charts(_FIXTURE)
    assert all(len(df) in (2, 3, 4) for df in charts.values())


def test_classify_rejects_non_date_axes() -> None:
    assert mma_viya._classify([1988, 1989]) == "A"
    assert mma_viya._classify(["Q1 2020"]) == "Q"
    assert mma_viya._classify(["Jan 2020"]) == "M"
    assert mma_viya._classify(["red", "blue"]) is None
    assert mma_viya._classify([1.5, 2.5]) is None
