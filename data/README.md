# data/ — the data lake (DVC-tracked, not in git)

Standard cookiecutter-data-science layers. Contents are tracked by **DVC** with an
R2/S3 remote; only `.dvc` pointers (and this README) are committed to git — never the
data blobs. See the DVC pipeline in `../dvc.yaml` (wired in Phase 0).

| Layer | What lives here |
|---|---|
| `raw/` | Immutable source dumps exactly as fetched (MMA series exports, MoT PDFs, FX). Never edited. |
| `interim/` | Cleaned & typed, pre-feature-engineering. |
| `processed/` | Model-ready parquet — the canonical training tables. |
| `external/` | Third-party reference data (holidays, geo, atoll lookup). |

**Lineage:** the pipeline records input hashes (`dvc.lock`) and every published
artifact carries `{runId, gitSha, inputHash}`, so any output traces back to exact
inputs + code revision. See `../docs/DATA-SOURCES.md` for what feeds `raw/`.
