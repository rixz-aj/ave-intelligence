# CLAUDE.md — Avé Intelligence (root)

> Keep this file SHORT. It is loaded into every session. Detail lives in the
> per-module CLAUDE.md files — load only the one you're working in.

## What this repo is

The **data-engineering monorepo** for Avé Intelligence — Maldives tourism
forecasting, pricing analytics, and market reports. Python, `uv` workspace, DVC.

**The website is NOT here.** It lives in `../nira-app` (TanStack Start +
Cloudflare). Do **not** open or load `nira-app` from a research/modeling session —
that's the whole point of the split (token-scoped work). The only thing the two
repos share is the artifact contract in [`CONTRACT.md`](./CONTRACT.md).

## Workspace map (where to work)

| You're working on… | Open only… |
|---|---|
| Shared ingestion / contracts / export / eval | `packages/core/` (+ its `CLAUDE.md`) |
| Demand forecasting (Phase 1) | `projects/tourism_forecasting/` (+ its `CLAUDE.md`) |
| Resort pricing (Phase 2) | `projects/resort_pricing/` |
| Recommendation engine (Phase 3) | `projects/recommendation_engine/` |
| Report builder (Phase 4) | `projects/reports/` |
| The web surface (`/intelligence`) | switch to `../nira-app`; spec in [`docs/WEB-INTEGRATION.md`](./docs/WEB-INTEGRATION.md) |

Every project depends on `ave_core`. Read the project's own `CLAUDE.md` first; it
tells you the models, inputs, and definition-of-done for that slice.

## The one rule that governs everything

`published/` is the **only** surface the website reads. It is fully described by
`published/manifest.json` + `published/meta/*.schema.json`. If you change an
artifact's shape, you change a JSON Schema and bump its version — never mutate a
published version in place (`v1`, `v2`, … are immutable). See `CONTRACT.md`.

## Conventions

- **Tooling:** `uv` (workspace), `ruff` (lint+format), `mypy --strict` on `ave_core`,
  `pytest` + `hypothesis`, DVC for the data lake, `go-task` (`Taskfile.yml`) as the
  command vocabulary. Prefer `task <name>` over raw commands.
- **Data contracts:** every `raw → interim → processed` boundary is validated by a
  `pandera` schema in `ave_core.contracts`. Schema drift must fail loudly.
- **Lineage:** every published artifact carries `{runId, gitSha, inputHash}` via
  `ave_core.lineage`. Don't hand-write artifacts; go through `ave_core.export`.
- **Modeling honesty:** no model ships unless it beats the seasonal-naive baseline
  (MASE < 1.0). Backtest metrics are embedded in every forecast artifact.
- **COVID break:** the 2020 collapse / 2021–22 recovery is a structural break —
  always handled explicitly (intervention dummy or burn-in exclusion), never
  silently fitted over.
- **Notebooks:** EDA only, `nbstripout`'d, excluded from the reproducible pipeline.

## Trust layer (brand rule)

Authority comes from **methodology notes + sample sizes (`n=`) + source lines** —
**never** founder faces, bios, or stock "team" photos. This holds on the website too.

## Build order

See [`ROADMAP.md`](./ROADMAP.md). Start at **Phase 0** (the end-to-end vertical
slice that proves the contract). Don't build a project before Phase 0 exists.
