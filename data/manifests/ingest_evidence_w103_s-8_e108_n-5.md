# Ingest evidence - w103_s-8_e108_n-5 (B-05 / gate G1)

Generated: 2026-11-15T09:47:07+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1883 retrieved-with-zero-detections
- days with detections: 1251
- rows: raw 5160 -> kept 5160
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 2957, 'Aqua': 2203}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 1007
  - 2019: 1065
  - 2020: 401
  - 2021: 427
  - 2022: 416
  - 2023: 915
  - 2024: 513
  - 2025: 276
  - 2026: 140

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 895 retrieved-with-zero-detections
- days with detections: 2239
- rows: raw 24073 -> kept 24073
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 24073}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 4794
  - 2019: 5932
  - 2020: 1552
  - 2021: 1807
  - 2022: 1351
  - 2023: 4357
  - 2024: 2360
  - 2025: 1077
  - 2026: 843

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-01 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-24, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

