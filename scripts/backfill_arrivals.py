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
from ave_core.ingest import mma_viya, mot_pdf
from ave_core.lineage import stamp

ARTIFACT_ID = "arrivals-total-mv"
R2_BASE = "https://media.avejourneys.com/intelligence"


def _append_mma_tail(points: pd.DataFrame, sources: list[str]) -> pd.DataFrame:
    """Extend the PDF-derived series with the MMA Viya monthly window for any months the
    MoT PDFs don't cover (the latest report sometimes ships a transposed layout the column
    parser can't read). MMA and MoT agree to <0.02% where they overlap, so the tail is a
    safe, source-noted gap-fill that keeps the series current."""
    try:
        mma_monthly = mma_viya.fetch_series(104, freq="M")
    except Exception as exc:  # noqa: BLE001 - network resilience; PDF series still stands
        print(f"  MMA tail skipped ({exc})")
        return points
    cutoff = points["ds"].max()
    tail = mma_monthly[mma_monthly["ds"] > cutoff]
    if tail.empty:
        return points
    print(f"  + {len(tail)} month(s) from MMA Viya tail: "
          f"{', '.join(f'{d:%Y-%m}' for d in tail['ds'])}")
    sources.append("mma_viya:series_104:monthly")
    return pd.concat([points, tail], ignore_index=True)


def backfill(
    from_year: int,
    to_year: int,
    published_root: Path,
    raw_dir: Path,
    version: int = 1,
    mma_tail: bool = True,
) -> pd.DataFrame:
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
    points = pd.DataFrame(
        {"ds": pd.to_datetime(frame["period"]), "y": frame["arrivals"].astype(float)}
    )
    if mma_tail:
        points = _append_mma_tail(points, sources)
    # The MoT archive re-uploads some months in more than one PDF. Identical re-uploads are
    # harmless (drop them); genuinely conflicting values for the same month are a parser bug
    # and must fail loudly rather than be silently coin-flipped.
    conflicting = points.groupby("ds")["y"].nunique()
    conflicts = conflicting[conflicting > 1].index
    if len(conflicts):
        raise SystemExit(
            "conflicting duplicate months (same month, different values): "
            + ", ".join(f"{c:%Y-%m}" for c in conflicts)
        )
    series_df = validate_arrivals(points.drop_duplicates("ds"))

    lineage = stamp("|".join(sorted(sources)).encode())
    artifact = build_series(
        metric="arrivals_total",
        geo="MV",
        freq="M",
        unit="arrivals",
        df=series_df,
        lineage=lineage,
    )

    target = published_root / "series" / "arrivals_total" / "MV" / f"v{version}.json"
    if version == 1 and target.exists():
        target.unlink()  # v1 is the interim dev fixture; regenerate it. v2+ stay immutable.
    path = write_series(artifact, published_root, version=version)

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
    parser.add_argument("--from-year", type=int, default=2019)
    parser.add_argument("--to-year", type=int, default=dt.date.today().year)
    parser.add_argument("--published", type=Path, default=Path("published"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/mot"))
    parser.add_argument(
        "--version",
        type=int,
        default=1,
        help="series version to write (v1=dev fixture; bump for immutable publishes)",
    )
    parser.add_argument(
        "--no-mma-tail",
        dest="mma_tail",
        action="store_false",
        help="don't extend the series with the MMA Viya monthly tail (default: do)",
    )
    args = parser.parse_args(argv)

    print(f"Backfilling arrivals {args.from_year}–{args.to_year} → v{args.version}…")
    series = backfill(
        args.from_year, args.to_year, args.published, args.raw, args.version, args.mma_tail
    )
    print(
        f"\n✓ {len(series)} monthly points "
        f"({series['ds'].min():%Y-%m} → {series['ds'].max():%Y-%m})"
        f"  min={series['y'].min():,.0f}  max={series['y'].max():,.0f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
