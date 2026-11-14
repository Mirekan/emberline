Task ID: B-05; owner: B; reviewer: C (overlap) + A (gate G1 sign-off, do not pass ourselves); deliverable/path: data/manifests/ingest_evidence_w100_s-2_e105_n1.md + data/manifests/ingest_evidence_w113_s-3_e116_n0.md (local, git-ignored) — this file is the committed summary
run/version ID: validation reports regenerated 2026-11-14T06:1xZ after ledger repair; input hashes: data/raw/MANIFEST.json (4249 windows, sha256 per window)
verification evidence: `python pipeline/validate.py --slug <slug> --source MODIS_SP VIIRS_SNPP_SP`; recount via the JSON reports; tests/test_b_ingestion.py 17/17 PASS
limitations: era capped at SP availability (2026-07-31); retrieved-day ≠ observed-clear-sky; detections are hotspots, not fires
requested reviewer action: C — confirm minimum support (DEC-2) and freeze split before fitting; A — gate G1 decision; next dependency: C-02 on matched aggregates

## G1 evidence summary — two AOIs, both sensor families, zero failures

All numbers from keyed FIRMS Area API (SP archives), immutable raw windows verified
against SHA-256, then validated by pipeline/validate.py. 0 failed requests, 0 hash
mismatches, 0 dropped rows across all four streams.

### AOI 1 — Riau (w100_s-2_e105_n1, 100,-2,105,1)

| | MODIS_SP | VIIRS_SNPP_SP |
|---|---|---|
| rows kept | 83,318 | 346,804 |
| Aqua / Terra | 48,295 / 35,023 | — (satellite=N) |
| retrieved days | 5,307 | 5,307 |
| days with detections | 3,004 | 4,384 |
| retrieved, zero detections | 2,303 | 923 |
| weakest year | 544 rows (2022) | 2,527 rows (2026, partial) |
| peak year | 20,135 (2015, El Niño) | 92,539 (2015, El Niño) |

### AOI 2 — Central Kalimantan (w113_s-3_e116_n0, 113,-3,116,0)

| | MODIS_SP | VIIRS_SNPP_SP |
|---|---|---|
| rows kept | 72,811 | 345,074 |
| Aqua / Terra | 44,878 / 27,933 | — (satellite=N) |
| retrieved days | 5,307 | 5,307 |
| days with detections | 2,194 | 3,962 |
| retrieved, zero detections | 3,113 | 1,345 |
| weakest year | 334 rows (2022) | see report JSON |

### What this establishes

- Both sensor families present for both AOIs across 2012-01-20 .. 2026-07-31 (~14.5 y).
- Aqua reference support: 93,173 Aqua rows total across the two AOIs — S-01 is feasible
  without Terra pooling (DEV-S01).
- Every calendar year has non-trivial support in both AOIs (weakest: 334 MODIS rows in
  2022 Kalteng) — input for C's minimum-support freeze (DEC-2).
- 2015 El Niño signal is strongly present — good validation/stress-test material.
- Suggested ~60/40 temporal split for C-01 (detections-based): train through 2020-10-08,
  test after — C decides and freezes BEFORE fitting (never tune on test years).

### What this does NOT establish

- Zero-detection days (2,303 Riau MODIS / 921 Riau VIIRS / 3,091+1,331 Kalteng) are
  successful queries with no rows — NOT proof of no fire, no clear-sky observation
  opportunity, and not zero-filled anywhere.
- MODIS is the reference measurement, not fire ground truth.
- Era is capped at 2026-07-31 (SP archive limit); NRT is never blended into this era.
- The five-preset AOI list substitutes global candidates from grid.yaml — recorded as an
  OPEN FLAG in docs/handoffs/B-03_downloader.md pending A/C confirmation.

### Provenance note (ledger repair, 2026-11-14T06:1xZ)

Running the two AOI downloads in parallel appended to one fetch_ledger.jsonl from two
processes; 14 window entries were lost to the append race and 2 lines arrived corrupt.
The resume design self-healed this: a re-run re-fetched exactly those 14 windows, the
2 corrupt fragments were purged, and the final provenance check confirms every one of
the 4249 window files matches a ledger sha256. Lesson recorded: run AOI fetches
sequentially (or give each stream its own ledger) when others re-run `make data`.
