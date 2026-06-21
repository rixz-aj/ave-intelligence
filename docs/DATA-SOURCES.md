# Data sources — Maldives tourism

Source register for the platform. **Primary** = the series we model from;
secondary = cross-checks / covariates / context. Access caveats and the COVID
structural break are load-bearing — read the notes.

## Primary

### ★ MMA Statistics Database (Viya) — series 104, "Total tourist arrivals"
- **Publisher:** Maldives Monetary Authority (MMA); attributed to Ministry of Tourism.
- **URL:** https://database.mma.gov.mv/viya/series/104
- **What:** single national monthly total-arrivals time series.
- **Coverage:** monthly, **Jan 1988 → present** (~38 yrs / 450+ obs) — by far the
  longest continuous series found. Ideal for SARIMA/Prophet seasonality.
- **Format:** interactive Viya app + Tables/Download export + a JSON REST API
  (`https://database.mma.gov.mv/api/series?ids=104`).
- **⚠️ Caveat:** the API needs a **Bearer token** and the docs
  (`/api/docs`) don't explain how to get one or whether self-signup is free.
  **Fallback:** the on-page Tables view + Download/export work without a token —
  `ingest/mma_viya.py` must support this path.
- **Sibling series (use as exogenous regressors):** bednights total `205` / hotels
  `207`, average stay `210`, occupancy total `216` / resorts `219` / hotels `218` /
  guesthouses `217`.

### Ministry of Tourism — Monthly Statistics Report (arrivals BY MARKET)
- **URL:** https://www.tourism.gov.mv/en/statistics/publications
- **What:** arrivals by nationality (~90 countries) and by residence; arrivals to
  resorts/hotels/guesthouses; distribution by atoll; **Table 5 = key indicators**
  (bednights/occupancy/avg stay); establishments, bed capacity, utilization.
- **Coverage:** monthly archive **2009 → present**; current month + YTD + prior-year.
- **Format:** **PDF only** (clean, machine-extractable with `pdftotext -layout`).
  Per-market monthly data exists *nowhere else free* — building a market panel means
  extracting every monthly PDF. (Table 1 = by nationality, Table 2 = by residence.)
- Example file (Aug 2025): `https://www.tourism.gov.mv/dms/document/2ea6dbaad39e5c1aa72b5ef1cdacf3af.pdf`

## Secondary / covariates / context

| Source | Publisher | Use | Format / caveat |
|---|---|---|---|
| [Tourism Statistics Dashboard](https://www.tourism.gov.mv/en/statistics/dashboard) | MoT | quick validation, market-share / regional split | web only, no bulk export |
| [Statistical Yearbook, Ch.10](https://statisticsmaldives.gov.mv/yearbook/) | Bureau of Statistics | **Excel/XLS** tourism tables | annual, lags; best if you need spreadsheets |
| [Maldives in Figures](https://statisticsmaldives.gov.mv/monthly-statistics/) | Bureau of Statistics | monthly Excel snapshot | summary-level tourism only |
| [Tourism Yearbook](https://tourism.gov.mv/en/page/tourism_year_book) | MoT | backfill / validate history | annual PDF |
| [MMA Monthly Statistics / Economic Update](https://www.mma.gov.mv/#/publications) | MMA | narrative context, receipts | PDF (machine-readable equiv = Viya) |
| [World Bank ST.INT.ARVL](https://data.worldbank.org/indicator/ST.INT.ARVL?locations=MV) | World Bank / UNWTO | annual cross-check, macro covariates (GDP, receipts) | CSV/API; **annual, ends ~2020** — not a primary feed |
| [UN Tourism dashboard](https://www.unwto.org/tourism-data/unwto-tourism-dashboard) | UNWTO | international benchmarking | granular DB (e-unwto) is paywalled |
| [IMF DataMapper](https://www.imf.org/external/datamapper/profile/MDV) | IMF | macro covariates (GDP, CA, inflation) | annual |

## Aviation (leading indicators) — mostly gapped/paywalled

- **MACL / Velana International Airport** (https://macl.aero/) — passenger totals
  released as **press releases only**; **no monthly machine-readable series**.
- **OAG** (seat capacity) and **ForwardKeys** (forward bookings) — the best leading
  indicators of future demand, but **commercial / paywalled**.

## Gotchas (do not skip)

- **COVID structural break:** Mar 2020 near-zero, 2021–22 recovery. Any naive
  SARIMA/Prophet fit over 2018–2023 is distorted — handle with an intervention
  dummy or burn-in exclusion, and **document it in the artifact**.
- **Definitional mismatch:** MMA "tourist arrivals" ≠ MACL airport passenger
  movements (which include domestic + seaplane + transfers). **Never blend them** in
  one chart/KPI without reconciling. Record the definition in each series' meta.
- **No free per-market monthly API** — that data is PDF-only (MoT Table 1).
- Some Bureau yearbook `/tourism/` sub-paths 404; navigate from the yearbook landing page.

*Last reviewed: 2026-06 (grounding research). Re-verify URLs each phase.*
