# EmberLine C-01 — Frozen Scientific Protocol
## Harmonization, Evaluation, Calendar & Windows

| | |
|---|---|
| **Protocol ID** | `PROTO-C01-v0.9` (frozen identifier — run IDs reference this string) |
| **Status** | **`FROZEN v1.0`** — signed off by B/D/E 14 Nov 2026 ~16:10 WIB (owner=reviewer same human, disclosed in DECISIONS.md). Changes now require a version bump + re-review. |
| **Owner / Reviewer** | Team member C / Team member B (per TEAM_TASKS.csv C-01) |
| **Created** | 14 Nov 2026 ~10:30 WIB (event day 1; team actual start 09:00 WIB — see DEC-4) |
| **Companion configs** | `config/grid.yaml`, `config/params.yaml` (machine-readable contract) |
| **Contract test** | `python tests/test_protocol_contract.py` (also pytest-compatible) |

**How to read this document**

- `F-n` = **frozen decision**. Changing one after fitting requires a protocol version bump (`v1.x`), a DECISIONS.md entry, re-run of affected artifacts, and reviewer sign-off. Changing one *after seeing held-out test results* is forbidden.
- `DEC-n` = **decision-needed marker**: an explicit unresolved input this protocol does not silently guess. DEC items are resolved *before* fitting, never after.
- `DEV-n` = **scope deviation** from the original PRD that requires A-02 approval and must appear in DECISIONS.md and the submission.

---

## 1. What EmberLine claims, and never claims

- A hotspot is a **satellite observation of a thermal anomaly** — not necessarily one physical fire. Detection counts are never converted into fire counts.
- **Harmonization is a learned measurement mapping**: translating VIIRS observations onto the scale of a chosen MODIS reference, using years when both instruments observed the same region. It is an *estimate with uncertainty*, not ground truth.
- MODIS here is a **reference measurement scale**, not physical-fire ground truth.
- FRP-sum is an **aggregate of sampled radiative-power observations** — not total daily energy, not burned area, not a fire count.
- Every calendar/window output is **historical and descriptive, not predictive**. No output is a "safe to burn" recommendation, forecast, alert, or early warning.

---

## 2. Frozen decisions

### 2.1 Sensors, platforms, units

**F-1 Reference sensor: Aqua MODIS.**
One fixed reference for all harmonization. Rationale: (a) a calibration needs exactly one reference — pooling two references makes sensor-difference and drift unidentifiable; (b) published analyses document long-term degradation/crosstalk artifacts in Terra MODIS fire bands (21/22) over its mission, while Aqua's fire bands are comparatively stable; (c) Terra (~10:30/22:30 equator crossings) and Aqua (~13:30/01:30) also sample *different times of day*, so mixing platforms would change instrument bias and daily sampling pattern simultaneously. Terra gets its own separate validated treatment later (optional O-05), never a silent ride-along.
Exact FIRMS source string pending the B-01 keyed availability probe → **DEC-1**.

**F-2 VIIRS platform: S-NPP (Suomi National Polar-orbiting Partnership), PROVISIONAL.**
S-NPP has the longest VIIRS archive (expected from ~2012, unverified until B-01 probes keyed coverage) → maximum overlap years for fitting. NOAA-20/NOAA-21 are excluded in v1. If B-01 shows S-NPP archive is unusable, the platform decision returns to A for explicit re-approval — **no silent substitute** (DEC-1).

**F-3 Metric: FRP-sum only (DEV-S02).**
FRP is Fire Radiative Power in **megawatts (MW)** — an instantaneous rate measured by both sensors. The harmonization target and headline activity metric is the **daily AOI FRP-sum per day/night class**. Detection count is aggregated separately, may be displayed as its own series, and is **never merged across sensors, never labeled a fire count, never used as a harmonization target**. FRP-sum is an aggregate of sampled observations (overpass times, cloud gaps), not total energy or burned area — this label is mandatory wherever FRP-sum appears (UI, exports, deck).

### 2.2 Grid and time

