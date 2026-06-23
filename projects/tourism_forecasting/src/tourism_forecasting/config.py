"""Phase-1 forecasting configuration — horizons, the COVID break, backtest settings.

One place for every load-bearing constant so the modeling choices are auditable (and so
the COVID structural-break handling is explicit, never silently fitted over).
"""

from __future__ import annotations

import pandas as pd

# Target series (published monthly arrivals, v2 = the long 2009→ MoT-PDF series).
METRIC = "arrivals_total"
GEO = "MV"
SERIES_VERSION = 3

# Forecast shape.
HORIZON_MONTHS = 12
HORIZON_LABEL = "12m"
SEASONAL_PERIOD = 12
BAND_LEVELS: tuple[int, ...] = (80, 95)  # prediction-interval levels in the artifact

# Structural breaks handled with explicit intervention dummies so the seasonal/trend
# structure is estimated from undistorted months — never deleted, never silently fitted
# across. Two known external shocks:
#   • COVID: arrivals were literally 0 in Apr–Jun 2020 (borders closed); abnormal recovery
#     through mid-2021.
#   • 2026 Gulf air-bridge shock: a Middle East conflict from late Feb 2026 closed Gulf
#     airspace / transit hubs (~30–35% of arrivals route via them), cancelling ~500 flights
#     to Malé → Mar 2026 −20.7% / Apr 2026 ≈−25% YoY after a RECORD Jan–Feb. A transient
#     connectivity shock (May rebounded after the early-April ceasefire), so we absorb Mar–Apr
#     2026 and forecast the underlying path absent further disruption.
COVID_WINDOW: tuple[pd.Timestamp, pd.Timestamp] = (
    pd.Timestamp("2020-03-01"),
    pd.Timestamp("2021-06-01"),
)
CONFLICT_2026_WINDOW: tuple[pd.Timestamp, pd.Timestamp] = (
    pd.Timestamp("2026-03-01"),
    pd.Timestamp("2026-04-01"),
)
INTERVENTION_WINDOWS: tuple[tuple[pd.Timestamp, pd.Timestamp], ...] = (
    COVID_WINDOW,
    CONFLICT_2026_WINDOW,
)

# Rolling-origin backtest. Expanding window, refit every origin. MIN_TRAIN keeps the first fit
# anchored to a full pre-COVID history; N_ORIGINS recent origins keeps runtime sane while
# covering the post-COVID regime the forecast actually operates in.
BACKTEST_MIN_TRAIN = 120  # months (~2009→2018) before the first evaluated origin
BACKTEST_N_ORIGINS = 30
BACKTEST_MAX_H = 12
