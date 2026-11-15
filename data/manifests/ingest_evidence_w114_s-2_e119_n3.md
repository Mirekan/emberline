# Ingest evidence - w114_s-2_e119_n3 (B-05 / gate G1)

Generated: 2026-11-15T09:46:50+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1508 retrieved-with-zero-detections
- days with detections: 1626
- rows: raw 19954 -> kept 19954
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 4965, 'Aqua': 14989}
- detections span: 2018-01-25 .. 2026-07-31
- per-year kept rows:
  - 2018: 2541
  - 2019: 5706
  - 2020: 1520
  - 2021: 740
  - 2022: 596
  - 2023: 3428
  - 2024: 2920
  - 2025: 1472
  - 2026: 1031

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 448 retrieved-with-zero-detections
- days with detections: 2686
- rows: raw 91028 -> kept 91028
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 91028}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 11521
  - 2019: 26264
  - 2020: 8184
  - 2021: 3682
  - 2022: 3360
  - 2023: 14701
  - 2024: 11791
  - 2025: 7658
  - 2026: 3867

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-25 .. 2026-07-31 (8.5 years)
- suggested ~60/40 temporal split: train through 2023-03-05, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

