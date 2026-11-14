# DECISIONS.md

**Owner: A (task A-02). One row per decision. Status ∈ `OPEN · PENDING · APPROVED · REJECTED · SUPERSEDED`.**
Every PRD deviation must appear here before affected work starts; silent deviations are forbidden.

## Scope deviations (from PRD, proposed in TEAM_EXECUTION_PLAN §2.5)

| ID | Decision | Affected requirements | Status |
|---|---|---|---|
| DEV-S01 | Aqua MODIS + one VIIRS platform (S-NPP) only; Terra & NOAA-20/21 excluded in v1 | FR-DATA-6, FR-HARM-8 (→ O-05) | PENDING |
| DEV-S02 | FRP-sum only as activity metric; metric selector deferred | FR-HARM-1 (selector component) | PENDING |
| DEV-S03 | Monotone log-space mapping (B2); quantile correction omitted in v1 | FR-HARM-3 | PENDING |
| DEV-S04 | Bounded custom rectangles only; genuine recompute for supported cached areas, explicit unsupported/insufficient otherwise | FR-UI-1 | PENDING |
| DEV-S05 | One app, one backend, precomputed versioned artifacts; no DB/auth/queue/runtime-LLM | PRD §11 | PENDING |
| DEV-S06 | CSV provenance as ordinary columns, not leading comment headers | FR-EXP-1 | PENDING |

## Open decisions

| ID | Needs | Resolves | Status |
|---|---|---|---|
| DEC-1 | B-01 keyed availability probe | exact FIRMS source strings, archive dates, S-NPP confirmation | OPEN |
| DEC-2 | B-05 overlap evidence | minimum-support numbers (0.90 paired-retrieval / 10 signal days, provisional) — frozen before fitting | OPEN |
| DEC-3 | coverage review at C-06 | `years_active` definition | OPEN |
| DEC-4 | A records re-baseline | team actual start 09:00 WIB Sat 14 Nov; proposed G2 evidence ~H22–H23 (22:00–23:00 WIB); G3 feature freeze stays H30 (Sun 06:00); deadline unchanged | PROPOSED |
| DEC-5 | A-01 confirmation | official brief + deadline timezone (claims language only) | OPEN |

## Integration decisions

| ID | Decision | Owner | Status |
|---|---|---|---|
| INT-1 | Monorepo with path ownership; artifacts-as-interface (no cross-role imports); Makefile = single entry point; contracts-first (D-02 freezes payload examples before parallel implementation) | D to confirm at D-01/D-02 | PROPOSED |
| INT-2 | Git discipline: single `main`, commit prefix `[task-id]`, push per task, one editor per shared file | D / A | PROPOSED |

## Gate records

Filled by A as gates pass/fail: G1 (real data) · G2 (science) · G3 (feature freeze) · G4 (release).

| Gate | Scheduled (re-baselined) | Result | Evidence |
|---|---|---|---|
| G1 | H8 → overdue; pending B-01/B-05 | — | — |
| G2 | ~H22–H23 (PROPOSED, DEC-4) | — | — |
| G3 | H30 = Sun 06:00 WIB | — | — |
| G4 | target H38, ready by H42 | — | — |
