"""Phase-1 forecasting configuration — horizons, the COVID break, backtest settings.

One place for every load-bearing constant so the modeling choices are auditable (and so
the COVID structural-break handling is explicit, never silently fitted over).
"""

from __future__ import annotations

import pandas as pd

# Target series (published monthly arrivals, v2 = the long 2009→ MoT-PDF series).
METRIC = "arrivals_total"
GEO = "MV"
SERIES_VERSION = 2

# Forecast shape.
HORIZON_MONTHS = 12
HORIZON_LABEL = "12m"
SEASONAL_PERIOD = 12
BAND_LEVELS: tuple[int, ...] = (80, 95)  # prediction-interval levels in the artifact

# COVID structural break. Arrivals were literally 0 in Apr–Jun 2020 (borders closed) and the
# recovery through mid-2021 was abnormal. We flag this window with intervention dummies so the
# seasonal/trend structure is estimated from the undistorted months — never deleted, never
# silently fitted across. Forecast months (2026+) carry no COVID effect.
COVID_WINDOW: tuple[pd.Timestamp, pd.Timestamp] = (
    pd.Timestamp("2020-03-01"),
    pd.Timestamp("2021-06-01"),
)

# Rolling-origin backtest. Expanding window, refit every origin. MIN_TRAIN keeps the first fit
# anchored to a full pre-COVID history; N_ORIGINS recent origins keeps runtime sane while
# covering the post-COVID regime the forecast actually operates in.
BACKTEST_MIN_TRAIN = 120  # months (~2009→2018) before the first evaluated origin
BACKTEST_N_ORIGINS = 30
BACKTEST_MAX_H = 12
