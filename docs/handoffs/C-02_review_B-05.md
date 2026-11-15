# C review — B-05 overlap evidence & B-02 AOI config

Task: C reviewer duties (per TEAM_TASKS.csv, reviewers of B-05/B-02). Input for
A's G1 gate decision (A-03). Date: 14 Nov 2026 ~12:40 WIB. Reviewer: C.

## Verified from committed artifacts

- **Internal consistency 7/7 PASS** — every number in B-05_overlap_evidence.md
  reconciles: Aqua+Terra sums equal MODIS kept-rows (83,318 / 72,811);
  days-with-detections + retrieved-zero = retrieved-days = 5,307 per source per
  AOI (4/4); total across the four streams = 848,007 ("848k" ✓).
- **MANIFEST.json structural check** — 4,249 windows, every one carries sha256;
  2,124 windows per source = 1,062 five-day chunks × 2 AOIs ✓; statuses
  `ok` (3,965) / `ok_empty` (284) kept separate ✓; 1 extra VIIRS_SNPP_NRT window
  = the B-01 probe, not blended into the SP era ✓.
- **Coverage claims support the science**: both families present across
  2012-01-20..2026-07-31 (~14.5 y); Aqua reference support 93,173 rows across
  two AOIs → S-01 (Aqua-only reference) feasible without Terra pooling.
  Weakest year 334 MODIS rows (2022, Kalteng) far exceeds the 10-signal-day floor.
- **Four-state missingness discipline held** (B-05 "what this does NOT establish"
  section is correct and matches F-9).

## C decisions enabled by this evidence (frozen today, before fitting)

| Decision | Value | Basis |
|---|---|---|
| DEC-1 (source strings) | `MODIS_SP`, `VIIRS_SNPP_SP`; VIIRS platform field is `N` | B-01 probe + B-05 fetch |
| DEC-2 (minimum support) | frozen at 0.90 paired-retrieval fraction / 10 signal days — confirmed met | weakest year 334 rows; ~100% retrieval coverage |
| Temporal split (F-10) | train ≤ 2020-10-08, test ≥ 2020-10-09 | earliest ~60% of 5,307-day era; frozen BEFORE fitting |
| match.py platform rule | source-based acceptance (fixes satellite='N' reality) | B-05 evidence |

`config/params.yaml` + `config/grid.yaml` updated; contract tests updated and
passing (65/65 protocol, 29/29 C-02).

## Deferred review item (honest gap)

Independent row recount against the saved Parquet and hash recomputation of raw
bytes require the git-ignored data files, which live on B's machine — **not
present in this working copy** (only MANIFEST.json is committed by design).
C-02 swap-in and the recount are BLOCKED until B transfers
`data/processed/<aoi>/` normalized rows + retrieval masks (or grants access).
Requested channel: shared drive / direct transfer; `data/**` stays out of git.

## UPDATE 14 Nov ~13:15 WIB — Riau fixture swap-in completed (recount DONE for the delivered fixture)

B delivered a compact REAL fixture (B-06, `FIXTURE_REAL_SAMPLE`):
`data/processed/{MODIS_SP,VIIRS_SNPP_SP}/w100_s-2_e105_n1/normalized.csv`
covering 2012-01-20..2015-09-15 (VIIRS file window starts 2015-09-01). C ran the
full seam end-to-end: `ledger_to_mask.py` (2,124 windows → 10,614 mask days =
5,307 × 2 sources ✓) → `match.py` swap-in. **Recount vs B-04 validation reports:
exact on every number** — MODIS rows_in 26,917 ✓; VIIRS 26,420 ✓;
`excluded_platform_v1` = Terra 10,250 ✓ (S-01); Aqua aggregated 16,667 ✓; one
detection disclosed as outside-AOI (centroid rule F-4). Pair states: 818
matched_signal / 2,910 one_sided (excluded from fitting) / 41,272 matched_zero
(zero-filled within the 15-day both-retrieved window) / 7,518 missing_retrieval
days outside the fixture window (honest: VIIRS side not delivered → not
fittable). Mask clipped to the delivered window, disclosed as
`mask_clipped_to_delivered_window`.

**VIIRS era question resolved**: the fixture's 2015-09-01 VIIRS start is a
fixture-window choice, NOT the archive boundary — B-01 availability probe says
`VIIRS_SNPP_SP 2012-01-20..2026-07-31` and the ledger shows 264 pre-2015-09
windows all containing rows (first: 2012-01-20, 330 rows). Overlap era
2012-01-20..2026-07-31 and the frozen split (train ≤ 2020-10-08) stand.

Remaining for full C-02 (not the fixture): Central Kalimantan processed files
not yet delivered; full-era Riau/Kalteng rows → then matched_pairs scale needs
parquet (pyarrow pin, D-01). C-03 proceeds on synthetic AOI-day series until
then — with the fixture correctly returning `insufficient_data` for fitting.

## Open flags for A

1. **Presets substitution**: B-02 replaced the plan's global candidates with an
   Indonesia-only set (south_sumatra, jambi, merauke pending density probe).
   C has no scientific objection — two G1 AOIs are real and sufficient for the
   harmonization claim — but this is a scope deviation that needs a DECISIONS.md
   entry (PRD's five-preset list vs delivered list).
2. Commit message hygiene: one C-02 commit subject contains pasted
   brainstorming text (cosmetic; no action needed beyond awareness).
