"""Publish the long-history ANNUAL arrivals series from the MMA Viya page.

The tokenless MMA Viya series page embeds a full annual total-arrivals chart
(1988→present) as Highcharts config. This script scrapes it via
`ave_core.ingest.mma_viya`, caches the raw page bytes for lineage, and writes a
`series` artifact + manifest entry into published/.

This is the long-arc companion to the monthly series (which only reaches 2009 via
MoT PDFs). Frequencies are kept SEPARATE per the two-frequency rule — the annual
series is context/structural, never blended into the monthly forecaster.

Usage:
    uv run python scripts/backfill_annual_mma.py
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd

from ave_core.export import (
    build_series,
    file_hash,
    load_manifest,
    upsert_artifact,
    write_manifest,
    write_series,
)
from ave_core.ingest import mma_viya
from ave_core.lineage import stamp

ARTIFACT_ID = "arrivals-total-mv-annual"
METRIC = "arrivals_total_annual"
R2_BASE = "https://media.avejourneys.com/intelligence"


def publish_annual(
    series_id: int, published_root: Path, raw_dir: Path, version: int = 1
) -> pd.DataFrame:
    html = mma_viya.fetch_page(series_id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"viya_series_{series_id}.html"
    raw_path.write_text(html)  # cache the exact bytes the series was derived from

    charts = mma_viya.parse_embedded_charts(html)
    if "A" not in charts:
        raise SystemExit("no annual chart found on the Viya page")
    series_df = mma_viya.validate_arrivals(charts["A"])

    lineage = stamp(html.encode())
    artifact = build_series(
        metric=METRIC,
        geo="MV",
        freq="A",
        unit="arrivals",
        df=series_df,
        lineage=lineage,
    )
    path = write_series(artifact, published_root, version=version)

    now = dt.datetime.now(dt.UTC).isoformat()
    rel = path.relative_to(published_root).as_posix()
    manifest = load_manifest(published_root)
    upsert_artifact(
        manifest,
        {
            "id": ARTIFACT_ID,
            "type": "series",
            "metric": METRIC,
            "geo": "MV",
            "version": version,
            "latest": True,
            "path": rel,
            "url": f"{R2_BASE}/{rel}",
            "hash": file_hash(path),
            "createdAt": now,
        },
    )
    write_manifest(manifest, published_root, generated_at=now, git_sha=lineage.gitSha)
    return series_df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", type=int, default=104)
    parser.add_argument("--published", type=Path, default=Path("published"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/mma"))
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args(argv)

    print(f"Publishing annual arrivals from MMA Viya series {args.series} → v{args.version}…")
    series = publish_annual(args.series, args.published, args.raw, args.version)
    print(
        f"\n✓ {len(series)} annual points "
        f"({series['ds'].min():%Y} → {series['ds'].max():%Y})"
        f"  min={series['y'].min():,.0f}  max={series['y'].max():,.0f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
