# CLAUDE.md — ave_core

The shared library every project depends on. Keep it small, typed (`mypy --strict`),
and tested. Project-specific modeling does **not** belong here — only reusable infra.

## Modules

| Module | Responsibility |
|---|---|
| `io/` | parquet read/write; R2/S3 readers+writers (data lake + publish targets) |
| `ingest/` | source connectors → `data/raw`. `mma_viya.py` (series 104 + token fallback), `mot_pdf.py` (Table-1 extraction via `pdftotext -layout`), `worldbank.py`, `fx.py` |
| `contracts/` | **pandera** schemas validating every `raw→interim→processed` boundary. Schema drift fails loudly |
| `features/` | lag / rolling / calendar / exogenous feature builders |
| `eval/` | rolling-origin backtest, MASE / sMAPE / pinball, `baseline.seasonal_naive` |
| `export/` | write web-consumable artifacts to `published/` (series/forecast JSON, manifest, MDX/PDF), `validate.py` against `meta/*.schema.json` |
| `lineage.py` | `{runId, gitSha, inputHash}` stamp embedded in every artifact |

## Rules

- **Never hand-write a `published/` artifact.** Go through `ave_core.export`, which
  stamps lineage and conforms to `published/meta/*.schema.json`.
- **Immutable versions.** `export.series`/`export.forecast` write `vN`; bump, never mutate.
- **Contracts at boundaries.** A transform that loads a DataFrame validates it against
  a `contracts` schema first. Add a fixture test when you add a schema.
- **No network at import time.** Connectors do I/O inside functions, never module top-level.
- **Determinism.** Seed models; `seasonal_naive` defines MASE=1.0 — nothing ships unless
  it beats it.

## Status (scaffold)

Implemented as working drafts: `lineage.py`, `eval/baseline.py`, `export/series.py`,
`export/manifest.py`, `export/validate.py`, `contracts/arrivals.py`.
Stub to finish in **Phase 0**: `ingest/mma_viya.py` (real fetch + on-page export
fallback), `io/` (parquet + R2), `dvc.yaml` wiring. Add tests under
`packages/core/tests/` as you implement.
