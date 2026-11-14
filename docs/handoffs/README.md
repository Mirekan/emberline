# docs/handoffs/ — handoff & blocker notes, gate evidence

One short file per milestone, named `<task-id>_<slug>.md` (e.g. `B-05_overlap_evidence.md`,
`G1_real_data.md`). Use these exact templates — replace bracketed values with
verified facts only.

## Handoff note

```
Task ID: [C-xx]; owner: [role/person]; reviewer: [named reviewer]; deliverable/path: [exact path]
run/version ID: [id]; input hashes: [hash or manifest ref]; verification evidence: [command, test output, screenshot or report]
limitations: [coverage, N/A metrics, failed tests, extrapolation]
requested reviewer action: [specific check]; next dependency: [task ID and recipient]
```

## Blocker message

```
Blocked task: [C-xx]. Missing input: [file, decision, access or evidence]
Attempted alternative: [what was tried and result]. Impact: [gate, artifact or claim affected]
Requested decision/person: [named human or role]. Time blocked: [minutes]
Next safe fallback: [documented limitation, narrower AOI, or defer]
```

**Escalation rule:** escalate after 45 minutes on one blocker. Time-box the
attempt, record the alternative tried, ask the owner or lead, and move to a safe
independent task. Never wait silently or improvise false evidence.

A task is DONE only when its reviewer checks the acceptance criteria and the
evidence link lands in `TEAM_TASKS.csv`.
