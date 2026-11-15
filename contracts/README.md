# contracts/ — the team's shared interface

**Owner: D (task D-02). C and E must sign off before separate implementations start.**

Rules:

1. **Contract-first:** code against the frozen example files here, never against
   in-progress implementations. If the contract must change, D edits, C+E re-sign,
   and every affected payload example gets a new version date.
2. Every payload carries `run_id` / `model_version` — a displayed number must be
   traceable to an artifact run (C-07 manifests).
3. `null` means explicit gap **with a reason** — never silently 0.
4. Status enum (all job/error responses): `queued · running · complete · failed ·
   insufficient_data · unsupported · expired`.

## Endpoint inventory

| Endpoint | Owner task | Example | Status |
|---|---|---|---|
| `GET /api/health` | D-03 | [`../api/README.md`](../api/README.md#current-http-boundary) | Local skeleton; C/E review pending |
| `GET /api/aoi/presets` | D-04 (config: B-02) | — | DRAFT |
| `GET /api/aoi/{id}/series` | D-04 | [`series.example.json`](series.example.json) | **FROZEN v1.0 — signed by C+E 14 Nov 2026 (owner=reviewer same human, disclosed in DECISIONS.md); D implements against this** |
| `GET /api/aoi/{id}/calendar` | D-04 / C-06 | — | DRAFT |
| `GET /api/aoi/{id}/climatology` | D-04 / C-06 | — | DRAFT |
| `GET /api/aoi/{id}/windows` | D-04 / C-06 | — | DRAFT |
| `GET /api/aoi/{id}/export` | D-06 | — | DRAFT |
| `GET /api/method` | D-04 / C-07 | — | DRAFT |
| `POST /api/aoi/analyze`, `GET /api/jobs/{id}` | D-05 | — | DRAFT |

## First payload draft — `GET /api/aoi/{id}/series`

Fields come straight from the C-01 protocol (`config/params.yaml`). See
[`series.example.json`](series.example.json). Key semantics E must render:

- `source_flag` ∈ `observed_modis · harmonized_viirs · gap` (protocol F-14: never blend).
- `flags[]` ∈ `one_sided · extrapolation · zero_returned_signal · insufficient_support` — each must be visually distinct from a gap.
- `harmonized = {lo_mw, estimate_mw, hi_mw}` — the interval is the uncertainty statement, not decoration; bounds are finite and ordered.
- Every daily record separates day/night classes; `daynight: "all"` only in rollups.
- Gaps carry `reason` ∈ `failed_request · unavailable_archive · outside_coverage · insufficient_support`.

## Serving artifact — `artifacts/<aoi>/serving.db` (SQLite, DERIVED)

**Producer: C-07 (`pipeline/serving_db.py`, rebuilt every `make reproduce`) · Consumer: D backend, any stack.**
The canonical artifacts remain the CSV/JSON files; `serving.db` is a derived,
git-ignored index (sha256 recorded in `run_manifest.json`) so the backend can
serve indexed queries without CSV parsing at request time. Backend opens it
**read-only** — it never writes science.

Tables:

| Table | Key | Contents |
|---|---|---|
| `meta` | key | run_id, git_sha, bbox/era, sources, train/test years, `stage_<id>` statuses, `missing_sources` (honest gaps) |
| `accepted_series` | date (+idx position) | published daily series: `source_flag`, `value_mw`, `index_value`, raw harmonized/observed |
| `calendar` | position (366) | median raw/smoothed, p10/p25/p75/p90, n_years, state (`populated`/`sparse`/`missing`) |
| `windows` | id | critical-window runs + `meta` rows for threshold, years_eligible, activity |
| `baselines` | (date, daynight) | observed MODIS/VIIRS + B0 + B1 predictions |
| `harmonized_daily` | (date, daynight) | B2 estimate + lo/hi + role + flags |
| `metrics` | (method, metric) | value or **NULL = N/A with `reason`** — never 0 |
| `splice_stress` | (method, transition_date) | B2 **and** B1 rows: shifts, errors, error_ratio, notes |
| `years` | year | era/valid days, eligible, active (DEC-3) |

Semantics preserved from the protocol: `NULL` = explicit gap/N-A with reason,
never 0; bounds finite/ordered; every row traces to `meta.run_id`. Deferred
stages ⇒ their tables simply don't exist (check `meta.stage_*` +
`missing_sources`) — the DB is never padded with synthetic rows.
