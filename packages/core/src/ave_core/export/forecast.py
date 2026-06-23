"""Build and write `forecast` artifacts conforming to published/meta/forecast.schema.json."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from ave_core.lineage import Lineage

SCHEMA_VERSION = "1.0.0"


def build_forecast(
    *,
    model: str,
    metric: str,
    geo: str,
    horizon: str,
    fc: pd.DataFrame,
    levels: Sequence[int],
    backtest: dict[str, Any],
    lineage: Lineage,
) -> dict[str, Any]:
    """Build a forecast artifact from a forecast DataFrame.

    `fc` is indexed by future month-start and carries `yhat` plus `lower_{L}`/`upper_{L}`
    columns for each prediction-interval level in `levels` (e.g. 80, 95). `backtest` is the
    embedded honesty block ({baseline, mase, smape, pinball, folds}).
    """
    points: list[dict[str, Any]] = []
    for ds_value, row in fc.iterrows():
        bands = [
            {
                "level": int(level),
                "lower": float(row[f"lower_{level}"]),
                "upper": float(row[f"upper_{level}"]),
            }
            for level in levels
        ]
        points.append(
            {
                "ds": pd.Timestamp(ds_value).strftime("%Y-%m-%d"),
                "yhat": float(row["yhat"]),
                "bands": bands,
            }
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "model": model,
        "metric": metric,
        "geo": geo,
        "horizon": horizon,
        "points": points,
        "backtest": backtest,
        "lineage": lineage.as_dict(),
    }


def write_forecast(artifact: dict[str, Any], published_root: Path, version: int) -> Path:
    """Write a forecast artifact to published/forecasts/{model}/{horizon}/v{version}.json.

    Versions are immutable — refuse to overwrite an existing version.
    """
    out: Path = (
        published_root / "forecasts" / artifact["model"] / artifact["horizon"] / f"v{version}.json"
    )
    if out.exists():
        raise FileExistsError(f"{out} already exists; bump the version (artifacts are immutable)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n")
    return out
