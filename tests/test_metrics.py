"""C-05 contract test — metrics with N/A policies (pipeline/metrics.py).

Known-answer checks on tiny synthetic series + the identical-held-out-rows
guarantee + honest deferred status when upstream artifacts are absent.

Run standalone:  python tests/test_metrics.py
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import metrics  # noqa: E402


def check_list():
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # -- mean log ratio bias: exact on tiny case --------------------------------
    import math
    r = metrics.mean_log_ratio_bias([10.0, 100.0], [20.0, 200.0])
    expected = (math.log1p(10) - math.log1p(20) + math.log1p(100) - math.log1p(200)) / 2
    check("mean log-ratio bias exact", abs(r["value"] - expected) < 1e-6, f"got {r}")

    # -- sMAPE: exact; zero denominators excluded and counted --------------------
    r = metrics.smape([1.0, 2.0], [2.0, 4.0])
    check("sMAPE exact (2*(1/3) both rows -> 0.666667)",
          abs(r["value"] - 0.666667) < 1e-5 and r["n"] == 2, f"got {r}")
    r = metrics.smape([0.0, 1.0], [0.0, 2.0])  # first row: both zero
    check("sMAPE zero-denominator row excluded and counted",
          abs(r["value"] - 2 * 1.0 / 3.0) < 1e-6 and r["n_excluded"] == 1, f"got {r}")
    r = metrics.smape([0.0], [0.0])
    check("sMAPE all-zero -> N/A, never infinity or fabricated zero",
          r["value"] == "N/A" and "zero" in r["reason"], f"got {r}")

    # -- MAPE: zero-actual excluded, counted --------------------------------------
    r = metrics.mape([1.0, 2.0, 0.0], [2.0, 4.0, 5.0])
    check("MAPE excludes zero actuals with count",
          abs(r["value"] - 1.0) < 1e-9 and r["n"] == 2 and r["n_excluded"] == 1, f"got {r}")

    # -- correlations --------------------------------------------------------------
    check("Pearson = 1 on a perfect line",
          abs(metrics.pearson([1, 2, 3], [2, 4, 6])["value"] - 1.0) < 1e-9)
    check("Spearman = 1 on any monotone transform",
          abs(metrics.spearman([1, 2, 3, 4], [10, 100, 200, 900])["value"] - 1.0) < 1e-9)
    check("Pearson constant series -> N/A",
          metrics.pearson([5, 5, 5], [1, 2, 3])["value"] == "N/A")
    check("Pearson <2 points -> N/A", metrics.pearson([1], [2])["value"] == "N/A")
    r = metrics.spearman([1, 2, 2, 4], [1, 2, 2, 4])
    check("Spearman handles ties via average ranks (1 here)",
          abs(r["value"] - 1.0) < 1e-9, f"got {r}")

    # -- log-space R2 ----------------------------------------------------------------
    check("log-R2 = 1 on perfect prediction",
          abs(metrics.log_space_r2([1, 10, 100], [1, 10, 100])["value"] - 1.0) < 1e-9)
    check("log-R2 constant observed -> N/A",
          metrics.log_space_r2([5, 5, 5], [1, 2, 3])["value"] == "N/A",
          f"got {metrics.log_space_r2([5, 5, 5], [1, 2, 3])}")
    r = metrics.log_space_r2([1, 10, 100], [10, 1, 1000])
    check("log-R2 in [0,1]-ish and computable on anti-correlated data",
          isinstance(r["value"], float), f"got {r}")

    # -- KS + Wasserstein: known values ------------------------------------------------
    check("KS = 1 on disjoint support",
          abs(metrics.ks_statistic([1, 2, 3, 4], [5, 6, 7, 8])["value"] - 1.0) < 1e-9)
    check("KS = 0 on identical samples",
          abs(metrics.ks_statistic([1, 2, 3], [1, 2, 3])["value"]) < 1e-9)
    r = metrics.ks_statistic([1, 2, 3, 4], [3, 4, 5, 6])
    check("KS = 0.5 on half-overlap", abs(r["value"] - 0.5) < 1e-9, f"got {r}")
    check("Wasserstein = 1 on shifted blocks",
          abs(metrics.wasserstein_distance([0, 0, 1, 1], [1, 1, 2, 2])["value"] - 1.0) < 1e-9)

    # -- calendar pattern correlation ---------------------------------------------
    months12 = [f"2022-{m:02d}-10" for m in range(1, 13)]
    r = metrics.calendar_pattern_correlation(months12, list(range(12)), list(range(0, 24, 2)))
    check("calendar correlation = 1 on proportional monthly means",
          abs(r["value"] - 1.0) < 1e-9 and "months:" in r["reason"], f"got {r}")
    r = metrics.calendar_pattern_correlation(months12[:5], list(range(5)), list(range(5)))
    check("calendar correlation <6 months -> N/A", r["value"] == "N/A", f"got {r}")

    # -- interval coverage ------------------------------------------------------------
    r = metrics.interval_coverage([5.0, 15.0], [0.0, 10.0], [10.0, 20.0])
    check("interval coverage = 1.0 when both inside",
          abs(r["value"] - 1.0) < 1e-9 and r["n"] == 2, f"got {r}")
    r = metrics.interval_coverage([5.0, 15.0], [0.0, 10.0], [4.0, 20.0])
    check("interval coverage = 0.5 when half miss",
          abs(r["value"] - 0.5) < 1e-9 and r["n"] == 2, f"got {r}")
    r = metrics.interval_coverage([5.0], [None], [None])
    check("coverage with missing bounds counted, not silently zero",
          r["value"] == "N/A" and r["n_excluded"] == 1, f"got {r}")

    # -- weekly aggregation ------------------------------------------------------------
    wd, wv = metrics.weekly_series(
        ["2022-01-03", "2022-01-05", "2022-01-10"], [1.0, 2.0, 8.0])
    check("weekly ISO sums: 2022-01-03 is Monday of ISO W01 -> W01=3, W02=8",
          wd == ["2022-W01", "2022-W02"] and wv == [3.0, 8.0], f"got {wd},{wv}")

    # -- evaluate(): identical held-out rows enforced ----------------------------------
    def write_csv(path, rows, fields):
        with open(path, "w", newline="", encoding="utf-8") as h:
            w = csv.DictWriter(h, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    base_fields = ["date", "daynight", "role", "source_flag", "modis_frp_sum_mw",
                   "viirs_frp_sum_mw", "B0_naive_splice_mw", "B1_ratio_pred_mw"]
    harm_fields = ["date", "daynight", "role", "source_flag", "n_cells_predicted",
                   "observed_modis_mw", "predicted_b2_mw", "lo_mw", "hi_mw", "flags"]
    base_rows, harm_rows = [], []
    for i in range(1, 41):  # 40 held-out days, 2021
        day = (2021, 1, i) if i <= 31 else (2021, 2, i - 31)
        d = f"{day[0]}-{day[1]:02d}-{day[2]:02d}"
        modis = 5.0 + i * 0.5
        viirs = modis / 1.25 * (2.0 if i > 20 else 1.0)  # planted raw jump after day 20
        base_rows.append({"date": d, "daynight": "day", "role": "test", "source_flag": "x",
                          "modis_frp_sum_mw": modis, "viirs_frp_sum_mw": viirs,
                          "B0_naive_splice_mw": viirs, "B1_ratio_pred_mw": modis})
        harm_rows.append({"date": d, "daynight": "day", "role": "test", "source_flag": "x",
                          "n_cells_predicted": 2, "observed_modis_mw": modis,
                          "predicted_b2_mw": modis, "lo_mw": modis * 0.8,
                          "hi_mw": modis * 1.2, "flags": ""})
    tmp = Path(tempfile.mkdtemp(prefix="c05_test_"))
    write_csv(tmp / "baseline_series.csv", base_rows, base_fields)
    write_csv(tmp / "harmonized_daily.csv", harm_rows, harm_fields)
    result = metrics.evaluate(tmp / "baseline_series.csv", tmp / "harmonized_daily.csv")
    check("evaluate(): identical held-out rows -> status ok, 40 days",
          result["status"] == "ok" and result["n_heldout_days"] == 40, f"got {result['status']}")
    check("all 12 required metrics present for each method",
          all(sorted(result["metrics"][m]) == sorted(metrics.REQUIRED_METRICS)
              for m in ("b0", "b1", "b2")),
          f"got {sorted(result['metrics']['b0'])}")
    check("perfect B2 -> coverage 1.0 and zero bias; naive splice shows the artifact",
          abs(result["metrics"]["b2"]["interval_coverage_empirical"]["value"] - 1.0) < 1e-9
          and abs(result["metrics"]["b2"]["mean_log_ratio_bias"]["value"]) < 1e-6
          and abs(result["metrics"]["b0"]["mean_log_ratio_bias"]["value"]
                  - result["metrics"]["b2"]["mean_log_ratio_bias"]["value"]) > 0.05,
          f"b0={result['metrics']['b0']['mean_log_ratio_bias']} "
          f"b2={result['metrics']['b2']['mean_log_ratio_bias']}")
    check("b0/b1 coverage marked not-applicable (no bounds published)",
          result["metrics"]["b0"]["interval_coverage_empirical"]["value"] == "N/A")
    # mismatched rows must hard-fail (identical-rows guarantee)
    harm_rows[5]["observed_modis_mw"] = 999.0
    write_csv(tmp / "harmonized_bad.csv", harm_rows, harm_fields)
    try:
        metrics.evaluate(tmp / "baseline_series.csv", tmp / "harmonized_bad.csv")
        check("observed-value disagreement between artifacts hard-fails", False)
    except ValueError as exc:
        check("observed-value disagreement between artifacts hard-fails", "disagree" in str(exc))

    # -- deferred path when artifacts absent ---------------------------------------------
    result2 = metrics.run(tmp / "missing_b.csv", tmp / "missing_h.csv", None, tmp, "riau")
    check("absent upstream artifacts -> honest deferred, not failed",
          result2["manifest"]["status"] == "deferred"
          and set(metrics.REQUIRED_METRICS) == set(result2["manifest"]["required_metrics"]))

    # -- LOYO runs on real pairs machinery ------------------------------------------------
    pairs = [{"aoi_id": "s", "cell_id": "R0C1000", "date": f"{y}-0{m}-15", "daynight": "day",
              "modis_frp_sum_mw": 10.0, "viirs_frp_sum_mw": 8.0, "viirs_detection_count": 2,
              "state": "matched_signal", "fitting_eligible": "true"}
             for y in (2018, 2019, 2020, 2021) for m in range(1, 10)]
    loyo = metrics.loyo_summary(pairs, {"2018", "2019", "2020"})
    check("LOYO training-internal: folds for each train year, ok status",
          loyo["status"] == "ok" and len(loyo["folds"]) == 3
          and all(f["status"] == "ok" for f in loyo["folds"]), f"got {loyo}")

    return checks


def _report(checks):
    failed = [(n, d) for n, ok_, d in checks if not ok_]
    for name, okv, detail in checks:
        print(f"[{'PASS' if okv else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not okv else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def test_metrics():
    failed = [(n, d) for n, ok_, d in check_list() if not ok_]
    assert not failed, f"C-05 metrics violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(check_list()))
