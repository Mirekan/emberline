# Ingest evidence - w100_s-2_e105_n1 (B-05 / gate G1)

Generated: 2026-11-15T03:55:23+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 2303 retrieved-with-zero-detections
- days with detections: 3004
- rows: raw 83318 -> kept 83318
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'Terra': 35023, 'Aqua': 48295}
- detections span: 2012-01-20 .. 2026-07-31
- per-year kept rows:
  - 2012: 10809
  - 2013: 10495
  - 2014: 14385
  - 2015: 20135
  - 2016: 2086
  - 2017: 1464
  - 2018: 2051
  - 2019: 13781
  - 2020: 1316
  - 2021: 1267
  - 2022: 853
  - 2023: 1610
  - 2024: 1412
  - 2025: 1110
  - 2026: 544

## VIIRS_SNPP_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 923 retrieved-with-zero-detections
- days with detections: 4384
- rows: raw 346804 -> kept 346804
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'N': 346804}
- detections span: 2012-01-20 .. 2026-07-31
- per-year kept rows:
  - 2012: 40219
  - 2013: 44319
  - 2014: 67205
  - 2015: 92539
  - 2016: 6264
  - 2017: 4202
  - 2018: 7556
  - 2019: 59568
  - 2020: 3398
  - 2021: 2566
  - 2022: 2651
  - 2023: 5324
  - 2024: 4203
  - 2025: 4263
  - 2026: 2527

## Detection overlap (input for C-01)

- overlap of actual detections: 2012-01-20 .. 2026-07-31 (14.5 years)
- suggested ~60/40 temporal split: train through 2020-10-08, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

