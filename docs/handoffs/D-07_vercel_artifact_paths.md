Blocked task: D-07 Vercel artifact serving. Root cause reproduced and fixed in the repository; the provider-side setting still needs one dashboard change by the project owner. Vercel CLI is logged out and the repo has no `.vercel/project.json`, so the live project config was not read or edited.

Cause: the Vercel project's function root is `api/`, so the deployed app is `api/app.py` with a bundle root that is not the repository root. `api/app.py:31` computes `ROOT = Path(__file__).resolve().parents[1]`; `api/app.py:76` reads `ROOT/artifacts/<aoi>/<file>`; `api/app.py:175` reads `ROOT/config/aois.yaml`. In that bundle both resolve outside the deployed files, so artifact routes 404 while the app itself answers.

Production evidence (2026-11-15T15:22–15:29Z, `https://emberline-u6pu.vercel.app`):
- `/`: HTTP 404 with the application's own JSON body — this deployment is API-only; the frontend is a separate project.
- `/api/health`: 200, `aois_with_artifacts: []`.
- `/api/aoi/presets`: 200, `presets: []` — a missing `config/aois.yaml` empties the list instead of raising.
- `/api/aoi/riau/calendar`: 404 `calendar.json`; `/series` and `/windows`: 404 `run_manifest.json`; `/grid`: 404 `grid.json`.
- `Origin: https://frontend.example` still returns `Access-Control-Allow-Origin: *`; CORS is not the fault.
- `git ls-files` confirms `artifacts/riau/*` and `config/aois.yaml` are tracked.

Fix applied (repo): root `app.py` re-exporting `api.app.app` as the Vercel entrypoint, plus `fastapi`/`uvicorn` in the root `requirements.txt` (Vercel installs from the entrypoint's manifest). `api/`, `web/`, `contracts/`, and `artifacts/` are untouched.

Verification: `.venv/bin/python -m uvicorn app:app --port 8399` from the repository root —
- `/api/health` 200, 16 AOIs with artifacts, `riau` present
- `/api/aoi/presets` 200, 17 presets, `riau` status `available`
- `/api/aoi/riau/calendar` 200, 15 years, 366 climatology points
- `/api/aoi/riau/windows` 200

Outstanding (project owner, dashboard): set Root Directory to the repository root, framework preset FastAPI, redeploy, then re-check health/presets/calendar from a fresh session. Multi-service import does not apply — one backend, no second service to bind.

Unrelated pre-existing failure: `tests/test_api_series.py::MapArtifactTests.test_grid_counts_observations_and_filters_detections_by_cell_bounds` expects date-less detection fixtures to aggregate, but `api_detections` keys its de-duplication set on `item["date"]`/`item["sensor"]`, so the aggregate is 0. It fails against unmodified `api/app.py`; not caused by this change, not fixed here.

Provider references checked:
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/deployments/configure-a-build#root-directory
