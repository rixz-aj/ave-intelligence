# Design system — Avé Intelligence

The aesthetic: a tourism-research **publication** — Financial Times × Bloomberg ×
Skift Research × Our World in Data, fused with the Avé luxury brand (Patina-grade
restraint). **Editorial first, analytics second.** A chart is a typographic object,
not a widget. This doc governs both the website charts and any exported PDF reports.

> The anti-goal is a SaaS/admin dashboard. If a layout reads as "KPI tiles + left-rail
> icon nav + colored stat cards", it's wrong.

## Palette

Ink-on-cream. Pure `#000`/`#FFF` are banned — they break the print illusion.

| Token | Hex | Use |
|---|---|---|
| Ink | `#16181D` | headlines, body, primary data series, axis labels (≈90% opacity for body) |
| Graphite | `#3D414B` | deck/standfirst, captions, chart subtitles; default single-series line |
| Slate Muted | `#6B7079` | meta, datelines, kickers, **faded context** (non-focus) series |
| Paper | `#FBF8F1` | page + chart-canvas background (warm ivory) |
| Paper Deep | `#F3EEE3` | pull-quotes, table zebra, plot-area tint, cards |
| Hairline | `#E3DCCD` | rules, gridlines, table borders — gridlines must *whisper* |
| **Avé Gold** | `#B08D4F` | THE accent: wordmark, **focus series**, kickers, key numbers, rule above chart titles. Keep < ~5% of any view |
| Gold Deep | `#8A6D34` | gold-as-small-text (passes contrast on Paper), gold link hover, in-chart gold labels |
| Gold Wash | `#EFE4CC` | area-fill under the gold series, highlighted rows (10–18% presence only) |
| Deep Teal | `#1F4E4A` | OPTIONAL 2nd categorical color (warm/cool w/ gold); charts only, never UI chrome |
| Signal Red | `#9E3B2E` | negative deltas / below-benchmark (brick, not alert-red) |
| Positive Green | `#3F6B4E` | positive deltas (muted forest, figures only) |

## Typography — three roles, never mixed

1. **Serif display** — headlines, deck, pull-quotes, big stat numerals. Tight:
   line-height 1.05–1.12, tracking −0.01em at large sizes. (Site already self-hosts
   **Cormorant Garamond**; for new editorial weight consider Newsreader / Fraunces /
   Source Serif as open alternatives, or GT Super / Canela / Tiempos commercially.)
2. **Sans text/UI** — body, captions, nav, labels. Body 17–19px, line-height 1.6,
   measure 62–72ch. (Site uses **Inter Tight**.)
3. **Mono / tabular figures** — ALL data (table cells, axis ticks, in-chart labels,
   KPIs). Must use true tabular lining figures so columns align. (Site uses
   **JetBrains Mono**; or `font-feature-settings: 'tnum' 1, 'lnum' 1` on the sans.)

Kickers/eyebrows: small-caps, letter-spacing 0.08em.

## Charts — FT / Economist / OWID doctrine

- **Gridlines:** horizontal only, 1px, Hairline. No vertical grid, no frame/box.
  Drop the y-axis spine (gridlines carry the scale); keep a thin x baseline. The
  zero/reference baseline is the only emphasized rule (1.5px Ink/Graphite).
- **Axes:** tick labels in tabular mono, Slate Muted, 12–13px, rounded/abbreviated
  (`1.2k`, `$4m`). Y-axis unit caption sits **above** the top tick ("Occupancy, %"),
  not rotated on the side.
- **Lines:** focus 2.25–2.5px solid; context 1.25px Slate Muted; ≤ ~4 lines (else
  small-multiples). One end-dot on the focus line; no markers on dense lines.
- **Direct labeling**, not legends — label each line at its right end in the line's
  own color (Economist/OWID hallmark). Kill the legend box.
- **Color encoding:** sequential = gold ramp (Wash→Gold→Deep); categorical = gold +
  Deep Teal + Slate (≤4); diverging = Signal Red ↔ neutral ↔ Positive Green. **Gold
  is always "this is the point"; everything else fades to neutral.**
- **Annotation:** in-chart text (not tooltips) with a thin leader line calls out the
  one insight (FT/NYT-style).
- **Title block:** left-aligned active-voice **takeaway** headline in serif
  ("Resort occupancy held above 80% through the shoulder season") + a Graphite
  sub-deck explaining the metric + a gold hairline rule above.
- **Source line:** bottom-left, Slate Muted, 11–12px tabular —
  "Source: Avé Intelligence · n=27 properties". This is part of the aesthetic and
  signals rigor; never omit it.
- **Numbers:** tabular lining figures, consistent decimals per column, thin-space
  thousands, right-align numeric columns. Bars: single gold fill, gap ~40%, no 3D /
  rounded corners. Sparklines allowed inline in tables.

## Implementation

**Observable Plot, server-rendered to static SVG** via the `document` option +
`.toHyperScript()` (React pattern; see https://observablehq.com/plot/getting-started).
It SSRs to crawlable SVG with no browser DOM, needs no client hydration for static
figures, and maps the doctrine above almost 1:1 (`axis: null`, custom `tickFormat`,
`Plot.text` for direct labels/annotations, CSS-var-driven `stroke`/`fill`).

- **Hero graphics (1–3):** hand-rolled SVG-in-React for set pieces where pixel craft
  matters (the site's `atlas-map-canvas.tsx` is the precedent).
- **Interactive charts:** a clearly-scoped client island only when genuinely needed.
- **Not** Recharts/nivo as the system — their defaults are the dashboard look we reject.

## Do-nots

KPI-tile dashboards · pure black/white · gold sprawl (>5%) · rainbow/12-color cycles ·
chart frames / vertical / heavy gridlines · legend boxes when direct labels work ·
non-tabular figures in aligned columns · tooltips/shadows/gradients/rounded bars/
donuts/3D · centered or unhyphenated-justified body · mixing the three type roles ·
shipping heavy interactive chart bundles for static figures · default scroll/entrance
animation · titling charts with the metric name · omitting the source/methodology line ·
**founder faces / stock "team" photos in the trust layer** (brand rule — use
methodology + `n=` instead).

## References

FT Visual Vocabulary · The Economist "Mistakes, we've drawn a few" · Our World in Data
(owid-grapher) · NYT/Upshot annotation · Bloomberg Graphics · Skift Research / McKinsey
Global Institute exhibits · Pew (methodology-forward) · Observable Plot SSR docs.
