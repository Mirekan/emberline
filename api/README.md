# EmberLine API

The FastAPI application in `app.py` serves versioned files from `artifacts/`.
It does not import the science pipeline or recompute scientific results. The
development server listens on `127.0.0.1:8300`, matching the Vite proxy.

## Run locally

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api\requirements.txt
npm run serve
```

On macOS/Linux, use `.venv/bin/python` for the install command. The npm
`serve` script selects the platform-specific Python executable from `.venv`.
Stop the server with Ctrl+C.

## Endpoints

- `GET /api/health`
- `GET /api/aoi/presets`
- `GET /api/aoi/{id}/series`
- `GET /api/aoi/{id}/calendar`, `/climatology`, `/windows`, `/stress`, `/grid`,
  and `/detections`
- `GET /api/method?aoi={id}`
- `GET /api/aoi/{id}/export?what=series|windows|calendar`
- `POST /api/aoi/analyze` and `GET /api/jobs/{job_id}`

Artifact-backed routes return an explicit error when the requested data is
unavailable. The analyze job store is in-process and bounded; jobs are not
persisted across server restarts. `FIRMS_MAP_KEY`, when used by other tools,
is not returned by the API.