**F-4 Grid: 0.1° cells, centroid assignment.**
Cell of a detection = the 0.1° cell containing the detection's reported centroid (no coordinate rounding). Cells are half-open `[west, east) × [south, north)`. AOI clipping keeps cells whose centroid lies inside the bbox. Bbox cap 5°×5°; antimeridian-crossing boxes rejected with an explicit message. Unequal physical cell area (shrinks ~cos latitude) is **not corrected in v1** — documented limitation, never silently adjusted.

**F-5 Time: UTC daily bins; day/night preserved.**
A detection's day = UTC calendar day from source `acq_date` + zero-padded `acq_time` (timezone-aware UTC; invalid times rejected). No local-time conversion anywhere in the pipeline. The `daynight` flag is preserved and all aggregation splits by **overpass class = (source, platform, day/night)**. Implication recorded for E: a "UTC day" is not a local midnight-to-midnight day; seasonal (month/day) patterns are unaffected.

### 2.3 Pairing, duplicates, missingness

**F-6 Pairing unit: (0.1° cell, UTC day, day/night class), per-sensor aggregates.**
Each unit carries, **separately per sensor**: detection count, FRP-sum, FRP-max, mean scan (where provided), plus platform/version/confidence fields. A **matched pair** = both sensors returned a (possibly zero-detection) retrieval for the same unit. One-sided returned signal (only one sensor has detections in a retrieved unit) is **retained** in that sensor's series with a `one_sided` flag — it is excluded from ratio/mapping *fitting* but never deleted from the record.

**F-7 True duplicates: exact-row identity per source-specific key.**
Key = (source, satellite, processing version, acq_date, acq_time, latitude, longitude, daynight) with **exact values as provided — never rounded** to create matches. Nearby detections from different overpasses/sensors/platforms are legitimate independent observations and are **never** deduplicated. Overlapping SP/NRT versions are resolved explicitly, never blended.

**F-8 Confidence filters (defaults; changes = protocol amendment).**
MODIS: keep `confidence >= 30` (nominal + high). VIIRS: keep nominal + high, exclude low. Unknown confidence values are **excluded and counted**, never silently promoted to nominal. Original confidence values survive in all processed artifacts.

**F-9 Missingness is not zero — four states, always distinguishable:**
1. **Failed request** (timeout/error/invalid): retrieval unknown; bounded retries, then reported as a gap.
2. **Unavailable archive**: verified availability evidence excludes the period.
3. **Successful query, zero detections**: valid empty response under the query/filter — not proof of no fire, not proof of observation opportunity.
4. **Verified observation opportunity**: only with independent coverage evidence.
Never zero-fill failures or unavailable periods. Retrieval masks and drop counts travel with every artifact, tooltip, and export. A detection-only CSV cannot establish clear-sky observation opportunity or fire absence.

**F-9b Minimum support (PROVISIONAL numbers — DEC-2, frozen *before* fitting, never after seeing test results):**
- Training-year eligible: ≥ 90% of the year's days have paired retrievals **and** ≥ 10 distinct days with MODIS FRP-sum > 0 in the AOI.
- Test-year eligible: the coverage condition (≥ 90% paired retrieval days). Its signal condition decides which *metrics* are computable, not whether the year is excluded.
- AOI is analyzable only with ≥ 2 eligible training years **and** ≥ 1 eligible test year; otherwise the AOI returns an explicit `insufficient_data` result — never a transferred model with unverified validity.

### 2.4 Split and the training-only law

**F-10 Temporal split, frozen before fitting.**
Contiguous **earliest ~60% of eligible overlap years → training**; remaining years → **final held-out test**. No shuffling; no year moves between sets after any model result is seen. If total eligible overlap years ≤ 3: use leave-one-year-out CV **within training** for method selection and disclose the degenerate final test explicitly.

**F-11 Training-only law.**
Every learned step — B1 ratio, B2 coefficients, smearing factor, interval calibration, covariate/feature choices, method selection, normalization constants, imputation, any threshold tuning — is fit on **training years or training-internal folds only**. Held-out years are never used for fitting, calibration, normalization, selection, or tuning. A leakage finding invalidates the metric run; refit from training only.

