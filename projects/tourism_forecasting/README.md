# Project A — Tourism Forecasting

Monthly Maldives tourist-arrival demand forecasting (seasonal-naive baseline →
SARIMA → Prophet → XGBoost), with backtested accuracy and prediction bands.

Surfaces on the website at **Intelligence → Forecast Center**
(`/intelligence/forecasts`, `/intelligence/forecasts/maldives-tourism-2026`).

- **Status:** Phase 1 (scaffold). See [`CLAUDE.md`](./CLAUDE.md) for the build brief
  and [`../../ROADMAP.md`](../../ROADMAP.md) for sequencing.
- **Primary data:** MMA series 104 (1988→present). See [`../../docs/DATA-SOURCES.md`](../../docs/DATA-SOURCES.md).
- **Run (once implemented):** `uv run python -m tourism_forecasting.pipeline`.

Outputs are forecast JSON + a report MDX written into [`../../published`](../../published)
per [`../../CONTRACT.md`](../../CONTRACT.md). No model code ever ships to the website.
