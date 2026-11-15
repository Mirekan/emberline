# Ingest evidence - w132_s-9_e137_n-4 (B-05 / gate G1)

Generated: 2026-11-15T09:46:52+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 2907 retrieved-with-zero-detections
- days with detections: 227
- rows: raw 421 -> kept 421
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Aqua': 311, 'Terra': 110}
- detections span: 2018-01-01 .. 2026-07-29
- per-year kept rows:
  - 2018: 108
  - 2019: 69
  - 2020: 31
  - 2021: 28
  - 2022: 31
  - 2023: 76
  - 2024: 31
  - 2025: 6
  - 2026: 41

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 2468 retrieved-with-zero-detections
- days with detections: 666
- rows: raw 2617 -> kept 2617
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 2617}
- detections span: 2018-01-07 .. 2026-07-31
- per-year kept rows:
  - 2018: 682
  - 2019: 391
  - 2020: 166
  - 2021: 109
  - 2022: 133
  - 2023: 618
  - 2024: 158
  - 2025: 66
  - 2026: 294

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-07 .. 2026-07-29 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-25, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