### 2.5 Methods (all evaluated on the identical held-out rows)

**F-12 Method definitions.**
- **B0 — naive splice:** observed MODIS reference before the supported VIIRS era; raw uncorrected VIIRS after. No correction. This is "the problem as-is".
- **B1 — training-fitted global ratio:** `r = Σ_training S_modis / Σ_training S_viirs` over matched retrieved cell-days; prediction `Ŝ = r · S_viirs`. One multiplicative constant.
- **B2 — primary harmonization (monotone, interpretable, log-space):**
  `log1p(S_modis) = a + b·log1p(S_viirs) + c·log1p(1 + n_viirs) + d·I_night`
  fit on training matched cell-days with **monotonicity constraints b ≥ 0, c ≥ 0** (a busier day can never map to a calmer estimate). Prediction per cell-day: `Ŝ = k · expm1(ŷ)`, with the back-transform bias factor `k` (Duan smearing on training residuals) computed **training-only**. `n_viirs` = VIIRS detection count in the same cell-day. Zero inflation, if needed, is handled explicitly as detection-probability-first, conditional-magnitude-second.
  - If training-internal folds show B2 unstable → pre-registered fallback **B2-simple** (log-ratio-only, no count covariate). Selection between variants uses **training folds only**.
  - **Quantile correction: omitted in v1** (DEV-S03). If ever added, it is training-only. A complex challenger is dropped before validation is weakened.
- Every method consumes **the same final held-out rows, same units, same AOI coverage**. No method-specific test subsets. First-run baseline values are recorded as observations — never as pre-invented targets, never used to select favorable AOIs or re-split.

### 2.6 Uncertainty

**F-13 Intervals calibrated where they are published.**
Nominal **80%** target, calibrated at the level it is shown: **AOI-daily**, from training residuals via day-level block bootstrap (preserves within-day spatial dependence). **Summing per-cell quantile bounds and calling the result an AOI interval is forbidden.** Bounds are finite, ordered (lo ≤ estimate ≤ hi), nonnegative. Inputs outside the training 1st–99th percentile get an explicit `extrapolation` flag. Actual held-out coverage is **measured and reported**; 80% is a target to verify, not a promise. If intervals cannot be calibrated honestly, publish the point estimate with an explicit unavailability statement — never a decorative band.

### 2.7 Published source policy

**F-14 One honest series, explicit about its origin.**
- Before the supported VIIRS era → **observed Aqua reference**.
- Within the validated VIIRS era → **mapped VIIRS estimate** + interval + source/run flags.
- During overlap → the separate **observed-MODIS comparison** series is also retained.
- Everything else → **explicit gap** with a reason.
Never average the sensors, never switch sources day-by-day to hide missingness, never blend. No Terra-era or worldwide coverage claims from an Aqua-only model.

### 2.8 Evaluation

**F-15 Metrics, all on identical held-out rows, each with sample size + missing counts + N/A policy.**
`mean log-ratio bias` · `sMAPE` (primary scale metric) · `MAPE` (zero-actual rows excluded, exclusion counted) · `Pearson & Spearman` at daily **and** weekly resolution · `log-space R²` · `KS statistic` · `Wasserstein distance` · `calendar-pattern correlation` (climatology agreement) · `empirical interval coverage`.
N/A policy: zero denominators, constant series, empty groups, zero support → `N/A:<reason>`, **never ∞, never a fabricated zero**. Daily vs weekly primary is pre-registered: daily primary if ≥ 60% of test days are paired-retrieved **and** ≥ 10 nonzero-signal days, else weekly primary — the rule is support-based, decided before results are seen. Leave-one-year-out summary is training-internal and mandatory. MODIS is the reference measurement, not truth; naive vs harmonized shifts are compared against the continued-MODIS series.

