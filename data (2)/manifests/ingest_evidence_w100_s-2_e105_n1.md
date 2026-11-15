# Ingest evidence - w100_s-2_e105_n1 (B-05 / gate G1)

Generated: 2026-11-14T03:31:45+00:00 by pipeline/validate.py

## MODIS_SP

- requested range: 2012-01-20 .. 2015-09-15 (1335 days)
- retrieval: 645 retrieved / 0 failed / 645 retrieved-with-zero-detections
- days with detections: 451
- rows: raw 26917 -> kept 26917
- drops: none
- hash: 129 files checked, 0 mismatch
- satellite: {'Terra': 10250, 'Aqua': 16667}
- detections span: 2012-01-20 .. 2015-09-15
- per-year kept rows:
  - 2012: 10809
  - 2013: 10354
  - 2015: 5754

## VIIRS_SNPP_SP

- requested range: 2015-09-01 .. 2015-09-15 (15 days)
- retrieval: 15 retrieved / 0 failed / 15 retrieved-with-zero-detections
- days with detections: 15
- rows: raw 26420 -> kept 26420
- drops: none
- hash: 3 files checked, 0 mismatch
- satellite: {'N': 26420}
- detections span: 2015-09-01 .. 2015-09-15
- per-year kept rows:
  - 2015: 26420

## Detection overlap (input for C-01)

- overlap of actual detections: 2015-09-01 .. 2015-09-15 (0.0 years)
- suggested ~60/40 temporal split: train through 2015-09-09, test after (C decides; freeze before fitting)

## Missingness notes (read before using these numbers)

- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.
- `days_zero_detections` means FIRMS returned a successful response with zero rows.
- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.
- A detection is a hotspot observation, not necessarily a fire (plan section 0).

