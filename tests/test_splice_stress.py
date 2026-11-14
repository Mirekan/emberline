"""C-05 contract test — splice stress tests (pipeline/splice_stress.py).

Synthetic held-out series with a PLANTED raw-VIIRS jump: the naive splice must
show the artifact, a perfect B2 must remove it, a deliberately bad B2 must keep
it visible (negative result), and short history must defer honestly.

Run standalone:  python tests/test_splice_stress.py
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import splice_stress  # noqa: E402

R_TRUE = 1.25


def build_series(n_days=90, start="2021-01-01", bad_b2=False):
    """FIXTURE_SYNTHETIC: smooth observed MODIS with 3 planted peaks; raw VIIRS
    error OSCILLATES exactly at each segment boundary (i>=15, >=45, >=75), so
    every ±14-day pseudo-transition window straddles an error change — a
    constant multiplicative error would cancel in the log-shift difference.
    B2 is a perfect correction unless `bad_b2` simulates a failed model whose
    own 3x oscillation makes the artifact WORSE than naive (negative result)."""
    start_d = date.fromisoformat(start)

    def f(i):
        return 2.0 if (15 <= i < 45 or 75 <= i < n_days) else 1.0

    base_rows, harm_rows = [], []
    for i in range(n_days):
        d = (start_d + timedelta(days=i)).isoformat()
        peak = 10.0 if i not in (14, 44, 74) else 60.0  # one planted peak per third
        modis = peak + 0.1 * i
        viirs = modis / R_TRUE * f(i)
        predicted = modis * (3.0 if bad_b2 else 1.0) * (f(i) if bad_b2 else 1.0)
        base_rows.append({"date": d, "daynight": "day", "role": "test", "source_flag": "x",
                          "modis_frp_sum_mw": round(modis, 6), "viirs_frp_sum_mw": round(viirs, 6),
                          "B0_naive_splice_mw": round(viirs, 6), "B1_ratio_pred_mw": round(modis, 6)})
        harm_rows.append({"date": d, "daynight": "day", "role": "test", "source_flag": "x",
                          "n_cells_predicted": 2, "observed_modis_mw": round(modis, 6),
                          "predicted_b2_mw": round(predicted, 6), "lo_mw": round(predicted * 0.8, 6),
                          "hi_mw": round(predicted * 1.2, 6), "flags": ""})
    return base_rows, harm_rows


def write_csvs(rows_b, rows_h):
    tmp = Path(tempfile.mkdtemp(prefix="c05_stress_"))
    for name, rows, fields in (("baseline_series.csv", rows_b, list(rows_b[0])),
                               ("harmonized_daily.csv", rows_h, list(rows_h[0]))):
        with (tmp / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return tmp


def check_list():
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # -- 1. planted jump: perfect B2 removes the artifact -------------------------
    rows_b, rows_h = build_series()
    tmp = write_csvs(rows_b, rows_h)
    result = splice_stress.run(tmp / "baseline_series.csv", tmp / "harmonized_daily.csv",
                               tmp, "synthetic", run_ts="20261114T1500Z")
    manifest = result["manifest"]
    check("stress run ok with 3 predetermined transitions",
          manifest["status"] == "ok" and len(manifest["tests"]) == 3, f"got {manifest['status']}")
    ok_tests = [t for t in manifest["tests"] if t["status"] == "ok"]
    check("all three windows valid (in-span, >=70% paired retrieval)",
          len(ok_tests) == 3 and all(t["window_fraction"] >= 0.70 for t in ok_tests))
    check("transitions sit on the planted segment peaks",
          [t["transition_date"] for t in ok_tests]
          == ["2021-01-15", "2021-02-14", "2021-03-16"],
          f"got {[t.get('transition_date') for t in manifest['tests']]}")
    check("naive splice shows the artifact (|error_naive| large)",
          all(abs(t["error_naive"]) > 0.2 for t in ok_tests),
          f"got {[t['error_naive'] for t in ok_tests]}")
    check("perfect B2 removes it (|error_harmonized| ~ 0)",
          all(abs(t["error_harmonized"]) < 0.05 for t in ok_tests),
          f"got {[t['error_harmonized'] for t in ok_tests]}")
    check("error_ratio << 1 for the good harmonization",
          all(t["error_ratio"] < 0.3 for t in ok_tests),
          f"got {[t['error_ratio'] for t in ok_tests]}")
    check("truth shift ~ 0 on smooth continued MODIS",
          all(abs(t["shift_truth_continued_modis"]["value"]) < 0.35 for t in ok_tests))

    # -- 2. negative result stays visible ------------------------------------------
    rows_b2, rows_h2 = build_series(bad_b2=True)
    tmp2 = write_csvs(rows_b2, rows_h2)
    result2 = splice_stress.run(tmp2 / "baseline_series.csv", tmp2 / "harmonized_daily.csv",
                                tmp2, "synthetic", run_ts="20261114T1500Z")
    bad_tests = [t for t in result2["manifest"]["tests"] if t["status"] == "ok"]
    check("bad B2 -> error_ratio >= 1 reported as NEGATIVE RESULT, never hidden",
          bad_tests and all(t["error_ratio"] >= 1 for t in bad_tests)
          and all("NEGATIVE" in t["interpretation"] for t in bad_tests),
          f"got {[t.get('error_ratio') for t in bad_tests]}")

    # -- 3. short history -> honest deferred ----------------------------------------
    rows_b3, rows_h3 = build_series(n_days=20)
    tmp3 = write_csvs(rows_b3, rows_h3)
    result3 = splice_stress.run(tmp3 / "baseline_series.csv", tmp3 / "harmonized_daily.csv",
                                tmp3, "synthetic", run_ts="20261114T1500Z")
    check("short held-out span -> all 3 slots deferred with exact shortfall",
          result3["manifest"]["status"] == "deferred"
          and len(result3["manifest"]["tests"]) == 3
          and all(t["status"] == "deferred" and "too short" in t["reason"]
                  for t in result3["manifest"]["tests"]))

    # -- 4. no manufactured p-values -------------------------------------------------
    check("changepoint significance recorded as not_implemented",
          manifest["changepoint_significance"].startswith("not_implemented"))
    check("no p-value anywhere in the manifest",
          "p_value" not in json.dumps(manifest).lower())

    # -- 5. absent artifacts -> deferred ----------------------------------------------
    result4 = splice_stress.run(tmp / "missing.csv", tmp / "missing2.csv", tmp, "riau")
    check("absent upstream artifacts -> deferred", result4["manifest"]["status"] == "deferred")

    return checks


def _report(checks):
    failed = [(n, d) for n, ok_, d in checks if not ok_]
    for name, okv, detail in checks:
        print(f"[{'PASS' if okv else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not okv else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def test_splice_stress():
    failed = [(n, d) for n, ok_, d in check_list() if not ok_]
    assert not failed, f"C-05 splice-stress violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(check_list()))
