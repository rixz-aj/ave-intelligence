# Web integration — building the `/intelligence` consumer in `nira-app`

This spec lives here (in the data repo) so the contract has one home. When you build
the web slice, **switch to `../nira-app`** and follow this. Read `CONTRACT.md` first.

`nira-app` is TanStack Start (React 19, Vite 8) on Cloudflare Workers + D1 + R2.
The `/intelligence` section mirrors the existing `/journal` pattern. It is a pure
consumer of `published/` artifacts — no Python, no model code.

> ⚠️ `nira-app` ships its whole working tree on deploy (incl. WIP). Never commit a
> half-synced `intelligence-content/`. `sync-intelligence.ts` must **validate before
> write**, and `/intelligence` routes must skip missing artifacts gracefully rather
> than error the page.

## Files to create in `nira-app`

```
src/routes/intelligence/
  index.tsx                 # landing: report/article list (clone src/routes/journal/index.tsx)
  $slug.tsx                 # report detail: marked(body) → .ave-prose + inline <EditorialChart/>
src/data/
  intelligence.ts           # type IntelligenceArticle + INTELLIGENCE_ARTICLES (metadata; client-safe; feeds sitemap)
  intelligence-content/      # COMMITTED from this repo via the sync script
    manifest.json            # snapshot of published/manifest.json (pins artifact versions)
    reports/*.mdx            # report bodies + frontmatter (diffable, SSR-rendered)
src/lib/
  intelligence-manifest.ts  # fetch + cache media.avejourneys.com/intelligence/manifest.json; resolve latest→vN
src/components/intelligence/
  EditorialChart.tsx        # Observable Plot → server-rendered static SVG via .toHyperScript()
  HeroFigure.tsx            # hand-rolled SVG for 1–3 signature graphics
  SourceLine.tsx            # "Source: Avé Intelligence · n=…" muted tabular
  MethodologyNote.tsx       # trust layer — NO founder faces (brand rule)
scripts/
  sync-intelligence.ts      # pull manifest + reports/*.mdx from this repo; validate vs meta/*.json; write into src/data/intelligence-content/
```

## Files to edit in `nira-app`

- **`src/components/shell/nav.tsx`** — insert Intelligence into `NAV_RIGHT` so it sits
  before Journal: `{ label: 'Intelligence', hoverLabel: 'Data', to: '/intelligence' }`.
  The mobile menu derives from `NAV_LEFT + NAV_RIGHT` automatically. (Nav is hardcoded
  around lines 19–27; `NavLink` is reusable; `isActive()` handles slug matching.)
- **`src/lib/sitemap.ts`** — add `/intelligence` to `STATIC_PATHS` and loop
  `INTELLIGENCE_ARTICLES` to push `/intelligence/${slug}` entries (published-only filter,
  same as ISLANDS/CHARTERS/JOURNEYS).
- **`src/styles.css`** — add the editorial chart tokens under `:root` (+ dark block):
  `Ink #16181D`, `Paper #FBF8F1`, `Paper Deep #F3EEE3`, `Hairline #E3DCCD`,
  gold ramp (`Gold Wash #EFE4CC` → `Avé Gold #B08D4F` → `Gold Deep #8A6D34`),
  optional `Deep Teal #1F4E4A`. Reuse existing `--font-serif/--font-sans/--font-mono`.

## Rendering rules (the design language)

The chart system is **Observable Plot rendered server-side to static SVG**
(`.toHyperScript()` React pattern — crawlable, zero client JS, fast LCP), with
hand-rolled SVG for 1–3 hero graphics. Follow the FT / Economist / Our-World-in-Data
doctrine — full spec in [`docs/DESIGN-SYSTEM.md`](./DESIGN-SYSTEM.md):

- Horizontal hairline gridlines only; no chart frame, no vertical grid, drop the y-axis spine.
- **Direct end-of-line labels**, not legend boxes. Gold = the focus series; everything
  else fades to neutral. Max ~4 categorical colors.
- Active-voice **takeaway** chart titles ("Occupancy held above 80% through the
  shoulder season"), not metric names. Always a muted source line ("Source: Avé
  Intelligence · n=…").
- Tabular lining figures everywhere data aligns (`font-feature-settings: 'tnum'`).
- No tooltips/shadows/gradients/rounded bars/donuts/3D/scroll-animation by default.

## Data flow at render time

1. Build/deploy uses the **committed** `intelligence-content/manifest.json` snapshot
   (reproducible).
2. `EditorialChart` resolves an artifact `id` → manifest entry → R2 `url` →
   fetches the series/forecast JSON → Plot renders SVG on the server.
3. Report pages: `marked.parse(mdxBody)` → `.ave-prose`; frontmatter → `INTELLIGENCE_ARTICLES`
   → sitemap + `pageMeta()` + `canonical()` (per `src/lib/seo.ts`).

## D1 — only if needed later

Start with **committed static content** (no migration). Add a `drizzle/000X_intelligence.sql`
table (or a `content_type` flag on `journal_posts`) + `scripts/build-intelligence-seed.ts`
ONLY when you need a draft/publish gating workflow. Wrap any D1 read in `createServerFn`.
