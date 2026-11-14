# Ingest evidence - w103_s-5_e106_n-2 (B-05 / gate G1)

Generated: 2026-11-14T13:55:33+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 2656 retrieved-with-zero-detections
- days with detections: 2651
- rows: raw 88124 -> kept 88124
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'Terra': 32911, 'Aqua': 55213}
- detections span: 2012-01-21 .. 2026-07-31
- per-year kept rows:
  - 2012: 11810
  - 2013: 2922
  - 2014: 13208
  - 2015: 31789
  - 2016: 990
  - 2017: 1059
  - 2018: 1877
  - 2019: 11296
  - 2020: 579
  - 2021: 879
  - 2022: 521
  - 2023: 7497
  - 2024: 1786
  - 2025: 1065
  - 2026: 846

## VIIRS_SNPP_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 971 retrieved-with-zero-detections
- days with detections: 4336
- rows: raw 400735 -> kept 400735
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'N': 400735}
- detections span: 2012-01-21 .. 2026-07-31
- per-year kept rows:
  - 2012: 47234
  - 2013: 11922
  - 2014: 60362
  - 2015: 155800
  - 2016: 4280
  - 2017: 4102
  - 2018: 8490
  - 2019: 52481
  - 2020: 2732
  - 2021: 3550
  - 2022: 2303
  - 2023: 35002
  - 2024: 6474
  - 2025: 3519
  - 2026: 2484

## Detection overlap (input for C-01)

- overlap of actual detections: 2012-01-21 .. 2026-07-31 (14.5 years)
- suggested ~60/40 temporal split: train through 2020-10-08, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