**F-16 Splice stress tests: ≥ 3 predetermined pseudo-transitions per sufficiently covered AOI.**
Selection rule (fixed now, no peeking): `T_i` = the peak-MODIS-FRP-sum day within each of 3 equal segments of the eligible held-out span. Requirements: the ±14-day window is fully inside held-out coverage with ≥ 70% paired retrieval on both sides. Each test compares: (A) MODIS-before + **raw** VIIRS-after (naive splice), (B) MODIS-before + **harmonized** VIIRS-after, (C) continued MODIS throughout (**truth reference**). Report `shift_naive`, `shift_harmonized`, `shift − truth`, and error ratio. Invalid/too-short windows are reported **failed/deferred** with the exact coverage shortfall. Changepoint significance is reported only with a pre-stated, dependence-aware valid procedure; otherwise that component is marked **not implemented** — no manufactured p-values. Unfavorable AOIs and negative B2 results stay visible in artifacts, method view, and the deck.

### 2.9 Activity index, calendar, windows

**F-17 Activity index.**
`idx(day) = log1p(harmonized AOI FRP-sum) / log1p(P95 of training-period daily reference-MODIS FRP-sum)`.
Denominator is frozen from training, positive by construction; if it is ≤ 0 or undefined, the index is **unavailable** and raw MW units are shown. The index is AOI-specific and **not automatically comparable across regions** — stated in UI and exports. Uncertainty bounds get the same monotone transform. Extremes are never clipped away.

**F-18 Calendar and critical windows.**
- Fixed **366-position month/day template**; true calendar dates preserved in exports; non-leap Feb 29 = `not_applicable`, never a data outage; year boundaries and ISO week 53 tested.
- Climatology: median + IQR (10th/90th optional) with **circular ±7-day smoothing** across the day-of-year seam.
- Critical windows: contiguous runs ≥ 3 days where the smoothed climatology curve ≥ its own **75th percentile** (configurable) — a descriptive seasonal threshold, **not a safety threshold**; December–January wrapping windows supported; every window publishes its `years_active` and `years_eligible` denominators.
- `years_eligible` = years with ≥ 60% valid (non-missing) positions. `years_active` = smoothed index exceeds the window threshold on ≥ 3 days (PROVISIONAL — DEC-3). Missing years are **never** counted as inactive; sparse records are labeled `insufficient`, never "normal".
- Weekly/monthly rollups must reconcile with the daily series.

### 2.10 Reproducibility

**F-19 Run identity and provenance.**
Every artifact carries a `run_id` plus: git SHA, created UTC, AOI/bbox/date range, sources, SHA-256 input hashes, params hash, train/test years, metrics path, library versions, deterministic seeds. One-command reproduction target (`make reproduce AOI=<id>`). No FIRMS MAP_KEY or any credential in code, configs, logs, manifests, screenshots, or docs — credentials are human-managed secrets.

---

## 3. Simplifications — methodology and analogies

These are pre-scoped simplifications (plan §2.5) **requiring A-02 approval**; they are recorded here because C-01 encodes them. Approval status lives in DECISIONS.md.

> **Caveat:** analogies are for orientation — the frozen definitions in §2 are the actual contract. An analogy that overclaims is worse than none.

### S-01 — Aqua MODIS + one VIIRS platform (S-NPP) only

**Methodology.** Calibration requires one fixed reference and one target. Terra and Aqua carry the same instrument *design* but different degradation trajectories (documented Terra fire-band crosstalk) *and* different overpass times (~10:30/22:30 vs ~13:30/01:30 equator crossings), so pooling them changes instrument bias and daily sampling simultaneously — two confounds that cannot be separated on hackathon-scale data. S-NPP is chosen as the single VIIRS target because it has the longest archive, i.e., the most overlap years to fit and validate on.

