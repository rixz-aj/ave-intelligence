# CONTRACT.md — the seam between `ave-intelligence` and `nira-app`

This is the **single interface** between the data platform (this repo) and the
website (`../nira-app`). Get this right and the two repos stay decoupled forever.

> **Invariant:** the website reads ONLY `published/`. It never imports, runs, or
> vendors Python. The data platform never imports website code.

`published/` is fully described by:
- `published/manifest.json` — the index of every artifact (id, type, version, hash, url),
- `published/meta/*.schema.json` — the JSON Schema for each artifact type (the public contract).

---

## What goes where: R2 vs committed

| Artifact | Lives in | Why |
|---|---|---|
| `series/*.json`, `forecasts/*.json` | **R2** (`media.avejourneys.com/intelligence/**`) | Large, regenerated monthly, immutable-versioned → cache forever. |
| report **PDFs** | **R2** | Binary, large. |
| `manifest.json`, `meta/*.json` | **committed** into `nira-app` (`src/data/intelligence-content/`) | Small, must be diffable + version-pinned so a deploy is reproducible. |
| report **MDX bodies** (`reports/*.mdx`) | **committed** into `nira-app` | Prose, SSR-rendered via `marked`, human-reviewable in PR. |

## How files move (hybrid, decoupled)

1. **Publish (this repo):** `task export` writes `published/`; `task publish` pushes
   series/forecast JSON + PDFs to R2 and commits `manifest.json` + `meta/` +
   `reports/*.mdx` here. **Write-then-flip:** upload artifacts to R2 *before*
   updating the manifest, so the manifest never points at a half-published object.
2. **Sync (nira-app):** `npm run sync:intelligence` (`scripts/sync-intelligence.ts`)
   pulls `manifest.json` + `reports/*.mdx` from this repo (GitHub raw or R2),
   **validates each against `meta/*.json` before writing** (a broken sync must never
   land — `nira-app` deploys WIP), and writes into `src/data/intelligence-content/`.
3. **Deploy (nira-app):** normal staging/prod deploy. Data artifacts resolve at
   runtime from R2 via `lib/intelligence-manifest.ts` (manifest `latest` → concrete
   `vN`, then pin + cache). The committed manifest snapshot is the source of truth
   for what the deploy renders.

**Net:** a monthly model rerun = an R2 push + one small `nira-app` content PR. Zero
Python ever ships to the site.

## Versioning rule

Artifacts are **immutable**: `v1`, `v2`, … are never mutated. "Latest" is resolved
through the manifest, not by overwriting a file. Every artifact carries a `hash`;
the manifest carries the `gitSha` of the run that produced it.

---

## Artifact shapes

Canonical schemas live in [`published/meta/`](./published/meta). Sketches below.

### `manifest.json`
```jsonc
{
  "schemaVersion": "1.0.0",
  "generatedAt": "2026-06-21T00:00:00Z",
  "gitSha": "abc1234",
  "artifacts": [
    { "id": "arrivals-total-mv", "type": "series", "metric": "arrivals_total", "geo": "MV",
      "version": 1, "latest": true, "path": "series/arrivals_total/MV/v1.json",
      "url": "https://media.avejourneys.com/intelligence/series/arrivals_total/MV/v1.json",
      "hash": "sha256:…", "createdAt": "2026-06-21T…" },
    { "id": "arrivals-forecast-sarima-12m", "type": "forecast", "model": "sarima", "horizon": "12m",
      "version": 1, "latest": true, "path": "forecasts/sarima/12m/v1.json",
      "url": "https://media.avejourneys.com/intelligence/forecasts/sarima/12m/v1.json", "hash": "sha256:…" },
    { "id": "maldives-tourism-2026", "type": "report", "slug": "maldives-tourism-2026",
      "version": 1, "latest": true, "path": "reports/maldives-tourism-2026.mdx",
      "pdfUrl": "https://media.avejourneys.com/intelligence/reports/maldives-tourism-2026-v1.pdf", "hash": "sha256:…" }
  ]
}
```

### series JSON
```jsonc
{ "schemaVersion": "1.0.0", "metric": "arrivals_total", "geo": "MV", "freq": "M", "unit": "arrivals",
  "points": [ { "ds": "2026-04-01", "y": 171000 } ],
  "lineage": { "runId": "…", "gitSha": "…", "inputHash": "sha256:…" } }
```

### forecast JSON
```jsonc
{ "schemaVersion": "1.0.0", "model": "sarima", "metric": "arrivals_total", "geo": "MV", "horizon": "12m",
  "points": [ { "ds": "2026-07-01", "yhat": 182000,
     "bands": [ { "level": 80, "lower": 174000, "upper": 190000 },
                { "level": 95, "lower": 168000, "upper": 196000 } ] } ],
  "backtest": { "baseline": "seasonal_naive", "mase": 0.71, "smape": 6.4, "pinball": 0.0, "folds": 12 },
  "lineage": { "runId": "…", "gitSha": "…", "inputHash": "…" } }
```

### report MDX frontmatter
```yaml
---
schemaVersion: "1.0.0"
slug: maldives-tourism-2026
title: "Arrivals are set to clear 2 million in 2026"   # active-voice takeaway, NOT the metric name
kicker: "ARRIVALS & DEMAND"
deck: "What 38 years of monthly data say about the year ahead."
publishedAt: "2026-06-21"
version: 1
artifacts: ["arrivals-total-mv", "arrivals-forecast-sarima-12m"]  # ids → manifest → R2 urls at render
sources: ["Avé Intelligence", "Ministry of Tourism (Maldives)", "MMA series 104"]
sampleSize: "n=450 monthly observations, Jan 1988–present"
pdfUrl: "https://media.avejourneys.com/intelligence/reports/maldives-tourism-2026-v1.pdf"
---
```
The MDX body is Markdown (`marked` → `.ave-prose`). Chart placeholders reference
artifact `ids`; the website's `EditorialChart` resolves `id → manifest → R2 JSON →
server-rendered Plot SVG`. Frontmatter maps to `INTELLIGENCE_ARTICLES` for the
sitemap + SEO (`pageMeta()` / `canonical()`).

---

See [`docs/WEB-INTEGRATION.md`](./docs/WEB-INTEGRATION.md) for the exact `nira-app`
files to create/edit when building the consumer side.
