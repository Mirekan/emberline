# pipeline/ — science & data pipeline (shared folder, per-file ownership)

**Rule:** B and C share this directory but own different files; nobody imports
the other's modules — the interface is files under `data/` and `artifacts/`.

| File | Owner | Task | Status |
|---|---|---|---|
<<<<<<< HEAD
| `fetch_firms.py` | B | B-03 | landed (`make data` default run; ≤5-day chunks, resumable, immutable raw; handoff: docs/handoffs/B-03_downloader.md) |
| `validate.py` | B | B-04 | landed (schemas, verbatim confidence, exact-identity dedupe, retrieval masks; tests/test_b_ingestion.py 17/17) |
| `build_fixture.py` | B | B-06 | landed (FIXTURE_REAL_SAMPLE from real validated rows + provenance chain) |
| `time_cache_reload.py` | B | B-06 | landed (monotonic-timed cache reload vs PRD <5 s target; measured PASS 1.85 s / 848k rows) |
| `grid.py` | C | C-02 | pending (0.1° grid, centroid assignment) |
| `match.py` | C | C-02 | pending (cell-day×day/night matched aggregates) |
=======
| `fetch_firms.py` | B | B-03 | pending (≤5-day Area API chunks, resumable, immutable raw) |
| `validate.py` | B | B-04 | pending (schemas, confidence, dedupe, masks) |
| `grid.py` | C | C-02 | **scaffold ✅ fixture-tested**; real-data run pending B-05 |
| `match.py` | C | C-02 | **scaffold ✅ fixture-tested**; real-data run pending B-05 (CLI: `python3 -m pipeline.match --input … --mask … --aoi-id … --bbox …`) |
| `run.py` | C | C-02/C-07 | pending — one-command runner consolidating the pipeline steps |
>>>>>>> f2f4d4b ([science] Implement C-02 grid and matching scaffold? Subject style)
| `harmonize.py` | C | C-04 | pending (B0/B1/B2 per PROTO-C01-v0.9) |
| `metrics.py` | C | C-05 | pending (held-out metrics + N/A policies) |
| `calendar.py` | C | C-06 | pending (366-position climatology) |
| `windows.py` | C | C-06 | pending (critical windows, Dec–Jan wrap) |

**C-02 input seam (what B-04/B-05 must deliver):** detection rows with `source,
satellite, latitude, longitude, daynight, frp_mw` + `acq_datetime_utc`
(preferred, tz-aware ISO) or `acq_date`+`acq_time` (accepted, disclosed), plus
optional `version, confidence, confidence_class, scan, track`; and a retrieval
mask `aoi_id, source, date, status ∈ {retrieved_rows, retrieved_empty, failed,
unavailable, not_requested}`. Exact duplicates or schema drift hard-fail by
design — that is the contract working, not a bug.

Entry points stay in the `Makefile` — add no ad-hoc scripts here.
