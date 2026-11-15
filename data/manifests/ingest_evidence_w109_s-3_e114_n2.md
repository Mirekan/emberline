# Ingest evidence - w109_s-3_e114_n2 (B-05 / gate G1)

Generated: 2026-11-15T09:46:47+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1634 retrieved-with-zero-detections
- days with detections: 1500
- rows: raw 58424 -> kept 58424
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 13456, 'Aqua': 44968}
- detections span: 2018-01-12 .. 2026-07-31
- per-year kept rows:
  - 2018: 9198
  - 2019: 20017
  - 2020: 1729
  - 2021: 2796
  - 2022: 2126
  - 2023: 10553
  - 2024: 5285
  - 2025: 4464
  - 2026: 2256

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 794 retrieved-with-zero-detections
- days with detections: 2340
- rows: raw 248374 -> kept 248374
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 248374}
- detections span: 2018-01-05 .. 2026-07-31
- per-year kept rows:
  - 2018: 39307
  - 2019: 83790
  - 2020: 11815
  - 2021: 12745
  - 2022: 9753
  - 2023: 38899
  - 2024: 18055
  - 2025: 24351
  - 2026: 9659

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-12 .. 2026-07-31 (8.5 years)
- suggested ~60/40 temporal split: train through 2023-02-28, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

