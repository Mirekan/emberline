#!/usr/bin/env python3
"""Splice Stress Test (C-05) — predetermined pseudo-transitions, no peeking.

T_i = peak observed MODIS FRP-sum day within each of 3 equal segments of the
eligible held-out span. Window = ±14 days, fully inside held-out, paired
retrieval fraction >= 0.70 (else reported deferred with the exact shortfall).
shift(X) = mean(X in 14d after T) / mean(X in 14d before T);
truth = continued MODIS throughout; error_ratio = shift_harmonized / shift_truth.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import emberline_proto as P


def _window_mean(rows_by_date, d0, d1, field):
    vals = []
    d = d0
    while d <= d1:
        r = rows_by_date.get(d.isoformat())
        if r is not None and r.get(field) is not None:
            vals.append(r[field])
        d += timedelta(days=1)
    return (sum(vals) / len(vals)) if vals else None


def run_stress(series: list, test_years: list, coverage: dict, out_dir: Path,
               run_id: str, fixture):
    mask = coverage["retrieval_mask"]
    by_date = {r["date"]: r for r in series}
    test_sorted = sorted(test_years)
    first_d = date(int(test_sorted[0]), 1, 1)
    last_d = date(int(test_sorted[-1]), 12, 31)
    span = (last_d - first_d).days + 1
    seg = span / P.STRESS_COUNT_MIN

    results = []
    for i in range(P.STRESS_COUNT_MIN):
        s0 = first_d + timedelta(days=round(i * seg))
        s1 = first_d + timedelta(days=round((i + 1) * seg) - 1)
        peak, peak_v = None, -1.0
        d = s0
        while d <= s1:
            r = by_date.get(d.isoformat())
            if r and r.get("raw_modis_frp_mw") is not None and r["raw_modis_frp_mw"] > peak_v:
                peak, peak_v = d, r["raw_modis_frp_mw"]
            d += timedelta(days=1)
        if peak is None:
            results.append({"segment": i + 1, "status": "deferred",
                            "reason": "no MODIS observation in segment"})
            continue
        d0, d1 = peak - timedelta(days=P.STRESS_WINDOW_DAYS), peak + timedelta(days=P.STRESS_WINDOW_DAYS)
        if d0 < first_d or d1 > last_d:
            results.append({"segment": i + 1, "pseudo_transition": peak.isoformat(),
                            "status": "deferred",
                            "reason": f"window leaves held-out span ({d0}..{d1})"})
            continue
        days = [d0 + timedelta(days=k) for k in range(2 * P.STRESS_WINDOW_DAYS + 1)]
        paired = sum(1 for d in days if mask.get(d, "retrieved") == "retrieved")
        frac = paired / len(days)
        if frac < P.STRESS_MIN_PAIRED:
            results.append({"segment": i + 1, "pseudo_transition": peak.isoformat(),
                            "status": "deferred",
                            "reason": f"paired_retrieval_fraction {frac:.2f} < {P.STRESS_MIN_PAIRED:.2f}"})
            continue
        pre0, pre1 = d0, peak - timedelta(days=1)
        post0, post1 = peak, d1
        mean_modis_pre = _window_mean(by_date, pre0, pre1, "raw_modis_frp_mw")
        mean_modis_post = _window_mean(by_date, post0, post1, "raw_modis_frp_mw")
        mean_viirs_post = _window_mean(by_date, post0, post1, "raw_viirs_frp_mw")
        mean_harm_post = _window_mean(by_date, post0, post1, "harmonized_estimate_mw")
        if None in (mean_modis_pre, mean_modis_post, mean_viirs_post, mean_harm_post) or mean_modis_pre == 0:
            results.append({"segment": i + 1, "pseudo_transition": peak.isoformat(),
                            "status": "deferred", "reason": "empty mean in window (all zero or missing)"})
            continue
        shift_naive = mean_viirs_post / mean_modis_pre
        shift_harm = mean_harm_post / mean_modis_pre
        shift_truth = mean_modis_post / mean_modis_pre
        results.append({"segment": i + 1, "pseudo_transition": peak.isoformat(),
                        "window": f"{d0}..{d1}", "paired_retrieval_fraction": round(frac, 2),
                        "status": "computed",
                        "shift_naive": round(shift_naive, 3),
                        "shift_harmonized": round(shift_harm, 3),
                        "shift_truth": round(shift_truth, 3),
                        "error_ratio": round(shift_harm / shift_truth, 3) if shift_truth else "N/A:zero_truth_shift"})
    out = Path(out_dir) / "stress_test.json"
    out.write_text(json.dumps({"run_id": run_id, "fixture": fixture,
                               "selection_rule": "peak MODIS FRP-sum day per equal segment of eligible held-out span (predetermined)",
                               "window_days": P.STRESS_WINDOW_DAYS,
                               "results": results}, indent=2), encoding="utf-8")
    computed = sum(1 for r in results if r["status"] == "computed")
    print(f"[stress] computed={computed}/{len(results)} -> {out.name}")
    return results
