# Ingest evidence - w130_s-6_e135_n-1 (B-05 / gate G1)

Generated: 2026-11-15T09:47:09+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 2741 retrieved-with-zero-detections
- days with detections: 393
- rows: raw 948 -> kept 948
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Aqua': 654, 'Terra': 294}
- detections span: 2018-01-06 .. 2026-07-30
- per-year kept rows:
  - 2018: 66
  - 2019: 307
  - 2020: 110
  - 2021: 22
  - 2022: 45
  - 2023: 165
  - 2024: 46
  - 2025: 52
  - 2026: 135

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1815 retrieved-with-zero-detections
- days with detections: 1319
- rows: raw 5712 -> kept 5712
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 5712}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 659
  - 2019: 1945
  - 2020: 695
  - 2021: 246
  - 2022: 276
  - 2023: 826
  - 2024: 268
  - 2025: 209
  - 2026: 588

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-06 .. 2026-07-30 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-25, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

