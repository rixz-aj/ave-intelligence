"""Ingest MMA Statistics Database (Viya) series into `data/raw`.

Primary target: series **104 = Total tourist arrivals** (monthly, Jan 1988–present).
Covariates: 205 bednights, 216 occupancy, 210 average stay. See docs/DATA-SOURCES.md.

⚠️ The JSON API (https://database.mma.gov.mv/api/series?ids=104) requires a Bearer
token with no documented self-signup. This connector MUST therefore support the
on-page Tables/Download export as a fallback path. Finish in **Phase 0**.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Series id -> tidy metric name used downstream (and in published artifact paths).
SERIES: dict[int, str] = {
    104: "arrivals_total",
    205: "bednights_total",
    216: "occupancy_total",
    210: "avg_stay",
}


def fetch_series(series_id: int, token: str | None = None) -> pd.DataFrame:
    """Return a tidy DataFrame[ds, y] for one MMA series.

    Phase 0: if a Bearer `token` is available, call the JSON API; otherwise parse
    the on-page Tables/Download export. Validate the result against
    `ave_core.contracts.arrivals` before returning.
    """
    raise NotImplementedError(
        "Phase 0: implement MMA fetch (API with token, else on-page export fallback). "
        "See docs/DATA-SOURCES.md and packages/core/CLAUDE.md."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest MMA Viya series into data/raw")
    parser.add_argument("--series", type=int, default=104, help="MMA series id (default 104)")
    parser.add_argument("--out", type=Path, default=Path("data/raw"), help="output dir")
    parser.add_argument("--token", default=None, help="MMA API Bearer token (optional)")
    args = parser.parse_args(argv)

    df = fetch_series(args.series, args.token)
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / f"mma_{SERIES.get(args.series, args.series)}.parquet"
    df.to_parquet(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
