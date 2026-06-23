# Handoff — Phase 1 (and the loose ends before it)

A self-contained brief to start a fresh session. Read this + the repo's `CLAUDE.md`,
`ROADMAP.md`, and `CONTRACT.md`. The website lives in `../nira-app` — only open it for
the web-facing items below.

---

## Where things stand (2026-06-21)

**Data platform (`ave-intelligence`, this repo) — DONE for Phase 0:**
- Public on GitHub: https://github.com/rixz-aj/ave-intelligence
- `uv` workspace, toolchain green (ruff · mypy --strict · pytest · `task validate`).
- `ave_core` real primitives: `ingest.mot_pdf` (parses MoT monthly PDFs by column —
  robust to COVID near-zero cells + both report layouts), contracts, eval (seasonal-naive
  baseline + MASE/sMAPE), export (series/manifest + schema validate), lineage.
- `scripts/backfill_arrivals.py` → **real 63-month arrivals series, 2021-01→2026-03**
  at `published/series/arrivals_total/MV/v1.json` (committed fixture; PDFs cached in
  `data/raw/mot/`).
- Primary source = public MoT PDFs (MMA Viya API is auth-gated — see `docs/DATA-SOURCES.md`).

**Website (`../nira-app`) — Phase 0 web slice MERGED, deployed to staging, but BUGGY:**
- `/intelligence` landing + nav (`Resorts·Islands·Charters·avé·Intelligence·Journal·About·Begin`)
  + hand-rolled SSR SVG arrivals chart. PR #1 merged to `main` (55eb49b).
- Deployed to **staging.avejourneys.com** (migrations 0006/0007 applied to nira-staging D1).
- ✅ Works perfectly in the Vite **dev** server (light/dark/mobile, real data).

---

## DO THESE FIRST (before Phase 1 proper)

### 1. Wire R2 publish (data side)
- R2 host is **`media.avejourneys.com`** (bucket `nira-media`), confirmed from the live worker binding `MEDIA_PUBLIC_URL`. The manifest URL is already correct.
- Add a publish step (`wrangler r2 object put`, or rclone) under a `task publish` that uploads `published/series/**` + `forecasts/**` + report PDFs to `intelligence/**` on the `nira-media` bucket. **Write-then-flip** (artifacts before manifest). Needs the Cloudflare private-relay account ([[nyra-cloudflare-account]]).
- Then nira-app can fetch from R2 instead of the committed fixture (`src/lib/intelligence-manifest.ts` per `docs/WEB-INTEGRATION.md`) — optional; the committed fixture already works.

