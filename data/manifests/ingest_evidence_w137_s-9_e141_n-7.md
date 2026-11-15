# Ingest evidence - w137_s-9_e141_n-7 (B-05 / gate G1)

Generated: 2026-11-14T13:55:40+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 3683 retrieved-with-zero-detections
- days with detections: 1624
- rows: raw 39708 -> kept 39708
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'Aqua': 29356, 'Terra': 10352}
- detections span: 2012-04-03 .. 2026-07-31
- per-year kept rows:
  - 2012: 1777
  - 2013: 1832
  - 2014: 5402
  - 2015: 11285
  - 2016: 1953
  - 2017: 1474
  - 2018: 4265
  - 2019: 3034
  - 2020: 1181
  - 2021: 250
  - 2022: 213
  - 2023: 4814
  - 2024: 840
  - 2025: 176
  - 2026: 1212

## VIIRS_SNPP_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 2924 retrieved-with-zero-detections
- days with detections: 2383
- rows: raw 189047 -> kept 189047
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'N': 189047}
- detections span: 2012-01-24 .. 2026-07-31
- per-year kept rows:
  - 2012: 8251
  - 2013: 8223
  - 2014: 27941
  - 2015: 51640
  - 2016: 9607
  - 2017: 6287
  - 2018: 21596
  - 2019: 15770
  - 2020: 6237
  - 2021: 1297
  - 2022: 989
  - 2023: 22336
  - 2024: 3578
  - 2025: 663
  - 2026: 4632

## Detection overlap (input for C-01)

- overlap of actual detections: 2012-04-03 .. 2026-07-31 (14.3 years)
- suggested ~60/40 temporal split: train through 2020-11-06, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

