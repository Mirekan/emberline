# Ingest evidence - w95_s1_e100_n6 (B-05 / gate G1)

Generated: 2026-11-15T09:47:04+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 2045 retrieved-with-zero-detections
- days with detections: 1089
- rows: raw 5426 -> kept 5426
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Aqua': 4021, 'Terra': 1405}
- detections span: 2018-01-11 .. 2026-07-31
- per-year kept rows:
  - 2018: 853
  - 2019: 554
  - 2020: 512
  - 2021: 446
  - 2022: 419
  - 2023: 397
  - 2024: 474
  - 2025: 1225
  - 2026: 546

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 877 retrieved-with-zero-detections
- days with detections: 2257
- rows: raw 31648 -> kept 31648
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 31648}
- detections span: 2018-01-06 .. 2026-07-31
- per-year kept rows:
  - 2018: 5371
  - 2019: 3643
  - 2020: 3097
  - 2021: 2703
  - 2022: 2678
  - 2023: 2291
  - 2024: 3049
  - 2025: 5817
  - 2026: 2999

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-11 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-28, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