### (Not a bug) The whole site is client-rendered
While deploying I found `/intelligence` renders an empty SSR `<body>` — but so do prod `/`,
`/journal`, `/concierge`, `/about`, `/charters`. The **entire live site** is client-rendered
(SSR shell + `<head>` only); only `/resorts` SSRs a full body. The `<head>` (title, meta,
canonical, og) DOES server-render for `/intelligence`, so the key SEO signals are fine and
Googlebot renders the JS body. `/intelligence` matches the site. **Making the site body-SSR
is a separate, site-wide TanStack-Start investigation** (why does only `/resorts` SSR? a
loader alone doesn't flip it — tested) — NOT part of adding `/intelligence`. Pick it up only
if you want full body-SSR site-wide for SEO.

---

## Phase 1 — Tourism Forecasting (the main event)

Module: `projects/tourism_forecasting/` (read its `CLAUDE.md`). Build order:
1. **Seasonal-naive baseline** (already in `ave_core.eval`) — the MASE=1.0 reference.
2. **SARIMA** (statsmodels) on the 63-month arrivals series, with explicit **COVID
   structural-break handling** (the series starts 2021 so the worst of COVID is excluded,
   but note it if you extend earlier).
3. **Prophet** — holidays/changepoints.
4. **XGBoost** — lag/rolling/calendar/exog features.
5. Rolling-origin backtest (MASE/sMAPE/pinball) **embedded in the forecast artifact**.
6. Export forecast JSON (point + 80/95 bands + backtest) via `ave_core.export`; one
   forecast report MDX. Surface at `/intelligence/forecasts/maldives-tourism-2026`.

**Heavy deps install in this phase:** `uv sync` will pull prophet/xgboost/statsmodels
(not yet installed — Phase 0 used a core-only venv). Expect a longer first sync.

**Data note:** for a longer training history, either (a) extend the MoT backfill below 2021
(harden `mot_pdf` for COVID-2020 near-zero months first — the column parser handles it, but
verify Apr–Jul 2020), or (b) pursue an MMA Viya API token for the 1988→ monthly series.

---

## 🟢 YOUR IDEAS — the structural-demand-model vision (decided 2026-06-23)

The owner's idea: go beyond univariate time-series to a **structural source-country demand
model** — source-country economics + propensity-to-consume/save + demographics + outbound
travel + competitor-destination substitution (Bali/Seychelles/Mauritius/Fiji/Caribbean) +
the resort-vs-island accessibility mix-shift → predict inbound by demographic.

A research+verify workflow (8 domains, adversarially checked) returned the verdict and it is
captured here as the Phase-1+ direction:

- **Feasible — but at ANNUAL frequency, as a separate analytical module, NOT the monthly
  forecaster.** Monthly macro doesn't exist free; disaggregating annual → monthly would
  fabricate the very variation the model claims to measure (violates the honesty contract).
- **Two genuine walls (be blunt with the owner):** (1) the nationality × accommodation-type
  cross-tab does **not** exist free anywhere — so "which nationalities drive the budget
  segment" is a narrative, not a measurement; (2) MPC and hotel ADR are estimated/assumed
  or paywalled, so a true AIDS price-elasticity system isn't buildable — only reduced-form.
- **Agreed scope = three honest pieces:** (a) monthly univariate forecaster [THIS PHASE];
  (b) compositional resort/guesthouse **mix-shift** module (the honest, measurable version
  of the island-accessibility hypothesis); (c) deferred **annual** structural/elasticity
  module (gravity / ARDL-ECM + competitor-substitution panel) for reports.
- **TIER-A free inputs to build next:** source-market CPI+FX (IMF IFS/DBnomics), holiday/
  Ramadan/CNY calendars (huge ROI — see the real March-2026 −21% Ramadan dip), competitor
  arrivals-by-nationality panel (Jamaica/SriLanka/Seychelles/Fiji/Thailand/Indonesia/DR),
  flight-route events to MLE. Full design brief in the session transcript / memory
  [[ave-intel-mma-data-path]].

## ✅ DONE this session (2026-06-23)

- **Long series:** `mma_viya` connector (tokenless annual 1988→2025, 38 pts) + monthly
  extended 2009→2026 (207 pts, MoT PDFs) published as immutable **v2**. Two real `mot_pdf`
  parser bugs fixed (prior-year-title vs release-month dateline; comma-in-title); 14/17
  complete years reconcile **exactly** to the MMA annual control totals.
- **Forecaster:** seasonal-naive + SARIMA + Prophet + XGBoost, COVID intervention dummies,
  rolling-origin backtest. **SARIMA wins: MASE 0.59 vs naive 0.83, sMAPE 5.6%** (Prophet &
  XGBoost did NOT beat naive on this 17-yr history — reported honestly). Forecast +
  `maldives-tourism-2026.mdx` published; takeaway = post-COVID boom plateauing near 2.2M.
- **Backlog:** Ramadan/holiday regressor (would fix the March-2026 swing); XGBoost needs
  detrending (can't extrapolate trend); push artifacts to R2 + nira-app sync.

---

## How to start the Phase 1 session

```
cd ~/code/ave-intelligence        # data/forecasting work stays here
# read: CLAUDE.md, ROADMAP.md (Phase 1), projects/tourism_forecasting/CLAUDE.md, docs/DATA-SOURCES.md
uv sync                            # installs prophet/xgboost/statsmodels (first run is slow)
task lint test                     # confirm green
```
For the web-facing items (SSR fix, Forecast Center pages) switch to `~/code/nira-app` and
read `ave-intelligence/docs/WEB-INTEGRATION.md`.

**Suggested kickoff prompt:**
> "Phase 1 of avé Intelligence — tourism forecasting. Read HANDOFF-PHASE1.md. First fix the
> /intelligence prod-SSR bug (item 1), then build the forecasting pipeline (seasonal-naive →
> SARIMA → Prophet → XGBoost, backtested) and publish the first forecast + report. Here are
> my additional ideas: [your ideas]."
