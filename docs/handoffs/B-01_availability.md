Task ID: B-01; owner: B; reviewer: D; deliverable/path: pipeline/fetch_firms.py (availability cmd), data/manifests/data_availability_*.csv (local, git-ignored)
run/version ID: keyed probe 2026-11-14T03:15Z; input hashes: ledger sha256 in fetch_ledger.jsonl (local); verification evidence: `python pipeline/fetch_firms.py availability` output saved with hash
limitations: probe reflects FIRMS at probe time; re-probe before extending any end date
requested reviewer action: D — confirm ledger URL fields are key-redacted; next dependency: DEC-1 (C resolves exact source strings)

## B-01 results — resolves DEC-1 inputs (keyed probe, 2026-11-14)

| source | min_date | max_date |
|---|---|---|
| MODIS_SP | 2000-11-01 | 2026-08-31 |
| MODIS_NRT | 2026-09-01 | 2026-11-14 |
| VIIRS_SNPP_SP | 2012-01-20 | 2026-07-31 |
| VIIRS_SNPP_NRT | 2026-08-01 | 2026-11-02 |
| VIIRS_NOAA20_SP | 2018-04-01 | 2026-07-31 |
| VIIRS_NOAA21_SP | 2023-03-01 | 2026-07-31 |

Exact source strings confirmed: **MODIS_SP** and **VIIRS_SNPP_SP** (S-NPP present and deepest
VIIRS archive). Overlap era: **2012-01-20 .. 2026-07-31 (~14.5 y)** — supports the 60/40 split
in PROTO-C01-v0.9. NOTE: the Area API returns one MODIS stream; split Terra/Aqua via the
`satellite` column (verified in real samples: Terra and Aqua rows coexist with a `satellite`
column; VIIRS rows carry `satellite=N`). NRT covers only recent months — never blended into
the SP era. Suggested replacement for `exact_source_strings: "PLACEHOLDER_PENDING_B01"` in
config/params.yaml: `modis_sp = "MODIS_SP" (filter satellite=Aqua)`, `viirs = "VIIRS_SNPP_SP"`.
