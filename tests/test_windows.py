"""C-06 contract test — critical windows (pipeline/windows.py).

Threshold percentile, contiguous-run detection, Dec->Jan wrapping, short-run
exclusion, years_active rule (DEC-3), honest deferred/insufficient paths.

Run standalone:  python tests/test_windows.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import calendar_climatology as calendar, windows  # noqa: E402
from tests.test_calendar import harmonized_rows, write_csv  # noqa: E402

REAL_CLIM = None  # real fixture path checked dynamically below


def check_list():
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # -- find_windows: runs, short-run exclusion, Dec-Jan wrap -------------------
    flat = [1.0] * 360
    curve = flat + [5.0] * 6  # positions 361..366 above any threshold of this curve
    thr = float(__import__("numpy").quantile(__import__("numpy").array(curve), 0.75))
    found = windows.find_windows(curve, thr)
    check("contiguous run at year end detected (6 days)",
          len(found) == 1 and found[0]["length_days"] == 6
          and found[0]["start_position"] == 361 and found[0]["end_position"] == 366
          and found[0]["wraps_dec_jan"] is False, f"got {found}")
    # craft a genuine Dec->Jan wrap: high at 365,366,1,2,3 within a low curve
    wrap_curve = [1.0] * 360 + [5.0] * 6  # positions 361..366
    wrap_curve[0] = 6.0; wrap_curve[1] = 6.0; wrap_curve[2] = 6.0  # positions 1,2,3
    thr2 = float(__import__("numpy").quantile(__import__("numpy").array(wrap_curve), 0.75))
    found2 = windows.find_windows(wrap_curve, thr2)
    wrap_win = [w for w in found2 if w["wraps_dec_jan"]]
    check("Dec->Jan window wraps contiguously (positions 361..3 -> one run)",
          len(wrap_win) == 1 and wrap_win[0]["start_position"] == 361
          and wrap_win[0]["end_position"] == 3 and wrap_win[0]["length_days"] == 9,
          f"got {found2}")
    # short runs excluded
    short_curve = [1.0] * 360 + [5.0, 5.0] + [1.0] * 4  # only 2 above
    thr3 = float(__import__("numpy").quantile(__import__("numpy").array(short_curve), 0.75))
    check("runs shorter than 3 days are not windows",
          all(w["length_days"] >= 3 for w in windows.find_windows(short_curve, thr3)))

    # -- integration through calendar.run on the seasonal synthetic ----------------
    tmp = Path(tempfile.mkdtemp(prefix="c06win_"))
    write_csv(tmp / "harmonized.csv", harmonized_rows())
    cal_result = calendar.run(tmp / "harmonized.csv", None, tmp, "synthetic")
    win_result = windows.run(tmp, tmp)
    manifest = win_result["manifest"]
    check("windows run ok on the seasonal synthetic climatology",
          manifest["status"] == "ok", f"got {manifest['status']}: {manifest.get('reason')}")
    check("threshold = 75th percentile of smoothed curve, stated as descriptive",
          manifest["threshold"]["percentile_of_smoothed_curve"] == 75
          and "NOT a safety threshold" in manifest["threshold"]["meaning"])
    check("seasonal curve yields >=1 window inside mid-year",
          manifest["n_windows"] >= 1
          and all(w["length_days"] >= 3 for w in manifest["windows"]),
          f"got {manifest['windows']}")
    activity = manifest["activity"]
    check("years_active uses DEC-3 provisional rule and stays inside eligible years",
          set(activity["years_active"]) <= set(manifest["years_eligible"])
          and "DEC-3 PROVISIONAL" in activity["rule"], f"got {activity['years_active']}")
    check("years_eligible carried from climatology (denominator published)",
          manifest["years_eligible"] == ["2021", "2022", "2023"])

    # -- insufficient climatology -> no defensible windows ---------------------------
    one_year = [r for r in harmonized_rows() if r["date"].startswith("2021")]
    tmp2 = Path(tempfile.mkdtemp(prefix="c06win_"))
    write_csv(tmp2 / "harmonized.csv", one_year)
    calendar.run(tmp2 / "harmonized.csv", None, tmp2, "synthetic")
    result_ins = windows.run(tmp2, tmp2)
    check("sparse climatology (<30 positions) -> insufficient_data, raw series note kept",
          result_ins["manifest"]["status"] == "insufficient_data"
          and "raw accepted series retained" in result_ins["manifest"]["raw_series_note"])

    # -- deferred when calendar artifacts absent --------------------------------------
    result_def = windows.run(Path(tempfile.mkdtemp(prefix="c06win_")), None)
    check("absent calendar artifacts -> deferred", result_def["manifest"]["status"] == "deferred")

    # -- real Riau file: windows status consistent with upstream calendar state -------
    real = Path(__file__).resolve().parents[1] / "artifacts/riau/climatology.json"
    if real.exists():
        result_real = windows.run(real.parent, real.parent)
        clim = json.loads(real.read_text())
        expected_ok = clim.get("status") == "ok" and len(clim.get("years_eligible", [])) >= 2
        check("real Riau: windows status consistent with calendar upstream state",
              (result_real["manifest"]["status"] == "ok") == expected_ok,
              f"windows={result_real['manifest']['status']}, clim={clim.get('status')}")
    return checks


def _report(checks):
    failed = [(n, d) for n, ok_, d in checks if not ok_]
    for name, okv, detail in checks:
        print(f"[{'PASS' if okv else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not okv else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def test_windows():
    failed = [(n, d) for n, ok_, d in check_list() if not ok_]
    assert not failed, f"C-06 windows violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(check_list()))
