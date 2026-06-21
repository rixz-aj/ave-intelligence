"""Read / update / write published/manifest.json — the index the website reads.

Publish order is **write-then-flip**: upload artifacts to R2 first, then update the
manifest, so the manifest never points at a half-published object (see CONTRACT.md).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"


def file_hash(path: Path) -> str:
    """Content hash of an artifact file (matches the lineage hash format)."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(published_root: Path) -> dict[str, Any]:
    """Load manifest.json, or return an empty manifest if none exists yet."""
    path = published_root / "manifest.json"
    if path.exists():
        loaded: dict[str, Any] = json.loads(path.read_text())
        return loaded
    return {"schemaVersion": SCHEMA_VERSION, "generatedAt": None, "gitSha": None, "artifacts": []}


def upsert_artifact(manifest: dict[str, Any], artifact: dict[str, Any]) -> None:
    """Insert or replace an artifact entry, keyed by its unique `id` (in place)."""
    existing: list[dict[str, Any]] = manifest.get("artifacts", [])
    manifest["artifacts"] = [a for a in existing if a.get("id") != artifact["id"]] + [artifact]


def write_manifest(
    manifest: dict[str, Any],
    published_root: Path,
    *,
    generated_at: str,
    git_sha: str,
) -> Path:
    """Stamp generation metadata and write manifest.json (the flip step)."""
    manifest["schemaVersion"] = SCHEMA_VERSION
    manifest["generatedAt"] = generated_at
    manifest["gitSha"] = git_sha
    path = published_root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path
