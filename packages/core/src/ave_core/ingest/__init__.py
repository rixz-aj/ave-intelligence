"""Ingestion connectors — pull raw sources into `data/raw`.

Connectors return tidy DataFrames and never do I/O at import time. See
`docs/DATA-SOURCES.md` for the source register and access caveats.

Planned connectors: `mma_viya` (series 104 + covariates), `mot_pdf` (Ministry of
Tourism Table-1 by-market via `pdftotext -layout`), `worldbank`, `fx`.
"""

from __future__ import annotations
