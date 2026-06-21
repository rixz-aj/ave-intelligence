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

## ⚠️ DO THESE FIRST (before Phase 1 proper)

### 1. Fix the `/intelligence` prod-build SSR bug  ← highest priority
The page renders an **empty body** in the production build (head/title/meta render; the
component body has zero DOM). Other routes SSR full bodies, so it's specific to this route.
- **Reproduce locally:** `cd ~/code/nira-app && npm run build && npx wrangler dev --env staging --port 8801 --local`, then `curl http://localhost:8801/intelligence` → body has no `<div>/<svg>`. No error in `wrangler tail` ("Ok" 200).
- **Facts:** component + data ARE in `dist/server/assets/intelligence-*.js`. Works in dev. So it's a prod-bundle SSR throw that's swallowed after the head flushes.
- **Debug path:** surface the real error — wrap/inspect `renderToReadableStream` `onError`, or temporarily add a try/catch logging in the component. Prime suspects: (a) a component import in the route's chunk resolving to `undefined` in the prod bundle → try importing brand primitives **directly** (`../../components/ave/layout`, `/labels`, etc.) instead of the `../../components/ave` barrel; (b) JSON-import interop (`import x from './*.json'`) — make it robust and **guard the `ARRIVALS_POINTS.reduce(...)` calls with an initial value** so module-load can't throw on an unexpected shape.
- Verify the fix with the local `wrangler dev` repro, then redeploy staging.

### 2. Wire R2 publish (data side)
- The real R2 host is **`media.nyratest.uk`** (bucket `nira-media`), per `nira-app` CLAUDE.md — NOT `media.avejourneys.com`. Update `scripts/backfill_arrivals.py` `R2_BASE` and the manifest URL accordingly (or confirm the migration to media.avejourneys.com first).
- Add a publish step (wrangler r2 object put, or rclone) under a `task publish` that uploads `published/series/**` + `forecasts/**` + report PDFs to `intelligence/**` on R2. **Write-then-flip** (artifacts before manifest).
- Then nira-app can fetch from R2 instead of the committed fixture (`src/lib/intelligence-manifest.ts` per `docs/WEB-INTEGRATION.md`) — optional once SSR is fixed.

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

## 🟢 YOUR IDEAS (fill this in before/at the start of the session)

> Drop your Phase 1 ideas here so the next session builds them in. Examples of the kind of
> thing that fits: extra metrics to forecast (by-market arrivals, occupancy, bednights),
> scenario/what-if controls, a specific report angle, a different model, UI for the Forecast
> Center, alerts, etc.

- …
- …
- …

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
