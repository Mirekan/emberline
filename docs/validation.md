# EmberLine — validation notes (C-05)

Task: C-05 · owner: C · reviewer: A · date: 14 Nov 2026 (~15:00 WIB) ·
protocol: PROTO-C01-v0.9 · status: **machinery verified, real-era evaluation DEFERRED**

## What is implemented (verified by contract tests)

| Component | Artifact | Verified by |
|---|---|---|
| 12-metric held-out menu (log-ratio bias, sMAPE, MAPE, Pearson/Spearman daily+weekly, log-R², KS, Wasserstein, calendar-pattern correlation, interval coverage) | `artifacts/<aoi>/harmonization_metrics.json` | `tests/test_metrics.py` 30/30 |
| Identical-held-out-rows guarantee across B0/B1/B2 (hard-fails on any disagreement) | evaluated in-run | `test_metrics.py` |
| Leave-one-year-out summary (training-internal refits via `fit_b2_rows`) | `harmonization_metrics.json → leave_one_year_out` | `test_metrics.py` |
| ≥3 predetermined splice stress tests (peak-of-segment rule, ±14 d, ≥70% retrieval) vs continued-MODIS truth | `artifacts/<aoi>/splice_stress_test.json` | `tests/test_splice_stress.py` 12/12 |
| Negative results stay visible (error_ratio ≥ 1 → "NEGATIVE RESULT" label) | stress manifest | `test_splice_stress.py` |
| No manufactured p-values (changepoint significance = not_implemented) | both manifests | `test_splice_stress.py` |

Key metric-design fact surfaced by the tests: the shift statistic is a WITHIN-series
log-difference, so a constant multiplicative error cancels — an artifact appears only
when the sensor error *changes* at the pseudo-transition. The synthetic scenario
therefore oscillates the error at each segment boundary (this is machinery testing,
not a physical claim).

## N/A policies (F-15) — enforced in code

- Zero denominators (sMAPE both-zero rows, zero fold ratio) → excluded **and counted**, never ∞.
- Constant series / empty groups / <2 points / <6 months → `N/A:<reason>`.
- Constant-series variance guard uses a 1e-12 tolerance (identical floats have ~1e-32 variance, not exact 0).
- Zero-actual MAPE rows excluded with counts; sample sizes travel with every result.

## Honest status for the real fixture

The delivered Riau fixture (2012-01-20..2015-09-15, VIIRS from 2015-09-01) contains
**no held-out era days** (test era starts 2020-10-09), so for real data:

- `harmonization_metrics.json` → status `deferred` (upstream artifacts absent),
- `splice_stress_test.json` → status `deferred` — **deferred ≠ failed**: machinery is
  verified on synthetic data; the real evaluation lands with the full-era swap-in
  (2012..2026, both AOIs). No metric is claimed on real data in this state.

## What the real evaluation will run (unchanged rules)

1. `python3 -m pipeline.baselines --pairs <matched_pairs.csv> --aoi-id <aoi>`
2. `python3 -m pipeline.harmonize --pairs <matched_pairs.csv> --aoi-id <aoi>`
3. `python3 -m pipeline.metrics --baselines … --harmonized … --pairs … --aoi-id <aoi>`
4. `python3 -m pipeline.splice_stress --baselines … --harmonized … --aoi-id <aoi>`

G2 evidence for A = both real-data manifests + this document + the C-03/C-04/C-05
contract tests (13/13, 21/21, 30/30, 12/12). No held-out row entered any fit,
calibration, normalization or method selection (enforced by construction and
verified by the leakage detectors in each test suite).

## Handoff

- To A (G2/A-04): this document + the two real-data manifests when the full era lands.
- To C-06: accepted series + interval semantics (coverage measured at C-05, not promised).
- To E: comparison chart values from `harmonized_daily.csv` / `baseline_series.csv` (lo/est/hi, B0/B1/B2).
- To F: validated claims and failures — say "harmonization reduces the splice artifact
  by X on held-out years" ONLY from `error_ratio` values in the real-data stress manifest.
