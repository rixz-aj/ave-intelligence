"""Estimate per-market tourism-demand elasticities by ARDL bounds testing.

The structural layer of the demand model. For each top source market, fits an ARDL(1,1,1)
error-correction model of log-arrivals on log real-GDP-per-capita (income) and a Song-Witt
log relative-price term (destination CPI x exchange rate / source CPI), on the clean
pre-COVID window. Reports the Pesaran bounds-test F (cointegration), the long-run income and
price elasticities, and the error-correction speed.

Honesty notes baked in: income is identifiable (strongly positive, luxury good — magnitudes
run high, inflated by the emerging-market travel-access effect and short samples); the price
channel is NOT robustly identified on free annual data (the relative-price proxy is crude).
This script reproduces the numbers quoted in reports/maldives-demand-elasticities.mdx.

Usage:
    uv run python scripts/demand_elasticities.py
"""

from __future__ import annotations

import warnings
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from statsmodels.tsa.ardl import UECM

from ave_core.ingest import mma_viya, worldbank

# MMA Viya arrivals series id -> (display name, ISO-3 for World Bank).
MARKETS: dict[int, tuple[str, str]] = {
    153: ("China", "CHN"),
    169: ("India", "IND"),
    116: ("Russia", "RUS"),
    127: ("UK", "GBR"),
    142: ("Germany", "DEU"),
    132: ("Italy", "ITA"),
}
CLEAN_END = 2019  # pre-COVID contiguous window; shocks (COVID, closures, boycott) excluded
# Pesaran (2001) bounds-test upper critical values, k=2, case III (unrestricted constant).
F_10, F_5 = 3.75, 4.32


def _arrivals(series_id: int) -> pd.Series:
    annual = mma_viya.parse_embedded_charts(mma_viya.fetch_page(series_id))["A"]
    return annual.assign(year=annual["ds"].dt.year).set_index("year")["y"]


def estimate() -> pd.DataFrame:
    cpi_mv = worldbank.fetch_indicator("MDV", worldbank.CPI).set_index(
        worldbank.fetch_indicator("MDV", worldbank.CPI)["ds"].dt.year
    )["y"]

    def one(item: tuple[int, tuple[str, str]]) -> dict[str, object]:
        series_id, (name, iso) = item
        arrivals = _arrivals(series_id)
        gdp = worldbank.fetch_indicator(iso, worldbank.GDP_PER_CAPITA)
        fx = worldbank.fetch_indicator(iso, worldbank.EXCHANGE_RATE)
        cpi = worldbank.fetch_indicator(iso, worldbank.CPI)
        by_year = {
            "gdp": gdp.set_index(gdp["ds"].dt.year)["y"],
            "fx": fx.set_index(fx["ds"].dt.year)["y"],
            "cpi": cpi.set_index(cpi["ds"].dt.year)["y"],
        }
        # Song-Witt relative price: CPI_MV * FX / CPI_source (higher => Maldives pricier).
        rel_price = cpi_mv * by_year["fx"] / by_year["cpi"]
        frame = pd.DataFrame(
            {"la": np.log(arrivals), "lg": np.log(by_year["gdp"]), "lp": np.log(rel_price)}
        ).dropna()
        frame = frame[frame.index <= CLEAN_END].sort_index()
        if len(frame) < 12:
            return {"market": name, "n": len(frame), "note": "too few observations"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = UECM(frame["la"], 1, exog=frame[["lg", "lp"]], order=1, trend="c").fit()
            f_stat = float(res.bounds_test(case=3).stat)
        phi = float(res.params["la.L1"])  # error-correction speed (negative)
        return {
            "market": name,
            "f_stat": round(f_stat, 2),
            "cointegrated": "5%" if f_stat > F_5 else ("10%" if f_stat > F_10 else "no"),
            "income_elasticity": round(-float(res.params["lg.L1"]) / phi, 2),
            "price_elasticity": round(-float(res.params["lp.L1"]) / phi, 2),
            "ecm_speed": round(phi, 2),
            "n": len(frame),
            "window": f"{frame.index.min()}-{frame.index.max()}",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(one, MARKETS.items()))
    return pd.DataFrame(rows).set_index("market")


def main() -> int:
    table = estimate()
    pd.set_option("display.width", 120)
    print(table.to_string())
    coint = table[table["cointegrated"] != "no"]
    print(
        f"\nCointegrated: {list(coint.index)}. "
        f"Income elasticities {coint['income_elasticity'].min():+.1f}–"
        f"{coint['income_elasticity'].max():+.1f} (lit ~+1.5–2; high = access effect). "
        "Price channel only UK/Russia correctly signed — not robustly identified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
