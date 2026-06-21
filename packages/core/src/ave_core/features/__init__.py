"""Feature builders — lag, rolling-window, calendar, and exogenous regressors.

Shared across projects (forecasting features, pricing features). Phase 1 fills this
in: `lags(series, [1,12])`, `rolling(series, window)`, `calendar(index)` (month,
quarter, holiday flags), and exogenous joins (bednights/occupancy/FX). Pure,
deterministic, and property-tested with hypothesis.
"""

from __future__ import annotations
