# Avé Intelligence

**A data platform for Maldives tourism research, forecasting, and market analytics.**

Avé Intelligence is the research arm of [Avé](https://avejourneys.com) — a public,
editorial-grade intelligence layer built on top of publicly available tourism,
aviation, and hospitality data. It produces forecasts, pricing analytics, and
recurring market reports that surface on the website at `/intelligence`.

The design goal is a tourism-research publication in the tradition of the
**Financial Times**, **Bloomberg**, and **Skift Research** — editorial first,
analytics second — not a SaaS dashboard.

This repository is the **data-engineering monorepo**. It owns all ingestion,
data contracts, modeling, and artifact export. It does **not** contain the
website — the website ([`nira-app`](../nira-app)) is a pure *consumer* of the
artifacts this repo publishes. The two are joined by exactly one seam: the
[`published/`](./published) folder, governed by [`CONTRACT.md`](./CONTRACT.md).

---

## Architecture

```
   SOURCES                 ave-intelligence  (this repo, Python / uv / DVC)              avejourneys.com (nira-app)
 ┌───────────────┐        ┌──────────────────────────────────────────────────┐        ┌────────────────────────────┐
 │ MMA series104 │        │  ingest ─▶ contracts ─▶ features ─▶ models ─▶ eval│        │  /intelligence routes       │
 │ MoT monthly   │ ─────▶ │  (pandera)              (lag/cal)   (SARIMA/      │        │   ├─ landing                │
 │ PDFs (Tbl 1)  │        │                                      Prophet/XGB) │        │   ├─ /forecasts             │
 │ World Bank    │        │                            │                      │        │   ├─ /resort-pricing        │
 │ FX / macro    │        │                            ▼                      │        │   └─ /reports/[slug]        │
 └───────────────┘        │                    ┌──────────────┐               │        │                             │
                          │                    │  published/  │  ── R2 ─────▶ │  series/forecast JSON + PDFs │
   DVC remote (R2) ◀──────┤  data/ (lake)      │  manifest +  │               │        │  (media.avejourneys.com)    │
   raw/interim/processed  │                    │  meta + mdx  │  ── commit ─▶ │  src/data/intelligence-content/ │
                          └────────────────────┴──────┬───────┴───────────────┘        │  (MDX report bodies, SSR)   │
                                                       │                                └────────────────────────────┘
                                              THE CONTRACT (CONTRACT.md)
                          The website never imports, runs, or vendors Python.
```

**Why two repos.** A research session opens only `ave-intelligence` and never has
to load the large website context (token-scoped work). The pipeline reruns on its
own monthly cadence (new Ministry of Tourism release) without coupling to website
deploys. Two clean toolchains, two clean CIs, one explicit schema-governed seam.

## What's inside

| Path | What it is |
|------|------------|
| [`packages/core`](./packages/core) | `ave_core` — shared library: ingestion connectors, pandera data contracts, feature builders, backtest/eval, artifact export, lineage stamping. |
| [`projects/tourism_forecasting`](./projects/tourism_forecasting) | **Project A** — monthly arrival demand forecasting (seasonal-naive baseline, SARIMA, Prophet, XGBoost). *Phase 1.* |
| [`projects/resort_pricing`](./projects/resort_pricing) | **Project B** — what drives resort ADR (regression on star/atoll/transfer/brand). *Phase 2.* |
| [`projects/recommendation_engine`](./projects/recommendation_engine) | **Project C** — traveler recommendation/segmentation engine. *Phase 3.* |
| [`projects/reports`](./projects/reports) | **Project D** — narrative report builder (MDX + PDF) that synthesizes A–C. *Phase 4.* |
| [`published/`](./published) | **The handoff boundary.** Versioned artifacts + `manifest.json` + JSON Schemas the website consumes. |
| [`data/`](./data) | DVC-tracked data lake (`raw`/`interim`/`processed`/`external`). Not in git. |

## Data sources

Primary monthly arrivals series: **Maldives Monetary Authority (MMA) Statistics
Database, series 104** ("Total tourist arrivals") — official, monthly, Jan 1988→present
(~38 years), machine-readable. Arrivals *by source market* come from the **Ministry
of Tourism** monthly PDFs (Table 1, ~90 countries), extracted with `pdftotext -layout`.
Full source register, access caveats, and the COVID structural-break note live in
[`docs/DATA-SOURCES.md`](./docs/DATA-SOURCES.md) (written in Phase 0).

## Quickstart

```bash
# Requires uv (https://docs.astral.sh/uv) and optionally go-task.
task setup        # uv sync + pre-commit install   (or: uv sync --dev)
task lint test    # ruff + mypy + pytest
task ingest       # pull MMA series 104 -> data/raw   (Phase 0)
```

## Status

Scaffolded. See [`ROADMAP.md`](./ROADMAP.md) for the phased build plan and
**exactly where to start a new session**. Phase 0 (the end-to-end vertical slice)
is the first build target.

---

*Methodology and sourcing are documented on every artifact and report. Authority
here comes from rigor — sample sizes, source lines, backtests — not personas.*
