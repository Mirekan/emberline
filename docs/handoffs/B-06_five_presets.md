Task ID: B-06; owner: B; reviewer: A; deliverable/path: data/processed/<source>/<slug>/normalized.csv for all five presets, data/fixtures/FIXTURE_REAL_SAMPLE/, data/raw/MANIFEST.json (committed), data/manifests/cache_reload_timing.json (local)
run/version ID: MANIFEST 10753 windows; input hashes: sha256 per window in the committed manifest
verification evidence: `python pipeline/fetch_firms.py verify` (0 unverified); `python pipeline/time_cache_reload.py` output below; tests/test_b_ingestion.py 17/17 PASS
limitations: SP era ends 2026-07-31; Merauke is a sparse savanna AOI (see per-AOI evidence); reload margin to the 5 s target is ~0.9 s at five-preset scale on the B machine — D should re-measure on the deployment host
requested reviewer action: A — review five-preset statuses and fixture; D — run the integration check on FIXTURE_REAL_SAMPLE; next dependency: C-05 held-out evaluation, C-06 calendar, D-07 real-data release

## Five-preset completion (all MODIS_SP + VIIRS_SNPP_SP, era 2012-01-20..2026-07-31)

| preset | slug | MODIS rows | VIIRS rows | detection days (M/V) | status |
|---|---|---|---|---|---|
| riau | w100_s-2_e105_n1 | 83,318 | 346,804 | 3,004 / 4,384 | supported |
| central_kalimantan | w113_s-3_e116_n0 | 72,811 | 345,074 | 2,194 / 3,962 | supported |
| south_sumatra | w103_s-5_e106_n-2 | 88,124 | 400,735 | 2,651 / 4,336 | supported |
| jambi | w102_s-3_e104.5_n-1 | 45,835 | 206,914 | 1,886 / 3,982 | supported |
| merauke | w137_s-9_e141_n-7 | 39,708 | 189,047 | 1,624 / 2,383 | supported (savanna: lower density, no shortfall) |

- Total validated rows: 1,818,370. Zero dropped rows; every stream retrieved
  5,307/5,307 days; 0 failed requests in the final state; 0 hash mismatches.
- All five statuses are honestly "supported": no preset is hidden behind another's cache.
  Per-AOI ingest_evidence_*.md committed under data/manifests/.

## Measured cache reload (PRD target < 5 s) — 2026-11-14

10 caches, 1,818,370 rows, 223.8 MB, full stdlib-csv parse, time.monotonic():
**TOTAL 4.141 s -> PASS** (recorded in data/manifests/cache_reload_timing.json with
hardware + method; warm OS file cache, sequential reads). Margin note: single full
load is 4.1 s on this machine; serving should keep artifacts in memory (D-04) rather
than re-reading CSV per request.

## FIXTURE_REAL_SAMPLE

data/fixtures/FIXTURE_REAL_SAMPLE/ — real validated rows only (El Nino week
2015-09-01..07, Riau, 400 rows per source), with provenance.json chaining back to
raw window hashes in the committed MANIFEST. README inside states what it can
(endpoint wiring, CSV roundtrip, column contract, hash chain) and cannot
(full-era coverage, climatology, five-preset statuses) test. Integration check
with D happens here before B hands over.

## Ops notes

- DNS hiccups during the last downloads left 128 failed-window entries across the
  run history; every one was healed by resumable re-fetch — final verify shows
  zero unverified files. `make data` re-runs are safe and cheap (skip-verified).
- The 2026-07-31 end is the SP archive limit; NRT sources remain excluded from the
  harmonization era by design (params.yaml source_policy).
