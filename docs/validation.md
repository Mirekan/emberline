# EmberLine — validation notes (C-05) — REAL G2 RESULTS

Task: C-05 · owner: C · reviewer: A · updated: 14 Nov 2026 ~23:00 WIB ·
protocol: PROTO-C01-v0.9 (FROZEN v1.0) · data: **full era 2012-01-20..2026-07-31, both AOIs**
(held-out = 4,244 days per AOI, identical rows across B0/B1/B2)

## Headline (honest)

**B1 — the training-fitted global ratio — is the accepted harmonization method.**
The proposed B2 monotone log-space mapping **did not improve on held-out data** and is
published as a visible negative result (protocol §6.4 fail action: "use the better honest
baseline; explain where mapping fails"). No held-out row entered any fit, calibration,
normalization or method selection — split and methods were frozen before results (verified
by the leakage detectors in all suites).

## Held-out results (4,244 test days per AOI, 2020-10-09..2026-07-31)

| Metric | AOI | B0 naive | **B1 ratio (accepted)** | B2 mapping |
|---|---|---|---|---|
| mean log-ratio bias | Riau | −0.753 | **−0.558** | −0.776 |
| | Kalteng | −0.869 | **−0.593** | −0.856 |
| log-space R² | Riau | −0.330 | **−0.107** | −0.352 |
| | Kalteng | −0.316 | **+0.037** | −0.288 |
| Wasserstein (MW) | Riau | 10.04 | **5.51** | 8.62 |
| | Kalteng | 35.93 | **8.38** | 27.70 |
| Pearson daily | Riau | 0.560 | 0.560 | 0.558 |
| | Kalteng | 0.758 | 0.758 | 0.756 |
| interval coverage (nominal 0.80) | Riau | n/a | n/a | **0.900** |
| | Kalteng | n/a | n/a | **0.865** |
| calendar-pattern correlation | Riau | — | — | 0.912 |
| | Kalteng | — | — | **0.997** |

Frozen B1 ratios: **0.6609 (Riau)**, **0.5423 (Kalteng)** — fit on training years only.
B2 coefficients (Riau): a≈0.0005, b=0.919, c=0.128, d≈−0.0005; monotone projection none
active; smearing k=1.0014; zero cells entered as exact weights (4.72M day / 4.74M night).

## Splice stress tests (predetermined peaks, ±14 d, continued-MODIS truth)

error_ratio = |error_harmonized| / |error_naive| — **< 1 = artifact reduced**.

| AOI | Method | T1 | T2 | T3 |
|---|---|---|---|---|
| Riau | B2 | 1.007 (worse) | 0.959 | 0.950 |
| **Riau** | **B1 (accepted)** | **0.892** | **0.850** | **0.835** |
| Kalteng | B1 (accepted) | **0.659** | 0.974 | **deferred** — era ends 6 days after the segment peak (2026-07-25), ±14 d window cannot fit; selection rule frozen, not re-picked |

B1 reduces the splice artifact **11–16% (Riau)** and **up to 34% (Kalteng T1)**. The
Kalteng third slot is honestly deferred (2 valid + 1 deferred), with the exact shortfall
recorded — the frozen selection rule was not re-picked after seeing results.

## Machinery verification (synthetic, unchanged)

All contract suites green: 64+29+13+21+30+12+17+11+12 (C-01..C-07) + B ingestion 17/17.
N/A policies, identical-held-out-rows guarantee, leakage detectors and negative-result
labeling verified on synthetic data; real runs now use the same code paths.

## Left-out-of-scope notes

- Kalteng VIIRS rows 345,074 → **344,336 (−0.2%)** on the fresh full-era validation —
  re-fetch campaign, SP archive revision; hashes 0 mismatch; fresh number authoritative.
- Changepoint significance: not implemented (no manufactured p-values).
- One-sided VIIRS rows (94,742 Riau / 80,262 Kalteng) retained in records, excluded from
  fitting per F-6 — their volume is itself a finding (VIIRS sees many small fires MODIS misses).

## For A-04 (G2 decision input)

Everything above traces to run IDs in `artifacts/<aoi>/*.json` + `run_manifest.json`.
Decision requested: accept **B1 as the published method** (protocol fail action) with the
B2 negative result visible in method page and demo.
