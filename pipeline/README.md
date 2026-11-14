# pipeline/ — science & data pipeline (shared folder, per-file ownership)

**Rule:** B and C share this directory but own different files; nobody imports
the other's modules — the interface is files under `data/` and `artifacts/`.

| File | Owner | Task | Status |
|---|---|---|---|
| `fetch_firms.py` | B | B-03 | pending (≤5-day Area API chunks, resumable, immutable raw) |
| `validate.py` | B | B-04 | pending (schemas, confidence, dedupe, masks) |
| `grid.py` | C | C-02 | pending (0.1° grid, centroid assignment) |
| `match.py` | C | C-02 | pending (cell-day×day/night matched aggregates) |
| `harmonize.py` | C | C-04 | pending (B0/B1/B2 per PROTO-C01-v0.9) |
| `metrics.py` | C | C-05 | pending (held-out metrics + N/A policies) |
| `calendar.py` | C | C-06 | pending (366-position climatology) |
| `windows.py` | C | C-06 | pending (critical windows, Dec–Jan wrap) |

Entry points stay in the `Makefile` — add no ad-hoc scripts here.
