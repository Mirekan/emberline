Task ID: B-02/B-03; owner: B; reviewer: C (B-02) / D (B-03); deliverable/path: config/aois.yaml, pipeline/fetch_firms.py, pipeline/validate.py, tests/test_b_ingestion.py
run/version ID: ledger + MANIFEST.json regenerated on every `make data` run; input hashes: fetch_ledger.jsonl -> data/raw/MANIFEST.json
verification evidence: `python tests/test_b_ingestion.py` = 17/17 PASS (synthetic FIXTURE_SYNTHETIC only); full-AOI evidence lands in data/manifests/ingest_evidence_*.md when the two G1 downloads finish
limitations: five-preset list deviates from grid.yaml's original global candidates (see OPEN FLAG below); SP era ends 2026-07-31
requested reviewer action: C — review AOI choices vs training/test support; D — review make data flow + redaction; next dependency: B-05 evidence -> C-02; DEC-2 support numbers

## What landed

- `pipeline/fetch_firms.py` — resumable FIRMS downloader. Default run = the `make data`
  target: reads config/aois.yaml, fetches every AOI/source/date range in <=5-day windows
  (verified live API cap), throttled, bounded retries, immutable raw bytes + per-file
  SHA-256, distinguishes ok / ok_empty / failed in the ledger, writes
  data/raw/MANIFEST.json (the committed manifest). Key never printed or logged; ledger
  URLs are key-redacted. Subcommands: availability / fetch / inspect / manifest.
- `pipeline/validate.py` — per-source schema validation + normalization
  (data/processed/<source>/<slug>/normalized.csv), drop counts per reason, per-day
  retrieval masks, per-year rows, and ingest_evidence_<slug>.md for G1.
  Contract alignment with PROTO-C01-v0.9: exact-identity dedupe key incl. version +
  daynight, coordinate rounding only in output formatting (never in the dedupe key),
  original confidence kept verbatim + scale recorded, no confidence filtering here
  (that is C's params.yaml decision), four-state missingness preserved
  (failed vs zero-detections vs unavailable vs retrieved), hash-mismatch quarantine.
- `config/aois.yaml` — B-02 five presets (riau, central_kalimantan, south_sumatra,
  jambi, merauke; all <=5 deg, sources MODIS_SP + VIIRS_SNPP_SP, 2012-01-20..2026-07-31).
- `tests/test_b_ingestion.py` — 17 checks incl. duplicate-vs-nearby, quarantine,
  empty-vs-failed payloads. Synthetic fixture lives only inside the test.

## OPEN FLAG for A/C — preset substitution

grid.yaml's expected_presets mention northern_california / pantanal / nsw_victoria.
The team approved an all-Indonesia five-preset list on 2026-11-14 (riau + central_kalimantan
are the two G1 AOIs; their full-era downloads are complete/in flight). If the team prefers
the global story instead, swap presets in config/aois.yaml BEFORE the remaining three
downloads start; riau/central_kalimantan stay usable either way. C should also replace
`exact_source_strings: "PLACEHOLDER_PENDING_B01"` in params.yaml (values in
docs/handoffs/B-01_availability.md) and confirm DEC-1/DEC-2 numbers.

## Note for D-01

- tests/test_protocol_contract.py needs PyYAML; pipeline/* B files are stdlib-only
  (`make data` works with plain python3 + no pip installs). tests/test_b_ingestion.py
  is also stdlib-only and can join `make test` as-is.
- Fetch verified on Python 3.14/3.11 (Windows). One resumed crash (read timeout during
  large VIIRS response body) was fixed by retrying all OSError subclasses; a resumed run
  skips only ledger-verified windows.
