#!/usr/bin/env bash
# Publish series/forecast JSON + report PDFs to R2 (bucket `nira-media`, served at
# media.avejourneys.com/intelligence/**) — the data side of the CONTRACT.
#
# Write-then-flip: this uploads the immutable versioned artifacts FIRST. The manifest
# (committed in git, and the snapshot synced into nira-app) is what "flips" to point at
# them — so the site never resolves a half-published object.
#
# Requires wrangler authenticated to the Cloudflare account that owns `nira-media`
# (the Apple private-relay account — see the project memory). Usage: `task publish`.
set -euo pipefail

BUCKET="nira-media"
ROOT="${1:-published}"
count=0

put() {  # <file> <content-type>
  local f="$1" ct="$2"
  local key="intelligence/${f#"$ROOT"/}"
  echo "→ r2://$BUCKET/$key"
  npx --yes wrangler r2 object put "$BUCKET/$key" --file "$f" --content-type "$ct" --remote
  count=$((count + 1))
}

# find is portable (macOS ships bash 3.2 — no globstar).
while IFS= read -r f; do put "$f" "application/json"; done \
  < <(find "$ROOT/series" "$ROOT/forecasts" -type f -name '*.json' 2>/dev/null)
while IFS= read -r f; do put "$f" "application/pdf"; done \
  < <(find "$ROOT/reports" -type f -name '*.pdf' 2>/dev/null)

echo "✓ published ${count} artifact(s) to https://media.avejourneys.com/intelligence/"
echo "  (now commit published/manifest.json + sync the report MDX into nira-app)"
