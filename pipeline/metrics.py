"""EmberLine C-05 — held-out metrics with N/A policies (PROTO-C01-v0.9, F-15).

Owner: team member C. Contract tests: tests/test_metrics.py.

Consumes the C-03 baseline series and the C-04 harmonized daily series (both
artifacts), asserts the SAME held-out AOI-day rows feed B0/B1/B2, and evaluates
every metric in the frozen menu. Every metric returns a machine-readable result:
{"value": float | "N/A", "reason": str, "n": int, "n_excluded": int}.

N/A policy (F-15): zero denominators, constant series, empty groups and zero
support yield {"value": "N/A", "reason": ...} — never infinity, never a
fabricated zero. Sample sizes and exclusions travel with every result.

MODIS is the reference measurement throughout — never fire ground truth.
Weekly resolution = ISO-week sums of the same held-out days. Interval coverage
applies to B2 only (the only method that publishes bounds). The leave-one-year-
out summary is training-internal (refits exclude one year, evaluate on it) and
never touches the frozen held-out era.

If the upstream artifacts are missing or their outcome was insufficient_data,
the whole evaluation is recorded as `deferred` with the exact shortfall — an
uncomputable test is never renamed a pass.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date as _date
from pathlib import Path

import numpy as np

from pipeline.baselines import PROTOCOL_VERSION, load_pairs
from pipeline import harmonize

REQUIRED_METRICS = [
    "mean_log_ratio_bias", "smape", "mape_zero_actual_excluded",
    "pearson_daily", "spearman_daily", "pearson_weekly", "spearman_weekly",
    "log_space_r2", "ks_statistic", "wasserstein_distance",
    "calendar_pattern_correlation", "interval_coverage_empirical",
]
TOL = 1e-9


def _num(v) -> float | None:
    return None if v in (None, "") else float(v)


def na(reason: str, n: int = 0, n_excluded: int = 0) -> dict:
    return {"value": "N/A", "reason": reason, "n": n, "n_excluded": n_excluded}


def ok(value: float, n: int, n_excluded: int = 0, reason: str = "") -> dict:
    return {"value": round(float(value), 6), "reason": reason, "n": n, "n_excluded": n_excluded}


def mean_log_ratio_bias(obs: list[float], pred: list[float]) -> dict:
    pairs = [(o, p) for o, p in zip(obs, pred) if o is not None and p is not None]
    if not pairs:
        return na("no valid rows")
    diffs = [float(np.log1p(o) - np.log1p(p)) for o, p in pairs]
    return ok(float(np.mean(diffs)), len(pairs))


def smape(obs: list[float], pred: list[float]) -> dict:
    valid, excluded = [], 0
    for o, p in zip(obs, pred):
        if o is None or p is None:
            excluded += 1
            continue
        denom = abs(o) + abs(p)
        if denom == 0:  # both zero: denominator undefined -> excluded, counted
            excluded += 1
            continue
        valid.append(2 * abs(p - o) / denom)
    if not valid:
        return na("all rows excluded (zero denominators)", len(obs), excluded)
    return ok(float(np.mean(valid)), len(valid), excluded)


def mape(obs: list[float], pred: list[float]) -> dict:
    valid, excluded = [], 0
    for o, p in zip(obs, pred):
        if o is None or p is None:
            excluded += 1
        elif o == 0:  # zero-actual rows excluded by policy, counted
            excluded += 1
        else:
            valid.append(abs(p - o) / abs(o))
    if not valid:
        return na("all rows excluded (zero actuals)", len(obs), excluded)
    return ok(float(np.mean(valid)), len(valid), excluded)


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # average ranks for ties
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float], x_label: str, y_label: str) -> dict:
    if len(xs) < 2:
        return na("fewer than 2 points", len(xs))
    x, y = np.array(xs), np.array(ys)
    if float(x.std()) == 0 or float(y.std()) == 0:
        return na(f"constant series ({x_label} or {y_label})", len(xs))
    return ok(float(np.corrcoef(x, y)[0, 1]), len(xs))


def pearson(obs: list[float], pred: list[float]) -> dict:
    pairs = [(o, p) for o, p in zip(obs, pred) if o is not None and p is not None]
    return _pearson([p[0] for p in pairs], [p[1] for p in pairs], "observed", "predicted")


def spearman(obs: list[float], pred: list[float]) -> dict:
    pairs = [(o, p) for o, p in zip(obs, pred) if o is not None and p is not None]
    if not pairs:
        return na("no valid rows")
    return _pearson(_ranks([p[0] for p in pairs]), _ranks([p[1] for p in pairs]),
                    "observed ranks", "predicted ranks")


def log_space_r2(obs: list[float], pred: list[float]) -> dict:
    pairs = [(o, p) for o, p in zip(obs, pred) if o is not None and p is not None]
    if not pairs:
        return na("no valid rows")
    lo = np.array([np.log1p(max(0.0, p[0])) for p in pairs])
    lp = np.array([np.log1p(max(0.0, p[1])) for p in pairs])
    sst = float(((lo - lo.mean()) ** 2).sum())
    if sst <= 1e-12:  # exact-zero variance is unreachable in floats for identical values
        return na("constant observed series in log space", len(pairs))
    sse = float(((lo - lp) ** 2).sum())
    return ok(1.0 - sse / sst, len(pairs))


def ks_statistic(obs: list[float], pred: list[float]) -> dict:
    pairs = [(o, p) for o, p in zip(obs, pred) if o is not None and p is not None]
    if not pairs:
        return na("no valid rows")
    a = np.sort(np.array([p[0] for p in pairs]))
    b = np.sort(np.array([p[1] for p in pairs]))
    all_vals = np.concatenate([a, b])
    cdf_a = np.searchsorted(a, all_vals, side="right") / len(a)
    cdf_b = np.searchsorted(b, all_vals, side="right") / len(b)
    return ok(float(np.max(np.abs(cdf_a - cdf_b))), len(pairs))


def wasserstein_distance(obs: list[float], pred: list[float]) -> dict:
    pairs = [(o, p) for o, p in zip(obs, pred) if o is not None and p is not None]
    if not pairs:
        return na("no valid rows")
    a = np.sort(np.array([p[0] for p in pairs]))
    b = np.sort(np.array([p[1] for p in pairs]))
    return ok(float(np.mean(np.abs(a - b))), len(pairs))


def calendar_pattern_correlation(dates: list[str], obs: list[float], pred: list[float]) -> dict:
    """Month-of-year mean agreement on the held-out rows (climatology proxy)."""
    by_month: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 0])
    for d, o, p in zip(dates, obs, pred):
        if o is None or p is None:
            continue
        m = int(d[5:7])
        by_month[m][0] += o
        by_month[m][1] += p
        by_month[m][2] += 1
    if len(by_month) < 6:
        return na("fewer than 6 distinct months in held-out rows", len(by_month))
    months = sorted(by_month)
    mo = [by_month[m][0] / by_month[m][2] for m in months]
    mp = [by_month[m][1] / by_month[m][2] for m in months]
    result = _pearson(mo, mp, "observed monthly means", "predicted monthly means")
    if result["value"] == "N/A":
        return result
    result["reason"] = "month-of-year means; months: " + ",".join(f"{m:02d}" for m in months)
    return result


def interval_coverage(obs: list[float], lo: list[float], hi: list[float]) -> dict:
    valid, missing, hits = 0, 0, 0
    for o, l, h in zip(obs, lo, hi):
        if o is None or l is None or h is None:
            missing += 1
            continue
        valid += 1
        hits += 1 if l <= o <= h else 0
    if not valid:
        return na("no interval rows available", len(obs), missing)
    return ok(hits / valid, valid, missing)


def weekly_series(dates: list[str], values: list[float]) -> tuple[list[str], list[float]]:
    sums: dict[tuple[int, int], float] = defaultdict(float)
    for d, v in zip(dates, values):
        if v is None:
            continue
        iso = _date.fromisoformat(d).isocalendar()
        sums[(iso[0], iso[1])] += v
    keys = sorted(sums)
    return [f"{k[0]}-W{k[1]:02d}" for k in keys], [sums[k] for k in keys]


# --------------------------------------------------------------------- runner
def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def evaluate(baselines_csv: Path, harmonized_csv: Path) -> dict:
    base_rows = _read_csv(baselines_csv)
    harm_rows = _read_csv(harmonized_csv)
    base_index = {(r["date"], r["daynight"]): r for r in base_rows}
    keys = sorted(base_index)
    harm_index = {(r["date"], r["daynight"]): r for r in harm_rows}
    if keys != sorted(harm_index):
        raise ValueError("C-03/C-04 series row sets differ — held-out rows must be IDENTICAL "
                         "across B0/B1/B2 (F-15)")
    test_keys = [k for k in keys if base_index[k]["role"] == "test"]
    if not test_keys:
        return {"status": "deferred", "reason": "no held-out AOI-days in the delivered window "
                "(real fixture ends before the frozen test era); metrics deferred, not failed"}

    obs, dates, daynights = [], [], []
    series = {"b0": [], "b1": [], "b2": []}
    lo, hi = [], []
    for key in test_keys:
        b, h = base_index[key], harm_index[key]
        for a, b_ in (("modis_frp_sum_mw", "observed_modis_mw"),):
            if abs(float(b[a]) - float(h[b_])) > 1e-6:
                raise ValueError(f"observed values disagree between artifacts at {key}")
        dates.append(key[0])
        daynights.append(key[1])
        obs.append(float(b["modis_frp_sum_mw"]))
        series["b0"].append(_num(b["B0_naive_splice_mw"]))
        series["b1"].append(_num(b["B1_ratio_pred_mw"]))
        series["b2"].append(_num(h["predicted_b2_mw"]))
        lo.append(_num(h["lo_mw"]))
        hi.append(_num(h["hi_mw"]))

    results: dict[str, dict] = {}
    wk_dates, wk_index = None, None
    for method in ("b0", "b1", "b2"):
        pred = series[method]
        w_dates, w_obs = weekly_series(dates, obs)
        w_pred_labels, w_pred_values = weekly_series(dates, pred)
        if w_pred_labels != w_dates:
            raise ValueError("weekly aggregation produced inconsistent buckets across methods")
        results[method] = {
            "mean_log_ratio_bias": mean_log_ratio_bias(obs, pred),
            "smape": smape(obs, pred),
            "mape_zero_actual_excluded": mape(obs, pred),
            "pearson_daily": pearson(obs, pred),
            "spearman_daily": spearman(obs, pred),
            "pearson_weekly": pearson(w_obs, w_pred_values) if len(w_obs) >= 2 else na("fewer than 2 weeks"),
            "spearman_weekly": spearman(w_obs, w_pred_values) if len(w_obs) >= 2 else na("fewer than 2 weeks"),
            "log_space_r2": log_space_r2(obs, pred),
            "ks_statistic": ks_statistic(obs, pred),
            "wasserstein_distance": wasserstein_distance(obs, pred),
            "calendar_pattern_correlation": calendar_pattern_correlation(dates, obs, pred),
        }
    results["b2"]["interval_coverage_empirical"] = interval_coverage(obs, lo, hi)
    for method in ("b0", "b1"):
        results[method]["interval_coverage_empirical"] = na(
            "not applicable: this method publishes no bounds", len(obs))
    return {
        "status": "ok",
        "n_heldout_days": len(test_keys),
        "heldout_date_span": [test_keys[0][0], test_keys[-1][0]],
        "metrics": results,
        "required_present": sorted(results["b2"]),
    }


def loyo_summary(pairs: list[dict], eligible: set[str]) -> dict:
    """Training-internal leave-one-year-out (never touches the frozen test era)."""
    train_years = sorted({y for y in eligible if y <= harmonize.TRAIN_END})
    folds = []
    for year in train_years:
        reduced = eligible - {year}
        rows_in_year = [r for r in pairs if r["date"][:4] == year
                        and str(r.get("fitting_eligible")).lower() == "true"]
        if not rows_in_year or len({r["date"][:4] for r in pairs
                                    if r["date"][:4] in reduced and r["date"] <= harmonize.TRAIN_END}) < 1:
            folds.append({"fold_year": year, "status": "skipped", "reason": "insufficient fold support"})
            continue
        model = harmonize.fit_b2_rows(
            [r for r in pairs
             if str(r.get("fitting_eligible")).lower() == "true"
             and r["date"][:4] in reduced and r["date"] <= harmonize.TRAIN_END])
        if not rows_in_year or not model:
            folds.append({"fold_year": year, "status": "skipped", "reason": "refit unsupported"})
            continue
        coef, k = model["coefficients"], model["smearing_k"]
        errs_b2 = [float(np.log1p(max(0.0, _num(r["modis_frp_sum_mw"]) or 0.0))
                         - np.log1p(harmonize._predict_cell(coef, k, r)))
                   for r in rows_in_year]
        # B1 fold: ratio refit without the year, evaluated on it
        others = [r for r in pairs
                  if str(r.get("fitting_eligible")).lower() == "true"
                  and r["date"][:4] in reduced and r["date"] <= harmonize.TRAIN_END]
        sum_m = sum(_num(r["modis_frp_sum_mw"]) or 0.0 for r in others)
        sum_v = sum(_num(r["viirs_frp_sum_mw"]) or 0.0 for r in others)
        if sum_v <= 0:
            folds.append({"fold_year": year, "status": "skipped", "reason": "zero fold ratio"})
            continue
        r_b1 = sum_m / sum_v
        errs_b1 = [float(np.log1p(max(0.0, _num(r["modis_frp_sum_mw"]) or 0.0))
                         - np.log1p(max(0.0, _num(r["viirs_frp_sum_mw"]) or 0.0) * r_b1))
                   for r in rows_in_year]
        folds.append({"fold_year": year, "status": "ok",
                      "b2_mean_log_ratio_bias": round(float(np.mean(errs_b2)), 6),
                      "b1_mean_log_ratio_bias": round(float(np.mean(errs_b1)), 6),
                      "n_rows": len(rows_in_year)})
    ok_folds = [f for f in folds if f["status"] == "ok"]
    summary = {
        "status": "ok" if ok_folds else "deferred",
        "folds": folds,
        "note": "training-internal summary; the frozen held-out era is never touched",
    }
    if ok_folds:
        summary["mean_b2_bias"] = round(float(np.mean([f["b2_mean_log_ratio_bias"] for f in ok_folds])), 6)
        summary["mean_b1_bias"] = round(float(np.mean([f["b1_mean_log_ratio_bias"] for f in ok_folds])), 6)
    return summary


def run(baselines_csv: str | Path, harmonized_csv: str | Path,
        pairs_path: str | Path | None, out_dir: str | Path, aoi_id: str,
        run_ts: str | None = None) -> dict:
    baselines_csv, harmonized_csv = Path(baselines_csv), Path(harmonized_csv)
    if not baselines_csv.exists() or not harmonized_csv.exists():
        manifest = {
            "protocol_version": PROTOCOL_VERSION, "task": "C-05", "aoi_id": aoi_id,
            "status": "deferred",
            "reason": "C-03/C-04 artifacts absent — upstream returned insufficient_data on "
                      "the delivered fixture; metrics deferred pending full-era data",
            "required_metrics": REQUIRED_METRICS,
            "note": "deferred ≠ failed: machinery verified on synthetic data (tests), "
                    "real evaluation lands with the full-era swap-in",
        }
    else:
        outcome = evaluate(baselines_csv, harmonized_csv)
        manifest = {
            "protocol_version": PROTOCOL_VERSION, "task": "C-05", "aoi_id": aoi_id,
            "outcome": outcome,
            "reference_not_truth": "MODIS is the chosen reference measurement, never fire ground truth",
            "no_tuning_on_test": "no held-out row entered fitting, calibration, normalization "
                                 "or method selection (verified by C-03/C-04/C-05 contract tests)",
        }
        if outcome.get("status") == "ok" and pairs_path and Path(pairs_path).exists():
            pairs = load_pairs(pairs_path)
            # eligibility read from the C-04 manifest (same gate, single source)
            gate = json.loads(Path(harmonized_csv).parent.joinpath("model_manifest.json").read_text())
            manifest["leave_one_year_out"] = loyo_summary(pairs, set(gate["eligible_years"]))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "harmonization_metrics.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"manifest": manifest, "outputs": {"metrics": str(path)}}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-05 held-out metrics")
    parser.add_argument("--baselines", required=True, help="C-03 baseline_series.csv")
    parser.add_argument("--harmonized", required=True, help="C-04 harmonized_daily.csv")
    parser.add_argument("--pairs", default=None, help="C-02 matched_pairs.csv (for LOYO)")
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out_dir = args.out or f"artifacts/{args.aoi_id}"
    result = run(args.baselines, args.harmonized, args.pairs, out_dir, args.aoi_id)
    status = result["manifest"].get("status") or result["manifest"]["outcome"]["status"]
    print(json.dumps({"status": status, "outputs": result["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
