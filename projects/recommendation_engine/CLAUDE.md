# CLAUDE.md — Project C: recommendation_engine

**Phase 3.** A traveler recommendation engine that supports the website's Begin /
concierge flow. Read root `CLAUDE.md` + `../../CONTRACT.md` first.

## Objective
Given budget, travel dates, trip type, traveler count, travel style, and interests
(honeymoon, family, diving, ultra-luxury, wellness, adventure), recommend resorts,
islands, experiences, and itineraries.

## Phasing (within this project)
1. **Rule-based** engine (transparent, shippable first).
2. **Scoring** engine (weighted feature scores).
3. **ML** recommendation (learned ranking / similarity).

## Inputs
Consumes Project A forecasts (seasonality/peak timing) and Project B pricing signals
as features — this cross-project dependency is the platform proving itself. Resort/
island attributes come from `nira-app`'s structured data.

## Integration
Surfaces in `nira-app`: the Begin page, the concierge inquiry flow, and resort/atlas
discovery. Expose a clean scoring interface the website can call; keep model internals here.

## Definition of Done
A recommendation service (scoring tier minimum) consumed by the Begin/concierge flow.
