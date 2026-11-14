# EmberLine — limitations (plain language)

Owner: C (task C-07) · date: 14 Nov 2026 · reviewer: A · protocol: PROTO-C01-v0.9

## What this product IS

A historical explorer for satellite fire-hotspot records (NASA FIRMS: MODIS and
VIIRS). It compares the two sensors' records, learns a transparent correction
(harmonization) from years when both observed the same region, shows the result
with uncertainty, and summarizes seasonal patterns on a historical calendar.

## What this product is NOT

- **Not a forecast.** No prediction, no early warning, no alerts, no fire spread.
- **Not safe-to-burn advice.** A "critical window" is a historical percentile of
  activity — never a safety recommendation.
- **Not fire ground truth.** MODIS is our chosen *reference measurement*; VIIRS
  mapped values are *estimates* learned from overlap years.

## Data honesty

- A **hotspot is a satellite observation of a thermal anomaly** — not necessarily
  one physical fire. Detection counts are never reported as fire counts.
- **FRP-sum is an aggregate of sampled radiative-power observations (MW)** —
  not total energy, not burned area, not a fire count.
- **Missing data is not zero.** Failed request ≠ unavailable archive ≠ zero
  detections ≠ verified observation opportunity — four different states, kept
  different everywhere (tooltips, exports, calendar).
- Zero-detection days prove neither "no fire" nor "clear-sky observation".
- 29 February in non-leap years is "not applicable" — never an outage.
- Missing years are never counted as inactive years.

## Scope and era

- Reference: **Aqua MODIS** only; one VIIRS platform (**S-NPP**); Terra and
  NOAA-20/21 are excluded in v1 (recorded deviation DEV-S01).
- Metric: **FRP-sum only** (DEV-S02); the archive era ends **2026-07-31**
  (SP-archive availability); NRT is never blended in.
- The activity index is **AOI-specific** — not comparable across regions.
- Quantile correction is omitted in v1 (DEV-S03); the B2 mapping is a global
  monotone lens, not a per-season/per-region calibration.

## Current build state (honest)

- Implemented and contract-tested (64+29+13+21+30+12+16+10+ manifest tests):
  grid/matching, baselines B0/B1, harmonization B2 + intervals, metrics, splice
  stress tests, calendar/windows, one-command orchestration.
- **Real-data status: the delivered real fixture (Riau, compact window
  2012-01-20..2015-09-15) has too little overlap to fit anything — every
  downstream stage honestly returns `insufficient_data`/`deferred`.** The
  full-era swap-in (2012..2026, both AOIs) is pending data handoff; until then,
  NO real-data metric, calendar or window claim is made — deferred ≠ failed.
- The 80% intervals are a **nominal target calibrated on training residuals**;
  their actual held-out coverage is measured during evaluation, not promised.

## Reproduction

`make reproduce AOI=riau` rebuilds every artifact from immutable inputs
(SHA-256-verified) and writes `artifacts/<aoi>/run_manifest.json` with the full
provenance chain (run ID, git SHA, input hashes, params hash, train/test years,
library versions, seeds). Every displayed number must trace to a run ID.
