"""Backfill the monthly total-arrivals series from public Ministry of Tourism PDFs.

For each year, discover the monthly report PDFs, download them (cached under
data/raw/mot), extract the TOTAL TOURIST ARRIVALS figure, and write a single
`series` artifact + manifest entry into published/ — the Phase-0 vertical-slice data.

The month each point covers is read from the PDF header, so listing order is never
trusted, and non-arrivals documents that don't parse are skipped.

Usage:
    uv run python scripts/backfill_arrivals.py --from-year 2019 --to-year 2026
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd

from ave_core.contracts import validate_arrivals
from ave_core.export import (
    build_series,
    file_hash,
    load_manifest,
    upsert_artifact,
    write_manifest,
    write_series,
)
from ave_core.ingest import mot_pdf
from ave_core.lineage import stamp

ARTIFACT_ID = "arrivals-total-mv"
R2_BASE = "https://media.avejourneys.com/intelligence"


def backfill(from_year: int, to_year: int, published_root: Path, raw_dir: Path) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    sources: list[str] = []

    for year in range(from_year, to_year + 1):
        try:
            html = mot_pdf.fetch_text(mot_pdf.year_listing_url(year))
        except Exception as exc:  # noqa: BLE001 - network resilience, keep going
            print(f"  {year}: listing fetch failed ({exc})")
            continue
        urls = mot_pdf.discover_report_urls(html)
        print(f"  {year}: {len(urls)} documents")
        for url in urls:
            name = url.rsplit("/", 1)[-1]
            try:
                pdf = mot_pdf.download_pdf(url, raw_dir / name)
                record = mot_pdf.parse_report(mot_pdf.extract_text(pdf))
            except Exception as exc:  # noqa: BLE001 - skip non-arrivals / bad PDFs
                print(f"    skip {name} ({exc})")
                continue
            records.append(record)
            sources.append(name)

    if not records:
        raise SystemExit("no reports parsed — nothing to write")

    frame = pd.DataFrame(records)
    series_df = validate_arrivals(
        pd.DataFrame({"ds": pd.to_datetime(frame["period"]), "y": frame["arrivals"].astype(float)})
    )

    lineage = stamp("|".join(sorted(sources)).encode())
    artifact = build_series(
        metric="arrivals_total",
        geo="MV",
        freq="M",
        unit="arrivals",
        df=series_df,
        lineage=lineage,
    )

    target = published_root / "series" / "arrivals_total" / "MV" / "v1.json"
    if target.exists():
        target.unlink()  # dev backfill regenerates v1; production versions are immutable
    path = write_series(artifact, published_root, version=1)

    now = dt.datetime.now(dt.UTC).isoformat()
    rel = path.relative_to(published_root).as_posix()
    manifest = load_manifest(published_root)
    upsert_artifact(
        manifest,
        {
            "id": ARTIFACT_ID,
            "type": "series",
            "metric": "arrivals_total",
            "geo": "MV",
            "version": 1,
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
    parser.add_argument("--from-year", type=int, default=2019)
    parser.add_argument("--to-year", type=int, default=dt.date.today().year)
    parser.add_argument("--published", type=Path, default=Path("published"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/mot"))
    args = parser.parse_args(argv)

    print(f"Backfilling arrivals {args.from_year}–{args.to_year}…")
    series = backfill(args.from_year, args.to_year, args.published, args.raw)
    print(
        f"\n✓ {len(series)} monthly points "
        f"({series['ds'].min():%Y-%m} → {series['ds'].max():%Y-%m})"
        f"  min={series['y'].min():,.0f}  max={series['y'].max():,.0f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
