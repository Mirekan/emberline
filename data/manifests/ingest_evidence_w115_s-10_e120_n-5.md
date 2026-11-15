# Ingest evidence - w115_s-10_e120_n-5 (B-05 / gate G1)

Generated: 2026-11-15T09:47:02+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1478 retrieved-with-zero-detections
- days with detections: 1656
- rows: raw 12413 -> kept 12413
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 4469, 'Aqua': 7944}
- detections span: 2018-01-02 .. 2026-07-31
- per-year kept rows:
  - 2018: 2256
  - 2019: 3199
  - 2020: 1405
  - 2021: 1127
  - 2022: 761
  - 2023: 1762
  - 2024: 1072
  - 2025: 609
  - 2026: 222

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 935 retrieved-with-zero-detections
- days with detections: 2199
- rows: raw 83130 -> kept 83130
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 83130}
- detections span: 2018-01-01 .. 2026-07-31
- per-year kept rows:
  - 2018: 13629
  - 2019: 19844
  - 2020: 9044
  - 2021: 7150
  - 2022: 4321
  - 2023: 13501
  - 2024: 7434
  - 2025: 6228
  - 2026: 1979

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-02 .. 2026-07-31 (8.6 years)
- suggested ~60/40 temporal split: train through 2023-02-24, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

