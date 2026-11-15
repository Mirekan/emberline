# EmberLine

Historical MODIS/VIIRS hotspot explorer: compare raw sensor records, a harmonized
estimate with uncertainty, and a burning-activity calendar for a region of interest.

**Status:** hackathon build, 14–15 Nov 2026 (NASA Space Apps Jakarta, challenge
"MODIS and VIIRS Hot Spots"). Planning sources live in `../TEAM_EXECUTION_PLAN.md`
and `../TEAM_TASKS.csv`. This README is a stub — task F-05 owns final content.

## What this product is — and is not

- A hotspot is a **satellite observation of a thermal anomaly**, not necessarily one physical fire.
- **FRP-sum is an aggregate of sampled radiative-power observations (MW)** — not total energy, not burned area, not a fire count.
- **Missing data is not zero.** Failed request ≠ unavailable archive ≠ zero detections ≠ verified observation opportunity.
- Harmonized values are **estimates with uncertainty**; MODIS is the chosen reference measurement, not ground truth.
- All outputs are **historical and descriptive — never predictive, never a safe-to-burn recommendation**.

## Repo map — edit only your directory

| Path | Owner | Contents |
|---|---|---|
| `Makefile`, `.gitignore`, `.env.example` | **D** | integration glue |
| `contracts/` | **D-02** (C & E sign off) | frozen payload examples, statuses, error schema |
| `config/aois.yaml` | **B-02** | five regions + real coverage |
| `config/grid.yaml`, `config/params.yaml` | **C-01** ✅ | scientific protocol contract |
| `pipeline/fetch_firms.py`, `validate.py` | **B** | ingestion, validation |
| `pipeline/grid.py`, `match.py`, `harmonize.py`, `metrics.py`, `calendar.py`, `windows.py` | **C** | science pipeline |
| `data/raw/`, `data/processed/` | **B** | caches (git-ignored; `data/raw/MANIFEST.json` committed) |
| `artifacts/` | **C** outputs, **D** serves | versioned results (JSON committed, parquet ignored) |
| `api/` | **D** | FastAPI service on port 8300; serves versioned artifacts without importing the pipeline |
| `web/` | **E** | React/Vite frontend — never imports Python |
| `tests/` | all roles | tests beside their code; `make test` runs everything |
| `docs/method.md`, `validation.md`, `limitations.md` | **C** (A verifies) | science docs |
| `docs/handoffs/`, gate evidence | all roles | handoff + blocker notes |
| `docs/demo/`, this README | **F** | deck, submission text |
| `DECISIONS.md` | **A** | scope decisions, deviations, gate records |

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

## Integration rules (short version)

1. **One monorepo, path ownership.** Nobody imports another role's code.
2. **Artifacts are the interface.** B→C: parquet + schema. C→D: versioned artifacts + `run_id`. D→E: HTTP payloads frozen in `contracts/`.
3. **Code against frozen contract examples**, not against in-progress implementations.
4. Shared files (`Makefile`, `contracts/`, `DECISIONS.md`) have exactly one editor each.
5. Commit per task with `[task-id]` prefix; use `[misc]` for small unplanned changes; never commit `data/`, `.env`, or credentials.

## Commit messages

Use this format:

`[<task-id>] <type>(<scope>): <imperative summary>`

For small changes outside the task plan, replace `<task-id>` with `misc`:

`[misc] <type>(<scope>): <imperative summary>`

Examples:

```text
[C-02] feat(pipeline): generate AOI grid
[misc] chore(repo): update .gitignore
[misc] docs(readme): clarify quickstart
[misc] refactor(pipeline): remove unused helper
```

Use `feat` for new behavior, `fix` for bug corrections, `refactor` for internal restructuring, `perf` for performance improvements, `docs` for documentation, `test` for tests, `build` for build integration, and `chore` for maintenance.

Use the task ID when a small change belongs to an existing task. Do not hide a bug, security issue, or data-loss fix under `[misc]`; create a proper task or use `[hotfix]`.

## Scientific protocol

All modeling follows the frozen protocol `PROTO-C01-v0.9` in
[`docs/method.md`](docs/method.md) (machine contract: `config/params.yaml`,
enforced by `tests/test_protocol_contract.py`).
