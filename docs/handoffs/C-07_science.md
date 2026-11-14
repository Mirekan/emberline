# Handoff — C-07 science packaging

Task: C-07 · owner: C · reviewer: A · date: 14 Nov 2026 ~16:00 WIB ·
deliverable: one-command pipeline + run manifest + docs · reviewer action: verify a
reproduction run and the manifest fields (A), then D/E/F consume the same evidence.

## Exact commands

```
make reproduce AOI=riau     # full chain: match → baselines → harmonize →
                            # metrics → stress → calendar → windows
make test                   # 9 contract suites (C-01..C-07 + B ingestion)
```

Note for the team: `tests/test_run_manifest.py` executes the full chain and is the
memory-heaviest suite — run `make reproduce` / `make test` when the machine has
headroom (team gate time), not continuously.

## Artifact paths (per AOI, versioned by run_id inside each manifest)

- `data/processed/<aoi>/c02/` — matched pairs + units (C-02)
- `artifacts/<aoi>/baseline_series.csv`, `baselines.json` (C-03)
- `artifacts/<aoi>/harmonized_daily.csv`, `model_manifest.json` (C-04)
- `artifacts/<aoi>/harmonization_metrics.json`, `splice_stress_test.json` (C-05)
- `artifacts/<aoi>/accepted_series.csv`, `calendar.csv`, `climatology.json`,
  `windows.json` (C-06)
- `artifacts/<aoi>/run_manifest.json` (C-07: F-19 provenance, stage statuses)

## Known gaps (verbatim, not hidden)

1. Full-era normalized rows + Kalteng processed files not yet delivered by B →
   real-data fitting/metrics/calendar honestly return `insufficient_data`/`deferred`
   on the compact Riau fixture; real evaluation lands with the era-penuh swap-in.
2. pyarrow not pinned yet (D-01 proposal: requirements.txt committed) — CSV
   primary until then; full-era volumes need parquet.
3. C-01 sign-offs (B/D/E boxes in method.md §8) still open — required BEFORE any
   real-data fitting.
4. Changepoint significance: not implemented (no p-values; recorded as such).

## Contracts for consumers

- D: serve `artifacts/<aoi>/` files as-is; statuses from manifests; never recompute.
- E: `accepted_series.csv` (index + raw MW + source_flag), `calendar.csv`
  (366 positions + smoothed median + p10-p90), `windows.json` (threshold meaning,
  wraps_dec_jan, years_active/eligible) — legend vocabulary in method.md F-9/F-18.
- F: claims ONLY from manifests (error_ratio, coverage) — "deferred" stages must be
  stated as deferred in the demo; limitations.md is the plain-language source.
