"""C-06 contract test — calendar climatology (pipeline/calendar.py).

Leap-day handling, index denominator freezing, gap-vs-zero distinction,
circular smoothing across the 366->1 seam, eligibility rule, honest
insufficient_data/deferred paths.

Run standalone:  python tests/test_calendar.py
"""
from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import calendar_climatology as calendar  # noqa: E402

REAL_HARM = Path(__file__).resolve().parents[1] / "artifacts/riau/harmonized_daily.csv"


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def harmonized_rows():
    """FIXTURE_SYNTHETIC: daily 2021-01-01..2023-12-31 (role test, seasonal
    signal) + training days 2020-07-01..2020-10-08 (role train, known values)
    + ONE leap day 2024-02-29 (partial era 2024)."""
    rows = []
    d = date(2020, 7, 1)
    while d <= date(2020, 10, 8):
        rows.append({"date": d.isoformat(), "daynight": "day", "role": "train",
                     "source_flag": "harmonized_viirs", "n_cells_predicted": 2,
                     "observed_modis_mw": 20.0, "predicted_b2_mw": 20.0,
                     "lo_mw": 16.0, "hi_mw": 24.0, "flags": ""})
        d += timedelta(days=1)
    d = date(2021, 1, 1)
    while d <= date(2023, 12, 31):
        doy = d.timetuple().tm_yday
        observed = 10.0 + 8.0 * math.sin(2 * math.pi * doy / 365.0)  # seasonal, >0
        rows.append({"date": d.isoformat(), "daynight": "day", "role": "test",
                     "source_flag": "harmonized_viirs", "n_cells_predicted": 2,
                     "observed_modis_mw": round(observed, 6),
                     "predicted_b2_mw": round(observed / 1.25, 6),
                     "lo_mw": round(observed / 1.25 * 0.9, 6),
                     "hi_mw": round(observed / 1.25 * 1.1, 6), "flags": ""})
        d += timedelta(days=1)
    rows.append({"date": "2024-02-29", "daynight": "day", "role": "test",
                 "source_flag": "harmonized_viirs", "n_cells_predicted": 2,
                 "observed_modis_mw": 44.0, "predicted_b2_mw": 35.2,
                 "lo_mw": 30.0, "hi_mw": 40.0, "flags": ""})
    return rows


def unit_rows():
    """FIXTURE_SYNTHETIC: pre-era Aqua-only days (2016), Terra row excluded."""
    return [
        {"aoi_id": "s", "cell_id": "R0C1000", "date": "2016-09-01", "daynight": "day",
         "family": "modis", "source": "MODIS_SP", "satellite": "Aqua", "version": "6.1",
         "detection_count": 1, "frp_sum_mw": 12.0, "frp_max_mw": 12.0, "mean_scan": 1.0,
         "conf_nominal": 1, "conf_low": 0, "conf_high": 0, "conf_unknown": 0},
        {"aoi_id": "s", "cell_id": "R0C1000", "date": "2016-09-02", "daynight": "day",
         "family": "modis", "source": "MODIS_SP", "satellite": "Terra", "version": "6.1",
         "detection_count": 1, "frp_sum_mw": 99.0, "frp_max_mw": 99.0, "mean_scan": 1.0,
         "conf_nominal": 1, "conf_low": 0, "conf_high": 0, "conf_unknown": 0},
    ]


