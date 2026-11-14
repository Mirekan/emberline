# api/ — backend (owner: D)

Rust/actix-web local server skeleton, selected by team member D. Entry point:
`src/main.rs`; routes and tests: `src/lib.rs`. Dependencies are pinned in
`Cargo.toml` and `Cargo.lock`. No database, authentication, queue, or pipeline import.

## Run from the repository root

```bash
make dev
curl http://127.0.0.1:8000/api/health
make test
make build
make serve
```

`make test` also runs C's existing Python protocol check; install its pinned
dependency using the root README setup. Rust-only: `cargo test --manifest-path api/Cargo.toml --locked`.
Stop the server with Ctrl+C before starting another on the same address.

Set `EMBERLINE_BIND_ADDR` to an IP:port socket address, default `127.0.0.1:8000`:
`EMBERLINE_BIND_ADDR=127.0.0.1:8080 make dev`. IPv6 uses `[::1]:8080`.
Invalid addresses or occupied ports fail startup. Environment variables must be
exported; `.env` is not auto-loaded. No FIRMS key is read or needed by this skeleton.

## Current HTTP boundary

- `GET /api/health`: HTTP 200 liveness, `service: "emberline-api"`, package
  `version`, `status: "not_ready"`, `ready: false`, `data_version: null`, `run_id: null`.
  This proves the process responds, not scientific/data readiness. No data is loaded.
- Unknown routes: HTTP 404 `application/problem+json` with fixed
  `type`, `title`, `status`, `detail`; request text and private paths are not echoed.
- No CORS permissions are granted; no wildcard origin. Approve frontend origins
  with E before enabling cross-origin access. No request-URL logging.

## Not implemented

Artifact-backed endpoints, custom jobs, CSV exports, frontend integration, and
public deployment. Keep future results backed by validated versioned artifacts
from `artifacts/`; never import `pipeline/` or invent scientific values (DEV-S05).
Shared contracts in [`../contracts/`](../contracts/) still need C/E sign-off.
Hosting approval and A's scope decisions remain pending; this is not D-03 completion.
Keep `FIRMS_MAP_KEY` server-side, errors sanitized, and future jobs bounded.
