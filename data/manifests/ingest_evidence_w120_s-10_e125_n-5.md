# Ingest evidence - w120_s-10_e125_n-5 (B-05 / gate G1)

Generated: 2026-11-15T09:46:59+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1359 retrieved-with-zero-detections
- days with detections: 1775
- rows: raw 17493 -> kept 17493
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 5853, 'Aqua': 11640}
- detections span: 2018-01-08 .. 2026-07-31
- per-year kept rows:
  - 2018: 2345
  - 2019: 3264
  - 2020: 1915
  - 2021: 1538
  - 2022: 1123
  - 2023: 3653
  - 2024: 1954
  - 2025: 1499
  - 2026: 202

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 892 retrieved-with-zero-detections
- days with detections: 2242
- rows: raw 99224 -> kept 99224
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 99224}
- detections span: 2018-01-08 .. 2026-07-31
- per-year kept rows:
  - 2018: 14008
  - 2019: 17795
  - 2020: 11105
  - 2021: 8213
  - 2022: 5743
  - 2023: 20253
  - 2024: 10768
  - 2025: 10162
  - 2026: 1177

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-08 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-27, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

