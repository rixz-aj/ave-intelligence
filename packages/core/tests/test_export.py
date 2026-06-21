"""Tests for lineage stamping and series/manifest export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ave_core.export import build_series, load_manifest, upsert_artifact, write_series
from ave_core.lineage import stamp


def test_lineage_stamp_shape() -> None:
    lineage = stamp(b"hello")
    d = lineage.as_dict()
    assert set(d) == {"runId", "gitSha", "inputHash"}
    assert d["inputHash"].startswith("sha256:")


def test_build_and_write_series_is_immutable(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {"ds": pd.to_datetime(["2026-01-01", "2026-02-01"]), "y": [100.0, 110.0]}
    )
    artifact = build_series(
        metric="arrivals_total", geo="MV", freq="M", unit="arrivals", df=df, lineage=stamp(b"x")
    )
    assert artifact["points"][0] == {"ds": "2026-01-01", "y": 100.0}

    path = write_series(artifact, tmp_path, version=1)
    assert path.exists()
    assert json.loads(path.read_text())["metric"] == "arrivals_total"

    with pytest.raises(FileExistsError):
        write_series(artifact, tmp_path, version=1)  # versions never overwrite


def test_manifest_upsert_is_keyed_by_id() -> None:
    manifest = load_manifest(Path("/nonexistent"))
    upsert_artifact(manifest, {"id": "a", "type": "series", "version": 1})
    upsert_artifact(manifest, {"id": "a", "type": "series", "version": 2})
    assert len(manifest["artifacts"]) == 1
    assert manifest["artifacts"][0]["version"] == 2
