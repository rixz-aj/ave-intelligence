"""Validate published/ against published/meta/*.schema.json — the public data contract.

Run as `python -m ave_core.export.validate published/` (also the CI gate / `task validate`).
Series & forecast JSON live on R2 and are gitignored locally, so only files actually
present on disk are checked; manifest.json is always validated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

TYPE_TO_SCHEMA: dict[str, str] = {
    "series": "series.schema.json",
    "forecast": "forecast.schema.json",
    "report": "report.schema.json",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text())


def validate_published(published_root: Path) -> list[str]:
    """Return a list of human-readable validation errors (empty == valid)."""
    errors: list[str] = []
    meta = published_root / "meta"

    manifest_path = published_root / "manifest.json"
    if not manifest_path.exists():
        return [f"missing {manifest_path}"]

    manifest = _load(manifest_path)
    manifest_validator = Draft202012Validator(_load(meta / "manifest.schema.json"))
    errors += [f"manifest.json: {e.message}" for e in manifest_validator.iter_errors(manifest)]

    for artifact in manifest.get("artifacts", []):
        schema_name = TYPE_TO_SCHEMA.get(artifact.get("type", ""))
        artifact_path = published_root / artifact.get("path", "")
        if schema_name and artifact_path.exists() and artifact_path.suffix == ".json":
            validator = Draft202012Validator(_load(meta / schema_name))
            for error in validator.iter_errors(_load(artifact_path)):
                errors.append(f"{artifact.get('path')}: {error.message}")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    published_root = Path(args[0]) if args else Path("published")
    errors = validate_published(published_root)
    if errors:
        print(f"✗ {len(errors)} validation error(s):")
        for error in errors:
            print("  -", error)
        return 1
    print("✓ published/ valid against meta/*.schema.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
