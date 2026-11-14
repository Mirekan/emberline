"""C-07 contract test — one-command reproducibility + provenance manifest
(pipeline/run.py).

NOTE: this test executes the FULL pipeline on the real Riau fixture and is the
memory-heaviest suite — run it when the machine has headroom (it is part of
`make test`, which the team runs at gate time, not continuously).

Verifies: F-19 provenance fields complete; input hashes match recomputation;
params hash deterministic; stage statuses recorded verbatim (insufficient_data
is not a failure); unknown AOI fails loudly instead of guessing.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import run as runner  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REAL_PAIRS = ROOT / "data/processed/riau/c02/matched_pairs.csv"
FIXED_TS = "20261114T1600Z"


def check_list():
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    if not REAL_PAIRS.exists():
        check("real Riau fixture present for the reproducibility run", False,
              f"{REAL_PAIRS} missing — run the C-02 swap-in first")
        return checks

    result = runner.run("riau", run_ts=FIXED_TS)
    manifest = result["manifest"]

    # -- F-19 provenance fields ------------------------------------------------
    required = ["run_id", "git_sha", "created_utc", "aoi_bbox_date_range", "sources",
                "input_sha256", "params_hash", "train_years", "test_years",
                "metrics_path", "library_versions", "seeds", "stage_statuses"]
    check("manifest carries every F-19 provenance field",
          all(k in manifest for k in required),
          f"missing: {[k for k in required if k not in manifest]}")
    check("run_id format PROTO_<gitsha>_<ts>",
          manifest["run_id"].startswith(f"PROTO-C01-v0.9_{manifest['git_sha']}_{FIXED_TS}"))
    check("sources are the frozen DEC-1 strings",
          manifest["sources"] == ["MODIS_SP", "VIIRS_SNPP_SP"])

    # -- input hashes match recomputation ----------------------------------------
    recomputed = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                  for p in manifest["input_sha256"]}
    check("input sha256 values match recomputation",
          recomputed == manifest["input_sha256"])
    params_hash2 = hashlib.sha256((ROOT / "config/params.yaml").read_bytes()).hexdigest()
    check("params_hash deterministic and matches params.yaml",
          manifest["params_hash"] == params_hash2)

    # -- stage statuses recorded verbatim (honest states, not verdicts) -----------
    stages = manifest["stage_statuses"]
    check("match stage ran (ok) on the real fixture", stages["c02_match"]["status"] == "ok")
    honest = {"c03_baselines", "c04_harmonize", "c05_metrics", "c05_splice_stress",
              "c06_calendar", "c06_windows"}
    check("downstream stages recorded as insufficient_data/deferred — never silently ok",
          all(stages[s]["status"] in {"insufficient_data", "deferred"} for s in honest),
          f"got {[(s, stages[s]['status']) for s in honest]}")
    check("honesty note present in manifest",
          "NOT failures or passes" in manifest["honesty_note"])

    # -- determinism of content (run_id timestamp aside) ---------------------------
    rerun = runner.run("riau", run_ts=FIXED_TS)
    check("two identical runs -> identical params hash + stage statuses (deterministic)",
          rerun["manifest"]["params_hash"] == manifest["params_hash"]
          and rerun["manifest"]["stage_statuses"] == manifest["stage_statuses"])

    # -- unknown AOI fails loudly, never guesses ------------------------------------
    try:
        runner.run("not_an_aoi")
        check("unknown AOI raises instead of guessing", False)
    except FileNotFoundError as exc:
        check("unknown AOI raises instead of guessing", "not in config/aois.yaml" in str(exc))

    # -- split years recorded from the frozen protocol -------------------------------
    check("train/test years recorded from frozen split (None until real fit succeeds)",
          manifest["train_years"] is None or isinstance(manifest["train_years"], list))

    return checks


def _report(checks):
    failed = [(n, d) for n, ok_, d in checks if not ok_]
    for name, okv, detail in checks:
        print(f"[{'PASS' if okv else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not okv else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def test_run_manifest():
    failed = [(n, d) for n, ok_, d in check_list() if not ok_]
    assert not failed, f"C-07 manifest violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(check_list()))
