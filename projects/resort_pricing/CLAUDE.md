# CLAUDE.md — Project B: resort_pricing

**Phase 2.** Explain what drives Maldives resort pricing (ADR). Read root `CLAUDE.md`
+ `../../CONTRACT.md` first. Reuse `ave_core` ingest/contracts/features — don't fork them.

## Objective
What drives average daily rate? Which variables matter most, which atolls command a
premium, and what is the effect of brand affiliation?

## Inputs (publicly available resort attributes)
Room rate, star rating, atoll, transfer type, distance from MLE, amenities, brand.
(`nira-app` already has structured resort data in `src/data` — a useful cross-reference
for the attribute set; collect pricing from public sources.)

## Analysis
Pricing distribution · luxury-premium · geographic (by atoll) · transfer-impact ·
brand-premium. Then a regression (OLS / regularized) explaining ADR drivers with
clearly reported coefficients and diagnostics.

## Outputs
A price-index series + a pricing report MDX with editorial charts, written into
`published/` via `ave_core.export`. Surfaces at `/intelligence/resort-pricing/market-overview`.

## Definition of Done
Published pricing artifacts + a live market-overview report; `task validate` green.
