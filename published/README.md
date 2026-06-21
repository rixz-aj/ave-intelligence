# published/ — the handoff boundary

This folder is the **only** surface the website (`../nira-app`) reads. It is the
contract between the two repos. See [`../CONTRACT.md`](../CONTRACT.md) for the full spec.

```
published/
├── manifest.json     # index of every artifact (id, type, version, hash, url) — COMMITTED
├── meta/             # JSON Schema per artifact type (the public data contract) — COMMITTED
│   ├── manifest.schema.json
│   ├── series.schema.json
│   ├── forecast.schema.json
│   └── report.schema.json
├── series/           # {metric}/{geo}/v{n}.json   → pushed to R2 (gitignored locally)
├── forecasts/        # {model}/{horizon}/v{n}.json → pushed to R2 (gitignored locally)
└── reports/          # {slug}.mdx (COMMITTED into nira-app) + {slug}.pdf (R2)
```

**Rules**
- Artifacts are **immutable**: `v1`, `v2`, … are never overwritten. "Latest" is
  resolved through `manifest.json`.
- **Write-then-flip:** publish artifacts to R2 *before* updating the manifest.
- Every artifact must validate against `meta/*.schema.json` — `task validate` / the
  CI gate enforces this.
- Never hand-write artifacts; produce them via `ave_core.export`.

`series/` and `forecasts/` JSON are gitignored here (they live on R2); only
`manifest.json`, `meta/`, and report MDX are committed.
