"""I/O — parquet read/write for the data lake, plus R2/S3 readers and writers.

Phase 0: implement `read_parquet`/`write_parquet` over `data/{interim,processed}`
and an `R2Writer` that uploads `published/series` + `published/forecasts` + PDFs to
`media.avejourneys.com/intelligence/**`. Keep all network I/O inside functions —
never at import time.
"""

from __future__ import annotations
