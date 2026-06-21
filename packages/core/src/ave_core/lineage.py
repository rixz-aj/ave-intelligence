"""Lineage stamping — every published artifact carries {runId, gitSha, inputHash}.

Traceability is part of the data-engineering contract: given any artifact you can
recover the code revision and the exact input bytes that produced it.
"""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Lineage:
    runId: str
    gitSha: str
    inputHash: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def git_sha() -> str:
    """Short git SHA of the working tree, or 'unknown' outside a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def hash_bytes(payload: bytes) -> str:
    """Content hash of the input bytes, prefixed with the algorithm."""
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def stamp(input_bytes: bytes) -> Lineage:
    """Produce a fresh lineage record for a run over the given input bytes."""
    return Lineage(runId=str(uuid.uuid4()), gitSha=git_sha(), inputHash=hash_bytes(input_bytes))
