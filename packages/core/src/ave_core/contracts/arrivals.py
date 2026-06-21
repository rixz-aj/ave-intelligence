"""Pandera contract for a monthly arrivals (or any single-metric) time series.

The canonical tidy shape the platform models from and exports as `series` artifacts:
one row per month, `ds` a unique month-start datetime, `y` a non-negative float
(nullable to allow genuine gaps — never fabricate). Uses the stable object API.
"""

from __future__ import annotations

import pandas as pd
import pandera as pa

arrivals_schema = pa.DataFrameSchema(  # type: ignore[no-untyped-call]
    columns={
        "ds": pa.Column("datetime64[ns]", unique=True, coerce=True, nullable=False),
        "y": pa.Column(float, checks=pa.Check.ge(0), nullable=True, coerce=True),
    },
    strict=True,
    ordered=True,
    name="arrivals",
)


def validate_arrivals(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and return the frame (sorted by ds). Raises on schema drift."""
    validated = arrivals_schema.validate(df)
    return validated.sort_values("ds").reset_index(drop=True)
