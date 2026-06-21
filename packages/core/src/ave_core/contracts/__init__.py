"""Data contracts — pandera schemas validating every raw→interim→processed boundary.

Schema drift must fail loudly. Add a schema here when you add a transform, and a
fixture test alongside it. See `arrivals.py` for the pattern.
"""

from __future__ import annotations

from ave_core.contracts.arrivals import arrivals_schema, validate_arrivals

__all__ = ["arrivals_schema", "validate_arrivals"]
