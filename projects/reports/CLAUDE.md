# CLAUDE.md — Project D: reports

**Phase 4.** The recurring intelligence-report system — the most visible, most
"publishable" output. Read root `CLAUDE.md` + `../../CONTRACT.md` first.

## Objective
Turn the platform's series/forecasts/analyses into editorial reports that read like
Skift Research / McKinsey exhibits — same MDX source renders on the website and
exports to PDF.

## Recurring report types
Maldives Tourism Outlook · China Market Update · India Market Update · Luxury Travel
Trends · Aviation Capacity · Resort Development Pipeline.

## Each report includes
Executive summary · key findings · charts (artifact-id references) · market commentary
· strategic implications · sources + methodology (`n=`).

## Build
`report_builder` (Jinja2 templates) emits a `published/reports/{slug}.mdx` (frontmatter
validated by `report.schema.json`) and a matching PDF (same source → R2). Charts are
referenced by artifact `id` and resolved on the website via the manifest. Consolidates
outputs from Projects A–C.

## Definition of Done
`/intelligence/reports` index + several publishable, PDF-exportable reports live;
CI validates `published/` against `meta/`; one hand-rolled SVG hero graphic for the flagship.
