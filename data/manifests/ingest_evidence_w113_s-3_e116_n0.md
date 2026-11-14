# Ingest evidence - w113_s-3_e116_n0 (B-05 / gate G1)

Generated: 2026-11-14T05:43:09+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 3113 retrieved-with-zero-detections
- days with detections: 2194
- rows: raw 72811 -> kept 72811
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'Terra': 27933, 'Aqua': 44878}
- detections span: 2012-01-20 .. 2026-07-31
- per-year kept rows:
  - 2012: 5553
  - 2013: 4056
  - 2014: 12309
  - 2015: 25103
  - 2016: 682
  - 2017: 536
  - 2018: 2594
  - 2019: 12271
  - 2020: 792
  - 2021: 457
  - 2022: 334
  - 2023: 5310
  - 2024: 1336
  - 2025: 837
  - 2026: 641

## VIIRS_SNPP_SP

- requested range: 2012-01-20 .. 2026-07-31 (5307 days)
- retrieval: 5307 retrieved / 0 failed / 1345 retrieved-with-zero-detections
- days with detections: 3962
- rows: raw 345074 -> kept 345074
- drops: none
- hash: 1062 files checked, 0 mismatch
- satellite: {'N': 345074}
- detections span: 2012-01-20 .. 2026-07-31
- per-year kept rows:
  - 2012: 25081
  - 2013: 15839
  - 2014: 56906
  - 2015: 123957
  - 2016: 3876
  - 2017: 3414
  - 2018: 11847
  - 2019: 59506
  - 2020: 3946
  - 2021: 2351
  - 2022: 1881
  - 2023: 23933
  - 2024: 5506
  - 2025: 4443
  - 2026: 2588

## Detection overlap (input for C-01)

- overlap of actual detections: 2012-01-20 .. 2026-07-31 (14.5 years)
- suggested ~60/40 temporal split: train through 2020-10-08, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