**What it costs.** No claim about the Terra era (mid-2002 onward only, and only as far as B-01's verified archive reaches); no multi-platform coverage claim. Extending to Terra/other VIIRS platforms is optional O-05 with its own overlap calibration and duplicate handling — never a free relabeling.

**Analogy — the lab thermometer.** When a lab adopts a new thermometer model, you validate it against **one trusted reference** in the same water bath. You don't validate it against an average of the trusted one *and* a third, slightly drifting thermometer — any disagreement would be unexplainable: sensor design, drift, or the third unit? Terra is that third thermometer. It may be perfectly usable — but it gets its own experiment (O-05), not a silent ride-along in the first calibration.

### S-02 — FRP-sum as the only activity metric

**Methodology.** MODIS detects at ~1 km resolution; VIIRS at ~375 m. VIIRS therefore records *more detections of smaller/hotter fires* — count differences are instrument artifacts, not fire physics, so a count ratio is not a physical quantity and count-based "correction" would calibrate the cameras, not the fires. FRP (MW) is a physical rate both instruments measure for the same underlying fires; the daily AOI FRP-sum is the closest comparable aggregate. It remains *sampling-dependent* (overpass schedule, clouds) — hence the mandatory "aggregate of sampled observations" label, never "total energy" or burned area.

**What it costs.** One headline number; no metric selector in v1 (original requirement interpreted as needing one is **deferred and recorded**, not called complete). Day/night distinction preserved because overpass and background conditions differ.

**Analogy — rain gauges.** A wide-mouth gauge catches more raindrops than a narrow one: the *drop count* describes the gauge, not the rain. *Millimetres of accumulation* is the comparable quantity. FRP-sum is our millimetres; detection count is our drop count — shown separately, never merged into a "number of fires".

### S-03 — Interpretable monotone log-space mapping (B2) + mandatory baselines

**Methodology.** Fire data is nonnegative, zero-inflated, and spans orders of magnitude — log space stabilizes variance and `log1p` keeps true zeros working. The **monotonicity constraint** (b, c ≥ 0) preserves physical ordering: a day with more observed signal can never map to a calmer estimate. Three-to-five parameters keep the fit honest on short overlap — a flexible black box would overfit and couldn't be audited in two days. B0 (naive splice) and B1 (one ratio) are **mandatory comparators**: any claim that B2 helps must beat them on the *same* held-out years, or the honest baseline is published instead.

**What it costs.** B2 is a global lens, not a per-season or per-region calibration; quantile correction is omitted in v1 (DEV-S03). If B2 loses, we publish that.

**Analogy — the eyeglasses prescription.** Harmonization is a **prescription for the satellite's eyesight**, ground from the years when both instruments looked at the same fires. B0 is walking around with no glasses (the raw blur). B1 is off-the-rack single-strength reading glasses from the pharmacy. B2 is a proper prescription — still just ground lenses (transparent, monotone), not surgery (no black box). And the held-out years are the eye exam the optician **didn't study for**: if the prescription fails that exam, we say so.

### S-04 / S-05 / S-06 — acknowledged, owned elsewhere

| | Decision | C's involvement |
|---|---|---|
| S-04 | Bounded custom rectangles; genuine recomputation only for supported cached areas; explicit `unsupported`/`insufficient_data` otherwise | C supplies the per-AOI support/eligibility rules (F-9b); D enforces; C reviews artifacts carry correct AOI IDs/bbox/run IDs |
| S-05 | One app, one backend, precomputed versioned artifacts; no DB/auth/queue/runtime-LLM | C produces the versioned artifacts that architecture serves |
| S-06 | Provenance as ordinary CSV columns (no leading comment headers) | C defines required provenance fields (F-19, §7-D); deviation recorded for FR-EXP-1 |

---

## 4. Evaluation run order (leakage-guarded)

1. Freeze protocol (this document) → sign-off B/D/E → A records scope decisions.
2. Ingest B-05 real overlap evidence; resolve **DEC-1/DEC-2**; re-freeze support numbers if needed *before* fitting.
3. C-02 matched aggregates (per-sensor, day/night, retrieval masks).
4. C-03 B0/B1 on frozen split → record first-run values as observations.
5. C-04 B2 (+ smearing, intervals) — training only.
6. C-05 held-out metrics + ≥3 stress tests/AOI + LOYO → **G2 evidence to A**.
7. C-06 index/calendar/windows from *accepted* C-05 series.
8. C-07 manifest + method/validation/limitations docs → handoff to A/D/E/F.

Any protocol change after step 4 = version bump + reviewer sign-off + affected artifacts re-run.

---

## 5. Scope deviations recorded here (A-02 approval required)

| ID | Deviation | Affected requirements |
|---|---|---|
| DEV-S01 | Aqua + one VIIRS platform only; Terra & NOAA-20/21 excluded in v1 | FR-DATA-6, FR-HARM-8 (deferred to O-05) |
| DEV-S02 | FRP-sum only; metric selector deferred | FR-HARM-1 (metric-selector component recorded as deferred) |
| DEV-S03 | Monotone log-space mapping; quantile correction omitted in v1 | FR-HARM-3 (with documented deviation) |
| DEV-S06 | CSV provenance as ordinary columns, not comment headers | FR-EXP-1 |

---

## 6. Unresolved assumptions — decision-needed markers

| ID | Needs | Resolves |
|---|---|---|
| **DEC-1** | B-01 keyed availability probe | Exact FIRMS source strings; earliest/latest archive dates; S-NPP platform confirmation |
| **DEC-2** | B-05 overlap evidence | Minimum-support numbers (F-9b) — frozen **before** fitting; any later change = version bump + re-review |
| **DEC-3** | Coverage review at C-06 | `years_active` definition (currently ≥3 threshold-exceeding days) |
| **DEC-4** | A records re-baseline | Team actual start 09:00 WIB 14 Nov; proposed re-baselined G2 ≈ H22–H23; G3 (freeze) stays H30; deadline unchanged |
| **DEC-5** | A-01 confirmation | Deadline timezone & official brief — affects claims language only, never the science math |

---

## 7. Handoffs enabled by this protocol

- **To B:** units (MW), UTC-bin + day/night semantics, exact dedupe keys (F-7), confidence thresholds (F-8), and the required mask columns: retrieval status (4 states, F-9), `one_sided` flags, drop counts.
- **To D:** payload contract inputs — per-sensor raw values, harmonized estimate + interval + `source_flag`, `run_id`/model version, train/test years, statuses incl. `insufficient_data`, gap/coverage reasons, index + window fields + denominators, error schema.
- **To E:** legend vocabulary (raw / naive / corrected / reference; gap vs zero vs high-uncertainty vs Feb-29-N/A), index meaning + non-comparability caveat, mandatory "historical/descriptive, not predictive" wording, glossary lines for FRP/harmonization/baseline.
- **To A:** this protocol as the scope record; deviations (§5) for DECISIONS.md; gate evidence contracts (§4).

**Handoff note (C-01):** Task C-01; owner C; reviewer B; deliverable `docs/method.md` + `config/grid.yaml` + `config/params.yaml` + `tests/test_protocol_contract.py`; evidence = passing contract test + sign-off row below; limitations = DEC-1/2/3 provisional inputs; next dependency = B-05 real overlap evidence for C-02.

---

## 8. Sign-off (required before any fitting)

- [x] **B** — units, matching, source-limit rules agree with ingestable reality — signed 14 Nov 2026 ~16:10 WIB (owner=reviewer same human, disclosed)
- [x] **D** — payload fields, status/null semantics implementable as written — signed 14 Nov 2026 ~16:10 WIB (owner=reviewer same human, disclosed)
- [x] **E** — labels, legends, calendar meanings renderable as written — signed 14 Nov 2026 ~16:10 WIB (owner=reviewer same human, disclosed)
- [x] **A** — scope decisions + deviations recorded in DECISIONS.md (DEV-S01..S06, DEC-1..4, AOI-PRESETS, INT-1/2 — all APPROVED 14 Nov)

*Signed versions are recorded with timestamp + reviewer name in the CSV evidence column and in DECISIONS.md. The protocol identifier stays `PROTO-C01-v0.9`; the frozen status is v1.0. Real-data fitting is now authorized — the compact Riau fixture still returns insufficient_data honestly (correct behavior), full-era runs land with the data handoff.*
