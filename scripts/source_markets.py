"""Publish the top source-market arrivals series — the source-market panel.

The MMA Viya database carries tourist arrivals by country as separate tokenless series
(China 153, India 169, Russia 116, UK 127, Germany 142, Italy 132, …). These are the
foundation of the source-market layer of the demand model and tell the post-COVID /
geopolitical reshuffle story directly. Annual frequency = the structural arc.

Usage:
    uv run python scripts/source_markets.py
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

# MMA Viya series id -> (metric slug, artifact id, display). The dramatic movers
# (China/India/Russia) plus the steady European base.
MARKETS: dict[int, tuple[str, str, str]] = {
    153: ("arrivals_china", "arrivals-china-mv", "China"),
    169: ("arrivals_india", "arrivals-india-mv", "India"),
    116: ("arrivals_russia", "arrivals-russia-mv", "Russia"),
    127: ("arrivals_uk", "arrivals-uk-mv", "United Kingdom"),
    142: ("arrivals_germany", "arrivals-germany-mv", "Germany"),
    132: ("arrivals_italy", "arrivals-italy-mv", "Italy"),
}


def publish(published_root: Path, raw_dir: Path, version: int = 1) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.UTC).isoformat()
    manifest = load_manifest(published_root)
    summary: dict[str, pd.Series] = {}
    git_sha = "unknown"

    for series_id, (metric, artifact_id, display) in MARKETS.items():
        html = mma_viya.fetch_page(series_id)
        (raw_dir / f"viya_series_{series_id}.html").write_text(html)
        charts = mma_viya.parse_embedded_charts(html)
        if "A" not in charts:
            raise SystemExit(f"series {series_id} ({metric}): no annual chart")
        df = mma_viya.validate_arrivals(charts["A"])
        summary[display] = df.set_index("ds")["y"]

        lineage = stamp(html.encode())
        git_sha = lineage.gitSha
        artifact = build_series(
            metric=metric, geo="MV", freq="A", unit="arrivals", df=df, lineage=lineage
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
        print(f"  ✓ {display:15s} {len(df):2d} pts {df['ds'].min():%Y}→{df['ds'].max():%Y}")

    write_manifest(manifest, published_root, generated_at=now, git_sha=git_sha)
    return pd.DataFrame(summary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--published", type=Path, default=Path("published"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/mma"))
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args(argv)

    print("Publishing top source-market arrivals from MMA Viya…")
    frame = publish(args.published, args.raw, args.version)
    last = frame.dropna(how="all").iloc[-1].sort_values(ascending=False)
    year = frame.dropna(how="all").index[-1]
    print(f"\n{year:%Y} leaderboard: " + ", ".join(f"{m} {v / 1000:.0f}k" for m, v in last.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
