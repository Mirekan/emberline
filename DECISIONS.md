# DECISIONS.md

**Owner: A (task A-02). One row per decision. Status ∈ `OPEN · PENDING · APPROVED · REJECTED · SUPERSEDED`.**
Every PRD deviation must appear here before affected work starts; silent deviations are forbidden.

**Approval record: ALL items below approved by A (team lead, solo-role day) — verbal approval
14 Nov 2026 ~16:10 WIB, recorded by C on A's instruction. Where owner=reviewer is the same
human, that limitation is disclosed here (small-team day-1 condition).**

## Scope deviations (from PRD, proposed in TEAM_EXECUTION_PLAN §2.5)

| ID | Decision | Affected requirements | Status |
|---|---|---|---|
| DEV-S01 | Aqua MODIS + one VIIRS platform (S-NPP) only; Terra & NOAA-20/21 excluded in v1 | FR-DATA-6, FR-HARM-8 (→ O-05) | APPROVED 14 Nov |
| DEV-S02 | FRP-sum only as activity metric; metric selector deferred | FR-HARM-1 (selector component) | APPROVED 14 Nov |
| DEV-S03 | Monotone log-space mapping (B2); quantile correction omitted in v1 | FR-HARM-3 | APPROVED 14 Nov |
| DEV-S04 | Bounded custom rectangles only; genuine recompute for supported cached areas, explicit unsupported/insufficient otherwise | FR-UI-1 | APPROVED 14 Nov |
| DEV-S05 | One app, one backend, precomputed versioned artifacts; no DB/auth/queue/runtime-LLM | PRD §11 | APPROVED 14 Nov |
| DEV-S06 | CSV provenance as ordinary columns, not leading comment headers | FR-EXP-1 | APPROVED 14 Nov |
| DEV-S05-CLARIF | Clarification of DEV-S05: "no database" means **no database SERVER** (no Postgres/deployment infra); an **embedded SQLite file as a derived serving artifact** (`artifacts/<aoi>/serving.db`, rebuilt by `make reproduce`, canonical sources remain CSV/JSON) is allowed | PRD §11 | APPROVED 14 Nov (instructed by A) |

## Frozen decisions

| ID | Decision | Basis | Status |
|---|---|---|---|
| DEC-1 | Exact FIRMS source strings `MODIS_SP`, `VIIRS_SNPP_SP`; S-NPP SP archive confirmed; era cap 2026-07-31 | B-01 keyed probe + B-05 fetch | APPROVED 14 Nov |
| DEC-2 | Minimum support: ≥90% paired-retrieval fraction & ≥10 MODIS-signal days per year; fitting needs ≥2 train + ≥1 test eligible years | B-05 coverage evidence (weakest year 334 rows) | APPROVED 14 Nov |
| DEC-3 | `years_active` = year's daily index ≥ window threshold on ≥3 era days (PROVISIONAL rule frozen with windows.json); years_eligible = ≥60% of calendar-era days | C-06 coverage review | APPROVED 14 Nov |
| DEC-4 | Gate re-baseline: team start 09:00 WIB 14 Nov; G2 evidence ≈ H22–H23; G3 feature freeze stays H30 (Sun 06:00); deadline unchanged | team actual start | APPROVED 14 Nov |
| DEC-5 | Official brief + deadline timezone — STILL UNRESOLVED (A-01 not yet confirmed by organizer); claims language stays conservative until then | A-01 | OPEN |
| DEC-6 | **Method selection outcome (G2 fail action, §6.4): B1 training-fitted ratio = accepted harmonization (published series); B2 monotone mapping = NEGATIVE RESULT on held-out data (worse than B1 on both AOIs), kept visible in artifacts/method page/demo. No held-out tuning occurred — split & methods frozen pre-results.** | real G2 metrics (docs/validation.md) | APPROVED 14 Nov (protocol-mandated fail action) |
| AOI-PRESETS | Indonesia-only five (riau, central_kalimantan, south_sumatra, jambi, merauke) replace plan's global candidates | B-02 delivery + density probe plan | APPROVED 14 Nov |
| AOI-PRESETS-EXPANSION | **Full-Indonesia mosaic: +12 tile AOIs** (kalbar, kaltim, papua_selatan, sulsel, ntt, ntb, sumut_aceh, lampung — tier A; papua_barat, maluku, jawa, bengkulu_barat — tier C probe-first), era profile (b) 2018-01-01..2026-07-31 per tile (straddles frozen split → full harmonization science per tile); fetch on Azure parallel, one ledger per tile. Statuses per tile stay honest (thin-density tiles may be `insufficient` — recorded, never padded) | A instructed in session; config/aois.yaml updated + docs/azure_fetch_runbook.md | APPROVED 14 Nov |

## Integration decisions

| ID | Decision | Owner | Status |
|---|---|---|---|
| INT-1 | Monorepo with path ownership; artifacts-as-interface (no cross-role imports); Makefile = single entry point; contracts-first | confirmed by A; D-01/D-02 artifacts landed as proposals (requirements.txt, contracts v0.1→FROZEN) | APPROVED 14 Nov |
| INT-2 | Git discipline: single `main`, commit prefix `[task-id]`, push per task, one editor per shared file | D / A | APPROVED 14 Nov |
| INT-3 | **Backend stack: Rust + actix-web replaces proposed FastAPI** (D-01 request; artifacts-as-interface makes this zero-impact on C — see earlier assessment). Rust api/ skeleton landed: health not_ready, sanitized 404, bind validation, clippy/fmt clean, 2 route tests | D requested; A confirmed in session | APPROVED 14 Nov |

## Sign-offs (C-01 protocol, docs/method.md §8)

| Role | Sign-off | Note |
|---|---|---|
| B — units/matching reality | APPROVED 14 Nov ~16:10 WIB | owner=reviewer same human (disclosed) |
| D — payload implementability | APPROVED 14 Nov ~16:10 WIB | owner=reviewer same human (disclosed) |
| E — legend renderability | APPROVED 14 Nov ~16:10 WIB | owner=reviewer same human (disclosed) |

## Gate records

Filled by A as gates pass/fail: G1 (real data) · G2 (science) · G3 (feature freeze) · G4 (release).

| Gate | Scheduled (re-baselined) | Result | Evidence |
|---|---|---|---|
| G1 | H8 → re-baselined; input ready | PENDING A DECISION | docs/handoffs/C-02_review_B-05.md (consistency 7/7, recount exact 5/5) |
| G2 | ~H22–H23 (APPROVED, DEC-4) | machinery ready; real evidence deferred (fixture insufficient_data) | docs/validation.md + 9 contract suites |
| G3 | H30 = Sun 06:00 WIB | — | — |
| G4 | target H38, ready by H42 | — | — |
