# ROADMAP — Avé Intelligence

The build is split so each piece is a self-contained session. Build **in order**:
each phase depends on the one before. Every phase has a **Definition of Done (DoD)**
— don't move on until it's green.

> **How to start a session for a phase:** open this repo, read root `CLAUDE.md`,
> then read the `CLAUDE.md` of the module named in the phase. That's all the
> context you need. For the web slice, switch to `../nira-app` and read
> `docs/WEB-INTEGRATION.md` here first.

---

## Phase 0 — Scaffold + one end-to-end vertical slice  ⟵ START HERE

**Goal:** prove the entire pipeline end-to-end with ONE real series and ONE real
chart on the live site. This phase *defines the contract* everything else conforms to.

**Module:** `packages/core` (this repo) + the web slice in `../nira-app`.

**Deliverables**
- `ave_core` minimal but real:
  - `ingest/mma_viya.py` — pull MMA **series 104** (monthly total arrivals). Support
    the on-page Tables/Download export as a fallback (the JSON API needs a Bearer
    token with no documented self-signup — see `docs/DATA-SOURCES.md`).
  - one `contracts` pandera schema for the arrivals series,
  - `eval/baseline.py` seasonal-naive (already drafted),
  - `export/series.py` + `export/manifest.py` (already drafted) + `export/validate.py`,
  - `lineage.py` stamp (already drafted).
- DVC initialised with the R2 remote; `dvc.yaml` DAG stub (`ingest → export`).
- **Run it:** ingest 104 → `data/processed/arrivals.parquet` → ONE
  `published/series/arrivals_total/MV/v1.json` → update `published/manifest.json` →
  push series JSON to R2, write one hand-authored report MDX.
- Web slice in `nira-app` (see `docs/WEB-INTEGRATION.md`): `/intelligence`
  landing + `$slug`, nav entry, `intelligence-manifest.ts` (fetch R2 manifest),
  ONE `EditorialChart` (Observable Plot → server-rendered SVG) drawing the real
  series, chart tokens in `styles.css`, `sync-intelligence.ts`, sitemap + SEO.

**DoD:** `/intelligence` renders one real article with one real, server-rendered
chart sourced from a real MMA series, deployed to **staging**. `task validate` passes.

---

## Phase 1 — Project A: tourism_forecasting

**Module:** `projects/tourism_forecasting` (read its `CLAUDE.md`).

**Deliverables**
- Seasonal-naive baseline (MASE = 1.0 reference) + **SARIMA** + **Prophet** on
  series 104, with **COVID structural-break** handling (intervention dummy / burn-in).
- Exogenous covariates from MMA series 205 / 216 / 210 (bednights / occupancy /
  average stay) for SARIMAX / Prophet regressors / XGBoost features.
- **XGBoost** global model with lag + rolling + calendar + exog features; quantile
  (or conformal) bands.
- Rolling-origin backtest (MASE / sMAPE / pinball) **embedded** in each forecast artifact.
- Export forecast JSON (point + 80/95 bands + backtest block) to R2.
- One forecast report MDX ("Maldives Tourism Outlook 2026") showing model-vs-naive.
- Per-market panel via MoT PDF Table 1 extraction where feasible.

**DoD:** a published forecast artifact that beats the baseline, plus a live forecast
report at `/intelligence/forecasts/maldives-tourism-2026`.

---

## Phase 2 — Project B: resort_pricing

**Module:** `projects/resort_pricing`.

**Deliverables**
- Collect publicly available resort attributes (room rate, star rating, atoll,
  transfer type, distance from MLE, amenities, brand).
- Pricing distribution, luxury-premium, geographic, transfer-impact, brand-premium analyses.
- Regression explaining ADR drivers (which variables matter, atoll premia, brand effect).
- Publish a price-index series + a pricing report MDX with editorial charts.

**DoD:** `/intelligence/resort-pricing/market-overview` live, sourced from published artifacts.

---

## Phase 3 — Project C: recommendation_engine

**Module:** `projects/recommendation_engine`.

**Deliverables**
- Phase 1 rule-based → Phase 2 scoring → Phase 3 ML recommendation, over
  budget / dates / trip-type / count / style / interests.
- Outputs: recommended resorts / islands / experiences / itineraries.
- Consumes forecasting + pricing outputs as features (cross-project dependency —
  this is the moment the platform proves itself).

**DoD:** a recommendation service consumed by the `nira-app` Begin / concierge flow
(scoring tier at minimum).

---

## Phase 4 — Project D: reports + hardening

**Module:** `projects/reports`.

**Deliverables**
- `report_builder` consolidates A–C into editorial MDX + matching PDF (same source).
- Recurring report types: Tourism Outlook, China / India market updates, Luxury
  Trends, Aviation Capacity, Development Pipeline.
- Full manifest of all artifact types; CI gate validating `published/` against `meta/`.
- README architecture diagram refresh + one hand-rolled SVG hero graphic for the flagship.
- *Optional:* D1 gating migration in `nira-app` if a draft/publish workflow is needed.

**DoD:** `/intelligence/reports` index + several publishable, PDF-exportable reports live.

---

## Cross-cutting (every phase)

- **SEO:** each artifact becomes indexable content (titles like "Maldives Tourism
  Forecast 2027", "Maldives Resort Pricing Analysis"). Sitemap + `pageMeta()` +
  `canonical()` on every route (handled in `nira-app`).
- **Contract discipline:** versioned immutable artifacts; `task validate` green.
- **Trust:** methodology + `n=` + source lines; never founder faces.

## Known risks (carry forward)

MMA API token access (use on-page export fallback) · COVID break must be modeled ·
MMA arrivals ≠ MACL airport passengers (don't blend) · cross-repo manifest drift
(immutable versions + hash + validate-before-commit) · publish *write-then-flip*
(artifacts before manifest) · Observable-Plot SSR is new here (de-risk with one
chart in Phase 0) · `nira-app` deploys WIP — never ship a half-synced
`intelligence-content/`. Full list in the grounding notes; mitigations baked into the DoDs.