def check_list():
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # -- position mapping ---------------------------------------------------------
    check("position mapping: Jan1=1, Feb29=60, Dec31=366",
          calendar.position_of(1, 1) == 1 and calendar.position_of(2, 29) == 60
          and calendar.position_of(12, 31) == 366)
    check("month_day_of round-trips", calendar.month_day_of(60) == (2, 29)
          and calendar.month_day_of(366) == (12, 31))

    # -- accepted series: source policy, no blending, gaps absent ------------------
    tmp = Path(tempfile.mkdtemp(prefix="c06_test_"))
    write_csv(tmp / "harmonized.csv", harmonized_rows())
    write_csv(tmp / "units.csv", unit_rows())
    result = calendar.run(tmp / "harmonized.csv", tmp / "units.csv", tmp, "synthetic")
    manifest, series = result["manifest"], result["series"]
    check("calendar status ok on 3 full eligible years", manifest["status"] == "ok",
          f"got {manifest['status']}: {manifest.get('reason')}")
    flags = {s["date"]: s["source_flag"] for s in series}
    check("pre-era days = observed Aqua (F-14), never Terra",
          flags.get("2016-09-01") == "observed_modis" and "2016-09-02" not in flags)
    check("era days = harmonized VIIRS estimate", flags.get("2021-01-01") == "harmonized_viirs")
    check("gaps are absent, never zero-filled", all(s["value_mw"] is not None for s in series)
          and "2016-09-03" not in flags)

    # -- index denominator frozen from training -------------------------------------
    train_vals = [20.0] * len([r for r in harmonized_rows() if r["role"] == "train"])
    denominator = manifest["index"]["denominator_mw"]
    check("denominator = P95 of training daily MODIS totals (frozen, recorded)",
          denominator == 20.0 and manifest["index"]["available"] is True
          and "role=train" in manifest["index"]["denominator_frozen_from"], f"got {manifest['index']}")
    sample = next(s for s in series if s["date"] == "2021-01-01")
    expected_idx = math.log1p(sample["value_mw"]) / math.log1p(denominator)
    check("index value = log1p(value)/log1p(frozen denominator), numeric",
          abs(sample["index"] - expected_idx) < 1e-5, f"got {sample['index']}")

    # -- Feb 29: leap year only, sparse state, never missing-data --------------------
    cal = {(int(r["position"])): r for r in result["calendar"]}
    feb29 = cal[60]
    check("Feb 29 populated ONLY by the leap year (n_years=1, sparse — not missing)",
          feb29["day"] == 29 and feb29["month"] == 2 and feb29["n_years"] == 1
          and feb29["state"] == "sparse" and feb29["years"] == "2024", f"got {feb29}")
    check("calendar has all 366 positions",
          len(result["calendar"]) == 366)

    # -- circular smoothing across the 366->1 seam ------------------------------------
    raw = [r["index_median_raw"] for r in result["calendar"]]
    sm = [r["index_median_smoothed"] for r in result["calendar"]]
    seam_pull = sm[0] is not None and sm[0] != raw[0]
    check("smoothing mixes neighbours across the 366->1 seam",
          seam_pull and all(v is not None for v in sm), f"sm[0]={sm[0]} raw[0]={raw[0]}")

    # -- eligibility rule (calendar-era days): partial years cannot pass ---------------
    # 2024 (1/60 days), 2016 (1/122 days) AND 2020 (100/366 — only Jul-Oct delivered)
    # all fall below 60%; full years 2021-2023 are eligible.
    check("eligibility: full years eligible, partial years (2024/2016/2020) not",
          set(manifest["years_eligible"]) == {"2021", "2022", "2023"}
          and not {"2024", "2016", "2020"} & set(manifest["years_eligible"]),
          f"got {manifest['years_eligible']}")
    check("missing years never listed as inactive (absent, not zero)",
          "2015" not in manifest["years_in_series"]
          and "inactive" not in json.dumps(manifest))

    # -- all-zero training denominator -> index unavailable, raw MW retained ----------
    zero_rows = []
    d = date(2020, 7, 1)
    while d <= date(2020, 10, 8):
        zero_rows.append({"date": d.isoformat(), "daynight": "day", "role": "train",
                          "source_flag": "harmonized_viirs", "n_cells_predicted": 2,
                          "observed_modis_mw": 0.0, "predicted_b2_mw": 0.0,
                          "lo_mw": 0.0, "hi_mw": 0.0, "flags": ""})
        d += timedelta(days=1)
    zero_rows += [r for r in harmonized_rows() if r["role"] == "test"]
    tmp2 = Path(tempfile.mkdtemp(prefix="c06_test_"))
    write_csv(tmp2 / "harmonized.csv", zero_rows)
    result2 = calendar.run(tmp2 / "harmonized.csv", None, tmp2, "synthetic")
    check("non-positive denominator -> index unavailable, raw MW shown (F-17)",
          result2["manifest"]["index"]["available"] is False
          and all(s["index"] is None for s in result2["series"])
          and all(s["value_mw"] is not None for s in result2["series"]))

    # -- honest deferred / insufficient ----------------------------------------------
    result3 = calendar.run(tmp / "missing.csv", None, tmp, "riau")
    check("absent C-04 artifact -> deferred (not failed)",
          result3["manifest"]["status"] == "deferred")
    one_year = [r for r in harmonized_rows() if r["date"].startswith("2021")]
    tmp3 = Path(tempfile.mkdtemp(prefix="c06_test_"))
    write_csv(tmp3 / "harmonized.csv", one_year)
    result4 = calendar.run(tmp3 / "harmonized.csv", None, tmp3, "synthetic")
    check("single eligible year -> insufficient_data, raw series retained",
          result4["manifest"]["status"] == "insufficient_data"
          and Path(result4["outputs"]["series"]).exists())

    # -- real Riau file: status consistent with eligibility (era evolves: fixture
    #    -> deferred; full era -> ok). Invariant: ok iff >=2 eligible years, and
    #    a sparse sample is never shown as a normal baseline either way.
    if REAL_HARM.exists():
        result5 = calendar.run(str(REAL_HARM), None, tmp, "riau")
        m5 = result5["manifest"]
        st = m5["status"]
        n_eligible = len(m5.get("years_eligible", []))
        check("real Riau harmonized series: status ok iff >=2 eligible years",
              (st == "ok") == (n_eligible >= calendar.MIN_ELIGIBLE_YEARS)
              and st in {"ok", "insufficient_data"},
              f"status={st}, eligible={m5.get('years_eligible')}")
    return checks


def _report(checks):
    failed = [(n, d) for n, ok_, d in checks if not ok_]
    for name, okv, detail in checks:
        print(f"[{'PASS' if okv else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not okv else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def test_calendar():
    failed = [(n, d) for n, ok_, d in check_list() if not ok_]
    assert not failed, f"C-06 calendar violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(check_list()))
