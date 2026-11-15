# Ingest evidence - w107_s-8_e112_n-3 (B-05 / gate G1)

Generated: 2026-11-15T09:47:13+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1632 retrieved-with-zero-detections
- days with detections: 1502
- rows: raw 8596 -> kept 8596
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 5076, 'Aqua': 3520}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 1149
  - 2019: 2100
  - 2020: 531
  - 2021: 657
  - 2022: 477
  - 2023: 1785
  - 2024: 991
  - 2025: 495
  - 2026: 411

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 595 retrieved-with-zero-detections
- days with detections: 2539
- rows: raw 52838 -> kept 52838
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 52838}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 6898
  - 2019: 14631
  - 2020: 3510
  - 2021: 3350
  - 2022: 2032
  - 2023: 11295
  - 2024: 5888
  - 2025: 2697
  - 2026: 2537

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-01 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-24, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

