# EmberLine

**Historical fire-activity explorer for Indonesia** — built for NASA Space Apps
2026 (Jakarta, challenge *"MODIS & VIIRS Hot Spots"*). EmberLine turns 14.5 years
of NASA FIRMS satellite observations (MODIS Aqua + VIIRS S-NPP, Science Quality
archive) into a validated, honest view of historical burning activity across
**17 regions of Indonesia** — from Aceh to Papua.

**Status:** hackathon build, 14–15 Nov 2026. Science core complete: full-era
reproduction for the two reference AOIs (Riau, Central Kalimantan — 8 pipeline
stages `ok`), G2 evaluation on **4,244 held-out days per AOI**, expansion tiles
ingested for 15 more regions. `DEPLOYMENT.md` documents the deployment flow;
[`docs/STATUS.md`](docs/STATUS.md) tracks the plan.

---

## What this product is — and is not

- A hotspot is a **satellite observation of a thermal anomaly**, not necessarily
  one physical fire.
- **FRP-sum is an aggregate of sampled radiative-power observations (MW)** —
  not total energy, not burned area, not a fire count.
- **Missing data is not zero.** Failed request ≠ unavailable archive ≠ zero
  detections ≠ verified observation opportunity — four different states, kept
  distinct everywhere.
- Harmonized values are **estimates with uncertainty**; MODIS is the chosen
  *reference measurement*, not ground truth.
- All outputs are **historical and descriptive — never predictive, never a
  safe-to-burn recommendation**.

## How the application works

```
NASA FIRMS API (MODIS Aqua · VIIRS S-NPP, SP archive 2012–2026)
   │
   ▼  fetch_firms.py          5-day windows, resumable, sha256 ledger
   ▼  validate.py             schema/coordinate/FRP checks → normalized.csv
   ▼  match (C-02)            0.1° grid → per-cell-day per-sensor aggregates
   │                          (matched pairs + compact zero-fill days)
   ▼  frozen split            train ≤ 2020-10-08 · test = held-out, never seen in fitting
   ▼  baselines (C-03)        B0 naive splice · B1 training-fitted ratio
   ▼  harmonize (C-04)        B2 monotone log-space mapping + 80% intervals
   ▼  metrics (C-05)          12 metrics on identical held-out rows + stress tests
   ▼  calendar (C-06)         366-day climatology + critical windows (p75)
   ▼  serving.db (C-07)       indexed SQLite per AOI
   │
   ▼  FastAPI (api/app.py)    serves versioned artifacts — READ-ONLY, never recomputes
   ▼  React + Vite (web/)     FireMap, calendars, region explorer
```

**Design rule (DEV-S05):** the backend *serves* precomputed science; it never
recomputes it at request time. The heavy data (`data/raw`, `data/processed`)
stays out of git — the canonical artifacts (small CSVs/JSONs) travel with the
repository, and `serving.db` is rebuilt from them in seconds on any machine.

### Who needs what

| Consumer | Needs | From where |
|---|---|---|
| **Backend (D)** | canonical artifacts + `serving.db` (rebuilt in seconds) | git pull |
| **Frontend (E)** | same artifacts via the API | FastAPI endpoint |
| **Re-processing (B/C)** | raw windows + normalized CSVs | Azure Blob `emberline-data` |
| **Audit** | raw inputs + run manifests (sha256-verified) | Blob + run manifests |

The raw archive (171 MB, 25,600+ windows across 17 regions) never travels
through git — it lives on the fetch VM and the Azure Blob container, with every
window sha256-verified against the committed `data/raw/MANIFEST.json`.

## Methodology (frozen protocol `PROTO-C01-v0.9`)

The full scientific protocol is frozen in [`docs/method.md`](docs/method.md)
(machine contract: `config/params.yaml`, enforced by
`tests/test_protocol_contract.py`). Key decisions, all taken **before** any
model saw the data:

| Decision | Value | Why |
|---|---|---|
| Reference sensor | MODIS **Aqua** | instrument stability vs Terra degradation; single reference |
| Target sensor | VIIRS **S-NPP** (SP archive) | longest archive (2012+) |
| Activity metric | **FRP-sum (MW)** per cell-day | physical quantity both sensors measure; detection counts are resolution artifacts |
| Spatial grid | 0.1° cells, centroid assignment | matches FIRMS native resolution scale |
| Train/test split | contiguous, date-frozen: **train ≤ 2020-10-08** | temporal split prevents future leakage |
| Methods compared | **B0** naive splice · **B1** training-fitted ratio · **B2** monotone log-space mapping | baselines make improvement claims falsifiable |
| Evaluation | 12 metrics on identical held-out rows + ≥3 splice stress tests + LOYO | identical rows across methods (F-15) |
| Missing data | four states, never zero-filled | failed ≠ archive-unavailable ≠ zero-detections ≠ observed |

