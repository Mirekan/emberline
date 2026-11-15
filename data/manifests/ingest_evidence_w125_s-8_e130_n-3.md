# Ingest evidence - w125_s-8_e130_n-3 (B-05 / gate G1)

Generated: 2026-11-15T09:47:10+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 2399 retrieved-with-zero-detections
- days with detections: 735
- rows: raw 2506 -> kept 2506
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 975, 'Aqua': 1531}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 408
  - 2019: 794
  - 2020: 166
  - 2021: 94
  - 2022: 100
  - 2023: 537
  - 2024: 167
  - 2025: 99
  - 2026: 141

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1732 retrieved-with-zero-detections
- days with detections: 1402
- rows: raw 12437 -> kept 12437
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 12437}
- detections span: 2018-01-06 .. 2026-07-31
- per-year kept rows:
  - 2018: 1789
  - 2019: 4200
  - 2020: 969
  - 2021: 428
  - 2022: 461
  - 2023: 2523
  - 2024: 793
  - 2025: 641
  - 2026: 633

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-06 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-26, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

