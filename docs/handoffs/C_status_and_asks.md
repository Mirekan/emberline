# C status & asks — before/alongside C-06 & C-07

Task: coordination note (owner C) · date: 14 Nov 2026 ~15:20 WIB ·
state: C-01..C-05 scaffolds + Riau fixture swap-in COMPLETE (commits c22d900..fc2e3e2);
real-data fitting has NOT happened (fixture support gate returned insufficient_data — compliant with
the "no fitting before sign-off" rule).

## ASK-1 → A (blocking real-data C-06/C-07, cheap to unblock)

1. **Approve DEV-S01..DEV-S06** (DECISIONS.md all still PENDING). C-06/C-07 *encode* these
   simplifications (FRP-sum-only index = S-02; frozen protocol = S-03; Aqua-only reference = S-01).
   A rejection after C-06 would mean rework — decide now, while everything is still scaffold.
2. **Record DEC-4** (gate re-baseline: team start 09:00 WIB, proposed G2 ≈ H22–23, G3 stays H30).
3. **Decide the B-02 presets open flag** (Indonesia-only five vs plan's global candidates) → DECISIONS.md.
4. **Run A-03 (G1 decision)** — C's review input is ready: `docs/handoffs/C-02_review_B-05.md`
   (consistency 7/7, fixture recount exact 5/5).

## ASK-2 → B (blocking full-era C-06/C-07)

- **Full-era 848k normalized rows + retrieval masks for BOTH AOIs** (currently only the compact
  Riau fixture is local; Kalteng `w113` processed files never delivered). Same channel as before;
  `data/**` stays out of git by design.

## ASK-3 → D (two small items)

1. **Pin pyarrow** (D-01) — full-era zero-fill pairs reach millions of rows; CSV output will not scale.
2. **Claim D-02 & finalize `contracts/`** — draft v0.1 (`series.example.json`) is waiting for the
   D-02 freeze; E-03 is blocked on it more than C is.

## ASK-4 → B/D/E (protocol formality, 15 minutes)

**Sign off C-01** (`docs/method.md` §8): units/matching reality (B), payload implementability (D),
legend renderability (E). Rule: no REAL fitting before sign-off — we are still compliant because
every real-data run so far honestly returned insufficient_data, but C-06/C-07 real runs must wait
for these three signatures.

## C's outstanding reviewer duties (NOT blocking C-06/C-07)

D-06 (CSV exports), E-03 (charts), F-02 (sources/AI log), F-04 (demo claims) — reviewed when they
land. A-03 input ready, decision sits with A.

## What proceeds regardless

C-06 (calendar/climatology/windows) and C-07 (packaging/manifest) scaffolds run on synthetic +
fixture data exactly like C-03..C-05 did — no dependency on the asks above. DEC-3 (active-year
definition) is resolved *inside* C-06 by design.
