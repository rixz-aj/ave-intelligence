"""Run the tourism-forecasting pipeline and publish the winning forecast artifact.

Backtests every model (seasonal-naive baseline + SARIMA/Prophet/XGBoost), picks the best
MASE, refits on all data, forecasts 12 months with 80/95 bands, and writes the forecast JSON
+ manifest entry into published/. The forecast carries its own backtest block (the honesty
record). Hand-author the report MDX separately; this only publishes the data artifact.

Usage:
    uv run python scripts/forecast_arrivals.py            # writes v1
    uv run python scripts/forecast_arrivals.py --version 2
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from tourism_forecasting.pipeline import run

from ave_core.export import (
    build_forecast,
    file_hash,
    load_manifest,
    upsert_artifact,
    write_forecast,
    write_manifest,
)
from ave_core.lineage import stamp
from tourism_forecasting import config

ARTIFACT_ID = "arrivals-forecast-12m"
R2_BASE = "https://media.avejourneys.com/intelligence"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--published", type=Path, default=Path("published"))
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args(argv)

    print("Backtesting models and forecasting (this refits every model — takes a few minutes)…")
    out = run(args.published)
    print(f"  winner: {out.winner}  backtest: {out.backtest_block}")

    series_path = (
        args.published / "series" / config.METRIC / config.GEO / f"v{config.SERIES_VERSION}.json"
    )
    lineage = stamp(series_path.read_bytes())
    artifact = build_forecast(
        model=out.winner,
        metric=config.METRIC,
        geo=config.GEO,
        horizon=config.HORIZON_LABEL,
        fc=out.forecast,
        levels=config.BAND_LEVELS,
        backtest=out.backtest_block,
        lineage=lineage,
    )
    path = write_forecast(artifact, args.published, version=args.version)

    now = dt.datetime.now(dt.UTC).isoformat()
    rel = path.relative_to(args.published).as_posix()
    manifest = load_manifest(args.published)
    upsert_artifact(
        manifest,
        {
            "id": ARTIFACT_ID,
            "type": "forecast",
            "model": out.winner,
            "metric": config.METRIC,
            "geo": config.GEO,
            "horizon": config.HORIZON_LABEL,
            "version": args.version,
            "latest": True,
            "path": rel,
            "url": f"{R2_BASE}/{rel}",
            "hash": file_hash(path),
            "createdAt": now,
        },
    )
    write_manifest(manifest, args.published, generated_at=now, git_sha=lineage.gitSha)

    first, last = out.forecast.iloc[0], out.forecast.iloc[-1]
    print(
        f"\n✓ wrote {rel}\n"
        f"  {out.forecast.index[0]:%Y-%m} yhat={first['yhat']:,.0f} "
        f"[80% {first['lower_80']:,.0f}–{first['upper_80']:,.0f}]\n"
        f"  {out.forecast.index[-1]:%Y-%m} yhat={last['yhat']:,.0f} "
        f"[80% {last['lower_80']:,.0f}–{last['upper_80']:,.0f}]\n"
        f"  next-12m total ≈ {out.forecast['yhat'].sum():,.0f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
