# pipeline/ — science & data pipeline (shared folder, per-file ownership)

**Rule:** B and C share this directory but own different files; nobody imports
the other's modules — the interface is files under `data/` and `artifacts/`.

| File | Owner | Task | Status |
|---|---|---|---|
| `fetch_firms.py` | B | B-03 | landed (`make data`; ≤5-day chunks, resumable, immutable raw; handoff: docs/handoffs/B-03_downloader.md) |
| `validate.py` | B | B-04 | landed (schemas, verbatim confidence, exact-identity dedupe, retrieval masks; tests/test_b_ingestion.py 17/17) |
| `build_fixture.py` | B | B-06 | landed (FIXTURE_REAL_SAMPLE from real validated rows + provenance chain) |
| `time_cache_reload.py` | B | B-06 | landed (monotonic-timed cache reload vs PRD <5 s target; measured 1.85 s / 848k rows) |
| `grid.py` | C | C-02 | **scaffold ✅ fixture-tested**; Riau swap-in run 2026-11-14 |
| `match.py` | C | C-02 | **scaffold ✅ + Riau fixture swap-in** (CLI: `python3 -m pipeline.match --input <modis.csv> <viirs.csv> --mask <mask.csv> --aoi-id … --bbox …`; mask clipped to delivered window, disclosed) |
| `ledger_to_mask.py` | C | C-02 | **✅ converts B-03 fetch_ledger.jsonl → retrieval-mask csv** |
| `run.py` | C | C-07 | **✅ one-command orchestrator** (`make reproduce AOI=<id>`; full chain + F-19 run manifest with stage statuses recorded verbatim) |
| `baselines.py` | C | C-03 | **scaffold ✅** (B0/B1 on frozen date-split; leakage-guarded; CLI `python3 -m pipeline.baselines --pairs <matched_pairs.csv> --aoi-id …`; real Riau fixture honestly returns insufficient_data) |
| `harmonize.py` | C | C-04 | **scaffold ✅** (B2 monotone log-space `a + b·log1p(S_v) + c·log1p(1+n) + d·I_night`, b/c≥0 via recorded projection; Duan smearing training-only; AOI-daily day-bootstrap intervals — nominal 80%, measured at C-05; zero policy v1: no-VIIRS-signal→0; CLI `python3 -m pipeline.harmonize --pairs … --aoi-id …`; real Riau fixture → insufficient_data) |
| `metrics.py` | C | C-05 | **✅ 12-metric held-out menu + LOYO + N/A policies** (identical-held-out-rows enforced; deferred ≠ failed; CLI `python3 -m pipeline.metrics --baselines … --harmonized … --pairs … --aoi-id …`) |
| `splice_stress.py` | C | C-05 | **✅ ≥3 predetermined pseudo-transitions vs continued-MODIS truth** (peak-of-segment rule, ±14 d windows, ≥70% retrieval; negative results labeled; no p-values; CLI `python3 -m pipeline.splice_stress --baselines … --harmonized … --aoi-id …`) |
| `metrics.py` | C | C-05 | pending (held-out metrics + N/A policies) |
| `calendar.py` | C | C-06 | **✅** (accepted series F-14 + frozen P95 denominator + 366-position climatology w/ circular ±7d smoothing; calendar-era eligibility rule; CLI `python3 -m pipeline.calendar --harmonized … --units … --aoi-id …`) |
| `windows.py` | C | C-06 | **✅** (critical windows = p75 of smoothed curve, runs ≥3 d, Dec–Jan wrap; years_active DEC-3 provisional; CLI `python3 -m pipeline.windows --calendar-dir …`) |

**C-02 input seam (what B-04/B-05 deliver):** detection rows with `source,
satellite, latitude, longitude, daynight, frp_mw` + `acq_datetime_utc`
(preferred, tz-aware ISO) or `acq_date`+`acq_time` (accepted, disclosed), plus
optional `version, confidence_raw, confidence_class, scan, track`; and a
retrieval mask `aoi_id, source, date, status ∈ {retrieved_rows,
retrieved_empty, failed, unavailable, not_requested}` — built from
`data/manifests/fetch_ledger.jsonl` via `pipeline/ledger_to_mask.py`. Exact
duplicates or schema drift hard-fail by design — that is the contract working,
not a bug.

Entry points stay in the `Makefile` — add no ad-hoc scripts here.
