# CLAUDE.md — Project A: tourism_forecasting

**Phase 1.** Forecast Maldives monthly tourist arrivals and publish forecast
artifacts + a flagship report. Read root `CLAUDE.md` and `../../CONTRACT.md` first.

## Objective

Produce honest, backtested monthly arrival forecasts (12-month horizon) with
prediction bands, plus source-market views where the data allows.

## Inputs

- **Target:** MMA series **104** (total arrivals, monthly, 1988→present) via
  `ave_core.ingest.mma_viya`.
- **Exogenous covariates:** MMA series 205 (bednights), 216 (occupancy), 210 (avg
  stay) for SARIMAX / Prophet regressors / XGBoost features.
- **By-market panel:** Ministry of Tourism monthly PDFs, Table 1 (`mot_pdf` connector,
  `pdftotext -layout`). Best-effort — see the data gaps in `docs/DATA-SOURCES.md`.

## Models (build in this order)

1. **Seasonal-naive baseline** (`ave_core.eval.seasonal_naive`) — defines MASE = 1.0.
2. **SARIMA** (statsmodels) — clean single series, analytic intervals, interpretable.
3. **Prophet** — holidays, changepoints, robust to messy/missing data.
4. **XGBoost** — global model with lag/rolling/calendar/exog features; quantile or
   conformal bands.

Nothing ships unless it beats the baseline (MASE < 1.0).

## The COVID rule (do not skip)

The 2020 collapse + 2021–22 recovery is a structural break. Handle explicitly —
intervention dummy (SARIMAX exog / Prophet holiday-style regressor) or burn-in
exclusion — and **document the choice in the forecast artifact and report**. Never
silently fit across it.

## Outputs (conform to the contract)

- Forecast JSON via `ave_core.export` → `published/forecasts/{model}/{horizon}/v{n}.json`
  with point + 80/95 bands + an embedded `backtest` block (MASE/sMAPE/pinball, folds).
- One report MDX → `published/reports/maldives-tourism-2026.mdx` (active-voice
  takeaway title; model-vs-naive chart; methodology + `n=`).

## Evaluation

Rolling-origin backtest (expanding window, refit each fold). Report MASE primarily
(scale-free, comparable), sMAPE secondarily, pinball loss for the bands.

## Definition of Done

A published forecast artifact that beats the baseline, validated by `task validate`,
surfaced at `/intelligence/forecasts/maldives-tourism-2026` on staging.

## Layout

```
src/tourism_forecasting/
  pipeline.py     # orchestrates: ingest → contract → features → fit → backtest → export
  models/         # sarima.py, prophet_model.py, xgb.py (one fit/predict interface each)
  config/         # horizons, covariate ids, COVID break dates
notebooks/        # EDA only (nbstripout'd)
tests/
```
