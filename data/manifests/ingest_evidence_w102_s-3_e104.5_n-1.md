# Ingest evidence - w102_s-3_e104.5_n-1 (B-05 / gate G1)

Generated: 2026-11-15T09:46:35+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 3421 retrieved-with-zero-detections
- days with detections: 1886
- rows: raw 45835 -> kept 45835
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'Aqua': 28482, 'Terra': 17353}
- detections span: 2012-01-20 .. 2026-07-31
- per-year kept rows:
  - 2012: 6489
  - 2013: 2464
  - 2014: 3940
  - 2015: 18068
  - 2016: 423
  - 2017: 321
  - 2018: 529
  - 2019: 9816
  - 2020: 174
  - 2021: 271
  - 2022: 215
  - 2023: 1283
  - 2024: 957
  - 2025: 595
  - 2026: 290

## VIIRS_SNPP_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 1325 retrieved-with-zero-detections
- days with detections: 3982
- rows: raw 206914 -> kept 206914
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'N': 206914}
- detections span: 2012-01-20 .. 2026-07-31
- per-year kept rows:
  - 2012: 24092
  - 2013: 10174
  - 2014: 17069
  - 2015: 85529
  - 2016: 1975
  - 2017: 1596
  - 2018: 2913
  - 2019: 45766
  - 2020: 1399
  - 2021: 1330
  - 2022: 1453
  - 2023: 6499
  - 2024: 3996
  - 2025: 2029
  - 2026: 1094

## Detection overlap (input for C-01)

- overlap of actual detections: 2012-01-20 .. 2026-07-31 (14.5 years)
- suggested ~60/40 temporal split: train through 2020-10-08, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

