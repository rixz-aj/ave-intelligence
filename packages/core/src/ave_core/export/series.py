"""Build and write `series` artifacts conforming to published/meta/series.schema.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ave_core.lineage import Lineage

SCHEMA_VERSION = "1.0.0"


def build_series(
    *,
    metric: str,
    geo: str,
    freq: str,
    unit: str,
    df: pd.DataFrame,
    lineage: Lineage,
) -> dict[str, Any]:
    """Build a series artifact dict from a tidy DataFrame[ds, y].

    `df` is expected to already pass `ave_core.contracts.validate_arrivals`.
    """
    points: list[dict[str, Any]] = []
    for ds_value, y_value in zip(df["ds"], df["y"], strict=True):
        points.append(
            {
                "ds": pd.Timestamp(ds_value).strftime("%Y-%m-%d"),
                "y": None if pd.isna(y_value) else float(y_value),
            }
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "metric": metric,
        "geo": geo,
        "freq": freq,
        "unit": unit,
        "points": points,
        "lineage": lineage.as_dict(),
    }


def write_series(artifact: dict[str, Any], published_root: Path, version: int) -> Path:
    """Write a series artifact to published/series/{metric}/{geo}/v{version}.json.

    Versions are immutable — refuse to overwrite an existing version.
    """
    out: Path = (
        published_root / "series" / artifact["metric"] / artifact["geo"] / f"v{version}.json"
    )
    if out.exists():
        raise FileExistsError(f"{out} already exists; bump the version (artifacts are immutable)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n")
    return out
