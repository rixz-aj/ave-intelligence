"""Register a committed report MDX into published/manifest.json.

Report prose lives as a committed MDX (the website renders it via `marked`); only its
frontmatter + a manifest entry are the contract surface. This validates the frontmatter
against published/meta/report.schema.json before upserting the manifest entry, so a broken
report can never land.

Usage:
    uv run python scripts/publish_report.py published/reports/maldives-tourism-2026.mdx
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from ave_core.export import file_hash, load_manifest, upsert_artifact, write_manifest


def _frontmatter(mdx: str) -> dict[str, object]:
    if not mdx.startswith("---"):
        raise SystemExit("report MDX has no YAML frontmatter")
    _, fm, _ = mdx.split("---", 2)
    loaded = yaml.safe_load(fm)
    if not isinstance(loaded, dict):
        raise SystemExit("report frontmatter is not a mapping")
    return loaded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mdx", type=Path)
    parser.add_argument("--published", type=Path, default=Path("published"))
    args = parser.parse_args(argv)

    fm = _frontmatter(args.mdx.read_text())
    schema = __import__("json").loads((args.published / "meta" / "report.schema.json").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(fm), key=str)
    if errors:
        print("✗ report frontmatter invalid:")
        for error in errors:
            print("  -", error.message)
        return 1

    now = dt.datetime.now(dt.UTC).isoformat()
    rel = args.mdx.relative_to(args.published).as_posix()
    manifest = load_manifest(args.published)
    entry: dict[str, object] = {
        "id": str(fm["slug"]),
        "type": "report",
        "slug": str(fm["slug"]),
        "version": int(fm["version"]),
        "latest": True,
        "path": rel,
        "hash": file_hash(args.mdx),
        "createdAt": now,
    }
    if "pdfUrl" in fm:
        entry["pdfUrl"] = fm["pdfUrl"]
    upsert_artifact(manifest, entry)
    write_manifest(manifest, args.published, generated_at=now, git_sha=manifest.get("gitSha") or "")
    print(f"✓ registered report '{fm['slug']}' → {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
