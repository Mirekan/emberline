# api/ — backend (owner: D)

FastAPI serving **versioned precomputed artifacts** from `artifacts/` — it must
never import `pipeline/` or recompute science at request time (DEV-S05).

- Payload contracts live in [`../contracts/`](../contracts/) — implement against
  the frozen examples; statuses include `insufficient_data`/`unsupported`.
- Keep `FIRMS_MAP_KEY` server-side only; sanitize errors; cap custom-area jobs.
- Entry point (proposed): `api/app.py` → `make dev` / `make serve`.
- Status: pending — owner tasks D-01…D-07.
