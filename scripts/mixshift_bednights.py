"""Publish the accommodation-type bednights series that drive the mix-shift module.

The MMA Viya database carries tourist bednights split by facility type as separate
tokenless series — resorts (208), hotels (207), guest houses (206), safari vessels (209).
Together they are the cleanest free measure of the resort→guesthouse mix-shift (the
honest, measurable version of the local-island-accessibility hypothesis): the website
derives shares from these raw component series at render.

Frequencies are kept separate per the two-frequency rule; this publishes the ANNUAL
component series (the long structural arc; guest houses begin at their 2010 legalisation).

Usage:
    uv run python scripts/mixshift_bednights.py
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

R2_BASE = "https://media.avejourneys.com/intelligence"

# MMA Viya series id -> (metric, artifact id). Resorts run from 1988; guest houses & safari
# vessels only from their 2010 legalisation, which is exactly the structural break.
COMPONENTS: dict[int, tuple[str, str]] = {
    208: ("bednights_resorts", "bednights-resorts-mv"),
    207: ("bednights_hotels", "bednights-hotels-mv"),
    206: ("bednights_guesthouses", "bednights-guesthouses-mv"),
    209: ("bednights_safari", "bednights-safari-mv"),
}


def publish(published_root: Path, raw_dir: Path, version: int = 1) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.UTC).isoformat()
    manifest = load_manifest(published_root)
    summary: dict[str, pd.Series] = {}
    git_sha = "unknown"

    for series_id, (metric, artifact_id) in COMPONENTS.items():
        html = mma_viya.fetch_page(series_id)
        (raw_dir / f"viya_series_{series_id}.html").write_text(html)
        charts = mma_viya.parse_embedded_charts(html)
        if "A" not in charts:
            raise SystemExit(f"series {series_id} ({metric}): no annual chart")
        df = mma_viya.validate_arrivals(charts["A"])
        summary[metric] = df.set_index("ds")["y"]

        lineage = stamp(html.encode())
        git_sha = lineage.gitSha
        artifact = build_series(
            metric=metric, geo="MV", freq="A", unit="bednights", df=df, lineage=lineage
        )
        path = write_series(artifact, published_root, version=version)
        rel = path.relative_to(published_root).as_posix()
        upsert_artifact(
            manifest,
            {
                "id": artifact_id,
                "type": "series",
                "metric": metric,
                "geo": "MV",
                "version": version,
                "latest": True,
                "path": rel,
                "url": f"{R2_BASE}/{rel}",
                "hash": file_hash(path),
                "createdAt": now,
            },
        )
        print(f"  ✓ {metric:22s} {len(df):2d} pts {df['ds'].min():%Y}→{df['ds'].max():%Y}")

    write_manifest(manifest, published_root, generated_at=now, git_sha=git_sha)
    frame = pd.DataFrame(summary)
    return frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--published", type=Path, default=Path("published"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/mma"))
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args(argv)

    print("Publishing accommodation-type bednights from MMA Viya…")
    frame = publish(args.published, args.raw, args.version)
    overlap = frame.dropna()
    if not overlap.empty:
        total = overlap.sum(axis=1)
        gh = overlap["bednights_guesthouses"] / total * 100
        print(
            f"\nGuest-house share of bednights: {gh.iloc[0]:.1f}% ({overlap.index[0]:%Y}) "
            f"→ {gh.iloc[-1]:.1f}% ({overlap.index[-1]:%Y})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