**Evaluation result (held-out era, both reference AOIs):**

| Metric | B0 naive | **B1 ratio (accepted)** | B2 mapping |
|---|---|---|---|
| Mean log-ratio bias (Riau / Kalteng) | −0.75 / −0.88 | **−0.56 / −0.60** | −0.78 / −0.87 |
| log-space R² (Kalteng) | −0.32 | **+0.04** (only positive) | −0.29 |
| Wasserstein MW (Riau / Kalteng) | 10.0 / 37.0 | **5.5 / 9.0** | 8.6 / 28.7 |
| Interval coverage (nominal 0.80) | — | — | **0.87–0.90 measured** |
| Calendar-pattern correlation | — | — | **0.91–0.998** |
| Splice artifact reduction (stress) | — | **11–16% (Riau), up to 34% (Kalteng)** | B2 did not improve |

**B1 — the simple training-fitted ratio — is the accepted published method.**
B2, the more complex mapping we proposed, **did not beat it on data it never
saw**; we publish that negative result rather than hide it.

## Quickstart

Requirements: Python 3.10+ and Node.js. The API reads local versioned artifacts;
it does not require credentials for the routes below.

```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\python.exe -m pip install -r api\requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r api/requirements.txt
npm run serve
# In another terminal, run the frontend:
npm --prefix web run dev
```

The API listens on `http://127.0.0.1:8300`, which matches the Vite `/api` proxy.
It serves health, AOI presets, accepted series, calendars, windows, maps,
detections, methods, jobs, and exports from `artifacts/`. If an artifact is
missing, the endpoint reports that explicitly; the API does not recompute science.
See [`api/README.md`](api/README.md) for details.

## Repository structure

```
api/            FastAPI serving layer (read-only over artifacts/)
web/            React + Vite frontend (FireMap, calendars, region explorer)
pipeline/       science pipeline (fetch, validate, match, harmonize, metrics, calendar)
scripts/        runbook helpers (validate_all, masks_all — fish/bash-safe)
config/         aois.yaml (17 regions) · grid.yaml · params.yaml (frozen protocol)
contracts/      frozen payload contracts (D-02, signed C+E)
artifacts/      per-AOI science artifacts (committed — the source of truth)
data/           raw + normalized caches (gitignored; regenerable; Blob backup)
docs/           method.md (frozen protocol) · validation.md (G2 results) ·
                limitations.md · STATUS.md · azure_fetch_runbook.md · handoffs/
tests/          10 contract suites (~150 checks)
DEPLOYMENT.md   production deployment guide
DECISIONS.md    decision ledger (DEV/DEC/INT — all approved)
```

## Data access

- **Everything a reviewer needs**: this repository (canonical artifacts, docs,
  tests, manifests).
- **Large caches** (raw windows, normalized CSVs): Azure Blob container
  `emberline-data` — restored/refreshed per region via
  `az storage blob download-batch`. Raw inputs are regenerable from FIRMS with
  the fetch pipeline; every window is sha256-verified against the committed
  manifest.

## Limitations

See [`docs/limitations.md`](docs/limitations.md) — in short: descriptive
historical analysis, not prediction or fire counting; FRP-sum is an aggregate
of sampled observations; the archive era ends 2026-07-31; low-density regions
are honestly reported as `insufficient` rather than padded; the harmonization
evaluation covers the two reference AOIs (expansion tiles: ingestion complete,
science chain in progress).

## Attribution

- Data: **NASA FIRMS** — MODIS (Aqua) & VIIRS (S-NPP), Science Quality archive,
  NASA/LANCE/EOSDIS.
- Built for **NASA Space Apps 2026** (Jakarta), challenge *MODIS & VIIRS Hot Spots*.
- AI assistance: pipeline code, documentation and this repository were prepared
  with AI assistance under human direction and review (disclosed per challenge
  rules).

## Team

| Role | Scope |
|---|---|
| B — data engineering | FIRMS ingestion, validation, manifests |
| C — science | grid/matching, baselines, harmonization, evaluation, calendar |
| D — backend/deploy | FastAPI serving layer, deployment |
| E — frontend | FireMap, calendars, region explorer |
| A/F — lead + docs | gates, portal, demo, submissions |

License: see `LICENSE` (decided per team vote; recorded in `DECISIONS.md`).
