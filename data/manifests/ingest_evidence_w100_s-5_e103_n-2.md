# Ingest evidence - w100_s-5_e103_n-2 (B-05 / gate G1)

Generated: 2026-11-15T09:47:15+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 2288 retrieved-with-zero-detections
- days with detections: 846
- rows: raw 4624 -> kept 4624
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'Terra': 1072, 'Aqua': 3552}
- detections span: 2018-01-15 .. 2026-07-31
- per-year kept rows:
  - 2018: 400
  - 2019: 1031
  - 2020: 192
  - 2021: 318
  - 2022: 442
  - 2023: 847
  - 2024: 588
  - 2025: 555
  - 2026: 251

## VIIRS_SNPP_SP

- requested range: 2018-01-01 .. 2026-07-31 (3134 days)
- retrieval: 3134 retrieved / 0 failed / 1307 retrieved-with-zero-detections
- days with detections: 1827
- rows: raw 23142 -> kept 23142
- drops: none
- hash: 627 files checked, 0 mismatch
- satellite: {'N': 23142}
- detections span: 2018-01-07 .. 2026-07-31
- per-year kept rows:
  - 2018: 2162
  - 2019: 4937
  - 2020: 1187
  - 2021: 1238
  - 2022: 3491
  - 2023: 4158
  - 2024: 2352
  - 2025: 2621
  - 2026: 996

## Detection overlap (input for C-01)

- overlap of actual detections: 2018-01-15 .. 2026-07-31 (8.5 years)
- suggested ~60/40 temporal split: train through 2023-03-01, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

