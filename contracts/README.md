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
