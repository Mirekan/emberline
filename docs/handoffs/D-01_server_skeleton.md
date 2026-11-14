# D-01 — Rust server skeleton

Owner: team member D (requesting user). Required reviewer: B; named reviewer pending A.
Stack: Rust + actix-web, explicitly requested by D; A should record the stack change
from proposed FastAPI in DECISIONS.md. No approval of other pending decisions implied.

Delivered: api/Cargo.toml, api/Cargo.lock, api/src/main.rs, api/src/lib.rs;
Makefile run/test/build wiring; requirements-test.txt; credential-free configuration,
ignore rules, and run documentation. No data/model run exists; health reports
not_ready with null data_version/run_id. No scientific fixtures are served.

Observed verification:
- make test: 2 Rust route tests passed; C-01 protocol checks 64/64 passed.
- make build: release binary built at api/target/release/emberline-api.
- Clean source copy with a fresh Python environment, no credentials, and reused
  Cargo dependency cache: make test and make build passed.
- cargo fmt --manifest-path api/Cargo.toml --check: passed.
- cargo clippy --manifest-path api/Cargo.toml --locked --all-targets -- -D warnings: passed.
- Real HTTP through make dev and make serve: health 200, not_ready/null provenance,
  sanitized JSON 404, no cross-origin grant; temporary processes stopped afterward.
- Empty, malformed, oversized-port and hostname bind addresses rejected at startup.
- make reproduce AOI=riau: explicit NOT READY, science pipeline missing.
- Ignore checks cover .env/.env.production, Rust target, .venv, data and parquet caches.

Limits: local skeleton only. D-02 C/E contract review, real artifact endpoints,
custom jobs, exports, frontend integration and hosting approval/deployment remain
pending. D-03 and D-07 are not complete. No credentials required or read.

Reviewer action: B verifies clean run/test setup and secret/cache boundaries;
C/E review health semantics before wider API implementation. A records stack and
hosting decisions. No task-board completion claimed before independent review.

AI assistance: Hermes Agent generated the server, tests, integration wiring and
related documentation; human review pending. No scientific data was generated.
