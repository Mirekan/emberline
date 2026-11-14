#!/usr/bin/env python3
"""Harmonize (C-03/C-04) — B0/B1/B2 per PROTO-C01-v0.9, training-only law.

Fits on TRAINING matched units only:
  B1  r = sum(S_modis)/sum(S_viirs)              (training matched units)
  B2  log1p(S_modis) = a + b*log1p(S_viirs) + c*log1p(1+n_viirs) + d*I_night
      monotone b,c >= 0 via refit-projection; S_hat = k*expm1(y_hat),
      k = Duan smearing factor from training residuals.
  Fallback (recorded, training-internal decision): b2_simple (log-log ratio).

Intervals: training daily residual day-block bootstrap (resample UTC days,
B resamples, centered mean-residual quantiles applied multiplicatively).
Extrapolation flag: viirs covariates outside training p1..p99.

Outputs:  <out>/harmonized_daily.csv, <out>/model.json
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import emberline_proto as P


def _log1p(x: float) -> float:
    return math.log1p(max(x, 0.0))


def _ols(rows: list, ys: list) -> list:
    """Least squares via normal equations (pure python, small matrices)."""
    k = len(rows[0])
    ata = [[sum(r[i] * r[j] for r in rows) for j in range(k)] for i in range(k)]
    atb = [sum(r[i] * y for r, y in zip(rows, ys)) for i in range(k)]
    # Gaussian elimination with partial pivoting
    A = [ata[i][:] + [atb[i]] for i in range(k)]
    for col in range(k):
        piv = max(range(col, k), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-12:
            raise ValueError("singular normal matrix")
        A[col], A[piv] = A[piv], A[col]
        for r in range(k):
            if r != col and A[col][col] != 0:
                f = A[r][col] / A[col][col]
                for cc in range(col, k + 1):
                    A[r][cc] -= f * A[col][cc]
    return [A[i][k] / A[i][i] for i in range(k)]


def _predict_unit(coef: list, s_viirs: float, n_viirs: int, night: int) -> float:
    """coef = (a, b, c, d); returns predicted S_modis_equivalent (MW)."""
    a, b, c, d = coef
    y = a + b * _log1p(s_viirs) + c * _log1p(1 + max(n_viirs, 0)) + d * night
    return math.expm1(max(y, 0.0))


def run_harmonize(matched_csv: Path, coverage: dict, out_dir: Path,
                  fixture: str | None = None):
    units = []
    with matched_csv.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            units.append(row)

    if not units:
        raise SystemExit("ERROR: no matched units — nothing to harmonize")

    years = sorted({u["date"][:4] for u in units})
    mask = coverage["retrieval_mask"]
    first_d = date.fromisoformat(min(u["date"] for u in units))
    last_d = date.fromisoformat(max(u["date"] for u in units))

    # eligible years: >=90% paired-retrieved days within [first,last] AND
    # (training) >=10 modis signal days. Test years need the coverage condition only.
    eligible = []
    for y in years:
        d0 = max(first_d, date(int(y), 1, 1)); d1 = min(last_d, date(int(y), 12, 31))
        total = (d1 - d0).days + 1
        retrieved = sum(1 for d in (d0 + timedelta(days=i) for i in range(total))
                        if mask.get(d, "retrieved") == "retrieved")
        frac = retrieved / total
        sig = sum(1 for u in units if u["date"][:4] == y and float(u["modis_frp_sum"]) > 0)
        if frac >= P.SUPPORT_PAIRED_FRACTION and sig >= P.SUPPORT_MODIS_SIGNAL_DAYS:
            eligible.append(y)
    if len(eligible) < P.MIN_TRAIN_YEARS + P.MIN_TEST_YEARS:
        raise SystemExit(json.dumps({"status": "insufficient_data",
            "message": "Not enough eligible years to fit and validate a mapping.",
            "eligible_years": eligible}))

    n_train = max(1, round(len(eligible) * P.TRAIN_FRACTION))
    train_years, test_years = eligible[:n_train], eligible[n_train:]
    train_set = set(train_years)

    # ---- fit on training units only -----------------------------------------
    fit_rows, fit_y = [], []
    s_viirs_train, n_viirs_train = [], []
    sum_m = sum_v = 0.0
    for u in units:
        if u["date"][:4] not in train_set:
            continue
        sm = float(u["modis_frp_sum"]); sv = float(u["viirs_frp_sum"])
        nv = int(u["viirs_n"]); night = 1 if u["daynight"] == "N" else 0
        sum_m += sm; sum_v += sv
        fit_rows.append([1.0, _log1p(sv), _log1p(1 + nv), float(night)])
        fit_y.append(_log1p(sm))
        s_viirs_train.append(_log1p(sv)); n_viirs_train.append(nv)

    b1_ratio = (sum_m / sum_v) if sum_v > 0 else None

    coef = None; method = "b2_primary"
    try:
        coef = _ols(fit_rows, fit_y)
        if coef[1] < 0 or coef[2] < 0:   # monotone projection: drop offending term, refit
            rows2 = [[r[0], r[3]] for r in fit_rows]
            coef2 = _ols(rows2, fit_y)
            coef = [coef2[0], max(coef[1], 0.0), 0.0, coef2[1]]
            method = "b2_monotone_projected"
    except ValueError:
        coef = None
    use_b2 = bool(coef) and coef[1] > 0
    if not use_b2:
        # Protocol fallback: b2_simple_log_ratio_only = the global training ratio.
        method = "b2_simple_log_ratio_only"
        k_smear = 1.0

    # training residuals (daily aggregation of mapped estimates vs observed Aqua)
    daily = defaultdict(lambda: {"modis": 0.0, "modis_n": 0, "viirs": 0.0, "viirs_n": 0})
    for u in units:
        d = u["date"]
        daily[d]["modis"] += float(u["modis_frp_sum"]); daily[d]["modis_n"] += int(u["modis_n"])
        daily[d]["viirs"] += float(u["viirs_frp_sum"]); daily[d]["viirs_n"] += int(u["viirs_n"])
    train_resid = []
    for d, a in daily.items():
        if d[:4] not in train_set:
            continue
        if use_b2:
            pred = sum(_predict_unit(coef, float(u["viirs_frp_sum"]), int(u["viirs_n"]),
                                     1 if u["daynight"] == "N" else 0)
                       for u in units if u["date"] == d)
        else:
            pred = (b1_ratio or 0.0) * a["viirs"]
        if a["modis"] > 0:
            train_resid.append(_log1p(a["modis"]) - _log1p(pred))

    # Duan smearing (training, mapped units with viirs detections)
    sm_list = []
    for u in units:
        if use_b2 and u["date"][:4] in train_set and int(u["viirs_n"]) > 0:
            pred = _predict_unit(coef, float(u["viirs_frp_sum"]), int(u["viirs_n"]),
                                 1 if u["daynight"] == "N" else 0)
            obs = float(u["modis_frp_sum"])
            if pred > 0:
                sm_list.append(math.exp(_log1p(obs) - _log1p(pred)) if obs > 0 else math.exp(-_log1p(pred)))
    k_smear = (sum(sm_list) / len(sm_list)) if sm_list else 1.0
    if not use_b2:
        k_smear = 1.0

    # interval: day-block bootstrap of training daily residuals (centered)
    rnd = random.Random(20261114)
    B = P.BOOTSTRAP_B
    means = []
    n = len(train_resid)
    for _ in range(B):
        tot = 0.0
        for _ in range(n):
            tot += train_resid[rnd.randrange(n)]
        means.append(tot / n)
    mu = sum(means) / len(means)
    centered = sorted(m - mu for m in means)
    q_lo = centered[int(0.10 * (B - 1))]
    q_hi = centered[int(0.90 * (B - 1))]
    # 80% interval on the natural scale: pred * exp(q) with q from centered draws
    def interval(pred: float):
        return pred * math.exp(q_lo), pred * math.exp(q_hi)

    # extrapolation bounds from training viirs covariates
    s_sorted = sorted(s_viirs_train)
    n_sorted = sorted(n_viirs_train)
    p1s, p99s = s_sorted[max(0, int(0.01 * (len(s_sorted) - 1)))], s_sorted[int(0.99 * (len(s_sorted) - 1))]
    p1n, p99n = n_sorted[max(0, int(0.01 * (len(n_sorted) - 1)))], n_sorted[int(0.99 * (len(n_sorted) - 1))]

    # p95 training daily reference MODIS frp (index denominator, frozen)
    ref_daily = sorted(a["modis"] for d, a in daily.items() if d[:4] in train_set)
    p95_ref = ref_daily[min(len(ref_daily) - 1, int(0.95 * (len(ref_daily) - 1)))] if ref_daily else 0.0

    # viirs era start = first date with viirs detections
    viirs_start = min((u["date"] for u in units if int(u["viirs_n"]) > 0), default=None)

    # ---- daily series ---------------------------------------------------------
    out_rows = []
    d = first_d
    while d <= last_d:
        md = d
        a = daily.get(md.isoformat(), {"modis": 0.0, "modis_n": 0, "viirs": 0.0, "viirs_n": 0})
        retrieved = mask.get(md, "retrieved") == "retrieved"
        flags = []
        if not retrieved:
            out_rows.append({"date": md.isoformat(), "source_flag": "gap",
                             "raw_modis_frp_mw": None, "raw_modis_n": None,
                             "raw_viirs_frp_mw": None, "raw_viirs_n": None,
                             "harmonized_lo_mw": None, "harmonized_estimate_mw": None,
                             "harmonized_hi_mw": None, "flags": [],
                             "gap_reason": "failed_request", "units": 0})
            d += timedelta(days=1)
            continue
        total_det = a["modis_n"] + a["viirs_n"]
        in_viirs_era = (viirs_start is not None and md.isoformat() >= viirs_start)
        if in_viirs_era:
            if use_b2:
                pred = sum(_predict_unit(coef, float(u["viirs_frp_sum"]), int(u["viirs_n"]),
                                         1 if u["daynight"] == "N" else 0)
                           for u in units if u["date"] == md.isoformat())
            else:
                pred = (b1_ratio or 0.0) * a["viirs"]
            est = max(pred, 0.0)
            lo, hi = interval(est)
            if a["viirs_n"] == 0 and a["modis_n"] > 0:
                flags.append("one_sided")
            if a["viirs_n"] > 0:
                lv, ln_ = _log1p(a["viirs"]), a["viirs_n"]
                if lv < p1s or lv > p99s or ln_ < p1n or ln_ > p99n:
                    flags.append("extrapolation")
            hw = (hi - lo) / 2
            if est > 0 and hw / est > P.UNCERTAINTY_FLAG_RATIO:
                flags.append("high_uncertainty")
            if total_det < P.INSUFFICIENT_SUPPORT_MIN_DET and total_det > 0:
                flags.append("insufficient_support")
            out_rows.append({"date": md.isoformat(), "source_flag": "harmonized_viirs",
                             "raw_modis_frp_mw": round(a["modis"], 2), "raw_modis_n": a["modis_n"],
                             "raw_viirs_frp_mw": round(a["viirs"], 2), "raw_viirs_n": a["viirs_n"],
                             "harmonized_lo_mw": round(max(lo, 0.0), 2),
                             "harmonized_estimate_mw": round(est, 2),
                             "harmonized_hi_mw": round(hi, 2),
                             "flags": "|".join(flags), "gap_reason": None, "units": 1})
        else:
            out_rows.append({"date": md.isoformat(), "source_flag": "observed_modis",
                             "raw_modis_frp_mw": round(a["modis"], 2), "raw_modis_n": a["modis_n"],
                             "raw_viirs_frp_mw": round(a["viirs"], 2), "raw_viirs_n": a["viirs_n"],
                             "harmonized_lo_mw": None, "harmonized_estimate_mw": None,
                             "harmonized_hi_mw": None,
                             "flags": "|".join(["one_sided"] if a["modis_n"] > 0 and a["viirs_n"] == 0 else []),
                             "gap_reason": None, "units": 1})
        d += timedelta(days=1)

    out_dir.mkdir(parents=True, exist_ok=True)
    ser_path = out_dir / "harmonized_daily.csv"
    cols = list(out_rows[0].keys())
    with ser_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader(); w.writerows(out_rows)

    model = {
        "protocol_id": P.PROTO_ID, "method": method,
        "coefficients": {"a": round(coef[0], 5), "b": round(coef[1], 5),
                          "c": round(coef[2], 5), "d": round(coef[3], 5),
                          "k_duan_smearing": round(k_smear, 5)} if use_b2
                        else {"b1_ratio": round(b1_ratio, 5) if b1_ratio else None},
        "b1_ratio": round(b1_ratio, 5) if b1_ratio else None,
        "split": {"train_years": train_years, "test_years": test_years,
                  "eligible_years": eligible, "method": "contiguous_earliest_60pct"},
        "interval": {"nominal": P.NOMINAL_INTERVAL, "B": B, "method": "training_daily_residual_bootstrap_centered",
                     "q_lo_log": round(q_lo, 4), "q_hi_log": round(q_hi, 4)},
        "index_denominator_p95_training_modis_mw": round(p95_ref, 2),
        "viirs_era_start": viirs_start,
        "extrapolation_bounds": {"log1p_viirs": [round(p1s, 3), round(p99s, 3)],
                                  "n_viirs": [p1n, p99n]},
        "filter_counts": coverage["filter_counts"],
        "fixture": fixture,
    }
    (out_dir / "model.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
    print(f"[harmonize] method={method} train={train_years[0]}..{train_years[-1]} "
          f"test={test_years[0]}..{test_years[-1]} k={k_smear:.3f}")
    print(f"[harmonize] series -> {ser_path.name} ({len(out_rows)} days)")
    return model, out_rows, p95_ref, train_years, test_years
