# Ingest evidence - w119_s-5_e124_n0 (B-05 / gate G1)

Generated: 2026-11-15T09:46:55+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 896 retrieved-with-zero-detections
- days with detections: 2238
- rows: raw 19898 -> kept 19898
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 7531, 'Aqua': 12367}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 2949
  - 2019: 4298
  - 2020: 1644
  - 2021: 1506
  - 2022: 1345
  - 2023: 3499
  - 2024: 1874
  - 2025: 1749
  - 2026: 1034

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 284 retrieved-with-zero-detections
- days with detections: 2850
- rows: raw 90503 -> kept 90503
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 90503}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 12241
  - 2019: 19409
  - 2020: 6975
  - 2021: 5977
  - 2022: 6045
  - 2023: 17195
  - 2024: 8625
  - 2025: 8887
  - 2026: 5149

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-01 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-24, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

