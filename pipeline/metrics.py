#!/usr/bin/env python3
"""Metrics (C-04) — the 12 required PROTO-C01 metrics on identical held-out rows.

Compares observed Aqua MODIS daily FRP-sum vs the harmonized estimate on TEST
years, paired on days where MODIS was observed. N/A policy: `N/A:<reason>` for
zero denominators / constant series / empty groups — never infinity, never a
fabricated zero. Sample sizes and missing counts travel with every metric.
"""
from __future__ import annotations

import math
from datetime import date


def _na(reason: str):
    return f"N/A:{reason}"


def _pearson(xs, ys):
    n = len(xs)
    if n < 2: return _na("n<2")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0: return _na("constant_series")
    return sxy / (sx * sy)


def _spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v); i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return _pearson(rank(xs), rank(ys))


def _linreg_r2_log(xs, ys):
    lx = [math.log1p(max(x, 0)) for x in xs]
    ly = [math.log1p(max(y, 0)) for y in ys]
    n = len(lx)
    if n < 2: return _na("n<2")
    mx, my = sum(lx) / n, sum(ly) / n
    sxx = sum((x - mx) ** 2 for x in lx)
    sxy = sum((x - mx) * (y - my) for x, y in zip(lx, ly))
    if sxx == 0: return _na("constant_series")
    b = sxy / sxx; a = my - b * mx
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(lx, ly))
    ss_tot = sum((y - my) ** 2 for y in ly)
    if ss_tot == 0: return _na("constant_series")
    return 1 - ss_res / ss_tot


def _ks(xs, ys):
    if not xs or not ys: return _na("empty_group")
    def ecdf(v):
        vs = sorted(v); out = []
        for i, x in enumerate(vs):
            out.append((x, (i + 1) / len(vs)))
        return out
    a, b = ecdf(xs), ecdf(ys)
    pts = sorted(set([x for x, _ in a] + [x for x, _ in b]))
    da = dict(a); db = dict(b)
    ca = cb = 0.0; dmax = 0.0
    for p in pts:
        if p in da: ca = da[p]
        if p in db: cb = db[p]
        dmax = max(dmax, abs(ca - cb))
    return round(dmax, 4)


def _wasserstein(xs, ys):
    if not xs or not ys: return _na("empty_group")
    a, b = sorted(xs), sorted(ys)
    i = j = 0; d = 0.0; pa = pb = None
    while i < len(a) or j < len(b):
        if j >= len(b) or (i < len(a) and a[i] < b[j]):
            if pb is not None:
                d += abs(a[i] - pb) * (j / len(b))
            pa = a[i]; i += 1
        else:
            if pa is not None:
                d += abs(b[j] - pa) * (i / len(a))
            pb = b[j]; j += 1
    return round(d / max(len(a), 1), 4)


def compute_metrics(series: list, test_years: list):
    test = {str(y) for y in test_years}
    paired = [r for r in series
              if r["date"][:4] in test
              and r["source_flag"] in ("harmonized_viirs", "observed_modis")
              and r["raw_modis_frp_mw"] is not None
              and r["harmonized_estimate_mw"] is not None]
    modis = [r["raw_modis_frp_mw"] for r in paired]
    est = [r["harmonized_estimate_mw"] for r in paired]
    m = {"n_test_days_paired": len(paired),
         "n_nonzero_modis_days": sum(1 for x in modis if x > 0),
         "n_nonzero_est_days": sum(1 for x in est if x > 0)}

    ratios = [math.log(max(e, 1e-9) / max(x, 1e-9)) for x, e in zip(modis, est) if x > 0 and e > 0]
    m["mean_log_ratio_bias"] = round(sum(ratios) / len(ratios), 4) if ratios else _na("no_nonzero_pairs")

    n = len(paired)
    m["smape"] = round(sum(abs(e - x) / ((abs(x) + abs(e)) / 2) for x, e in zip(modis, est) if (x + e) > 0) / n, 4) if n else _na("empty")
    nz = [(x, e) for x, e in zip(modis, est) if x > 0]
    m["mape_zero_actual_excluded"] = (round(sum(abs(e - x) / x for x, e in nz) / len(nz), 4) if nz else _na("no_nonzero_actual_pairs"))

    m["pearson_daily"] = _pearson(modis, est)
    m["spearman_daily"] = _spearman(modis, est)

    def weekly(series_vals, dates):
        agg = {}
        for v, d in zip(series_vals, dates):
            iso = date.fromisoformat(d).isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
            s, c = agg.get(key, (0.0, 0)); agg[key] = (s + v, c + 1)
        keys = sorted(agg)
        return [agg[k][0] for k in keys]
    wk_m = weekly(modis, [r["date"] for r in paired])
    wk_e = weekly(est, [r["date"] for r in paired])
    m["pearson_weekly"] = _pearson(wk_m, wk_e)
    m["spearman_weekly"] = _spearman(wk_m, wk_e)

    m["log_space_r2"] = _linreg_r2_log(modis, est)
    m["ks_statistic"] = _ks(modis, est)
    m["wasserstein_distance"] = _wasserstein(modis, est)

    # calendar pattern correlation: monthly totals observed vs estimated
    def monthly(vals, dates):
        agg = {}
        for v, d in zip(vals, dates):
            k = d[:7]; agg[k] = agg.get(k, 0.0) + v
        return [agg[k] for k in sorted(agg)]
    m["calendar_pattern_correlation"] = _pearson(monthly(modis, [r["date"] for r in paired]),
                                                 monthly(est, [r["date"] for r in paired]))

    cov = [1 if (r["harmonized_lo_mw"] is not None and r["harmonized_lo_mw"] <= r["raw_modis_frp_mw"]
                 and r["raw_modis_frp_mw"] <= r["harmonized_hi_mw"]) else 0
           for r in paired if r["harmonized_lo_mw"] is not None and r["raw_modis_frp_mw"] > 0]
    m["interval_coverage_empirical"] = (round(sum(cov) / len(cov), 4) if cov
                                        else _na("no_nonzero_modis_with_interval"))
    m["interval_coverage_note"] = "MODIS treated as reference measurement — not ground truth."
    return m
