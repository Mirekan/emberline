#!/usr/bin/env python3
"""Calendar & climatology (C-06) — 366 month/day template, PROTO-C01 §calendar.

Five cell states (pattern+text+icon in the UI, never color alone):
  data · valid_zero · retrieval_gap · high_uncertainty · insufficient_support
  · not_applicable (Feb 29 non-leap — never "missing data").
Index: log1p(harmonized)/log1p(p95 training reference); same transform on bounds.
Climatology: median + IQR over eligible years per month/day, ±7-day circular smoothing.
Critical windows: 75th percentile of the smoothed curve, min run 3 days, Dec-Jan wrap.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path

import emberline_proto as P

MD = [(m, d) for m in range(1, 13) for d in range(1, 32)
      if d <= ([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])]
MD_LEAP_IDX = {f"{m:02d}-{d:02d}": i for i, (m, d) in enumerate(MD)}


def _date_for_md(year: int, md: str):
    m, d = md.split("-")
    try:
        return date(year, int(m), int(d))
    except ValueError:
        return None  # Feb 29 in a non-leap year


def run_calendar(series: list, p95_ref: float, train_years: list, eligible_years: list,
                 out_dir: Path, run_id: str, model_version: str, fixture):
    # group series by year
    n_md = len(MD)
    md_str = [f"{m:02d}-{d:02d}" for m, d in MD]
    by_year = {}
    for r in series:
        by_year.setdefault(r["date"][:4], {})[r["date"]] = r

    def index_of(row):
        if row["harmonized_estimate_mw"] is not None:
            v, lo, hi = row["harmonized_estimate_mw"], row["harmonized_lo_mw"], row["harmonized_hi_mw"]
        else:
            v, lo, hi = row["raw_modis_frp_mw"], None, None
        if v is None or p95_ref <= 0:
            return None, None, None
        den = math.log1p(p95_ref)
        iv = (math.log1p(max(v, 0)) / den) if den > 0 else None
        ilo = (math.log1p(max(lo, 0)) / den) if (den > 0 and lo is not None) else None
        ihi = (math.log1p(max(hi, 0)) / den) if (den > 0 and hi is not None) else None
        return iv, ilo, ihi

    years_out = []
    for y in sorted(by_year):
        positions = []
        leap = (int(y) % 4 == 0 and int(y) % 100 != 0) or int(y) % 400 == 0
        for md in md_str:
            dt = _date_for_md(int(y), md)
            if dt is None:
                positions.append({"month_day": md, "value_mw": None, "state": "not_applicable",
                                  "source_flag": None, "flags": [],
                                  "reason": "feb29_non_leap", "index": None})
                continue
            r = by_year[y].get(dt.isoformat())
            if r is None or r["source_flag"] == "gap":
                positions.append({"month_day": md, "value_mw": None, "state": "retrieval_gap",
                                  "source_flag": None, "flags": [],
                                  "reason": (r or {}).get("gap_reason") or "failed_request",
                                  "index": None})
                continue
            v = r["harmonized_estimate_mw"] if r["harmonized_estimate_mw"] is not None else r["raw_modis_frp_mw"]
            total_det = (r["raw_modis_n"] or 0) + (r["raw_viirs_n"] or 0)
            if v == 0:
                state = "valid_zero"
            elif "insufficient_support" in (r["flags"] or []) or total_det < P.INSUFFICIENT_SUPPORT_MIN_DET:
                state = "insufficient_support"
            elif "high_uncertainty" in (r["flags"] or []):
                state = "high_uncertainty"
            else:
                state = "data"
            iv, _, _ = index_of(r)
            positions.append({"month_day": md, "value_mw": v, "state": state,
                              "source_flag": r["source_flag"],
                              "flags": r["flags"] or [], "reason": None, "index": iv})
        years_out.append({"year": int(y), "eligible": y in eligible_years,
                          "positions": positions})

    # typical-year climatology across eligible years (per month/day), smoothed ±7
    elig_years = [y for y in years_out if y["eligible"]]
    pos_by_md = {}
    for y in elig_years:
        for p in y["positions"]:
            if p["value_mw"] is not None:
                pos_by_md.setdefault(p["month_day"], []).append(p["value_mw"])
    clim = []
    n_md = len(MD)
    md_str = [f"{m:02d}-{d:02d}" for m, d in MD]
    raw_med = {}
    for i, md in enumerate(md_str):
        vals = sorted(pos_by_md.get(md, []))
        if not vals:
            raw_med[md] = None
            clim.append({"month_day": md, "median_mw": None, "iqr": None,
                         "n_years": len(vals), "state": "retrieval_gap" if not vals else "data"})
            continue
        k = len(vals)
        med = vals[k // 2] if k % 2 else (vals[k // 2 - 1] + vals[k // 2]) / 2
        p25 = vals[max(0, int(0.25 * (k - 1)))]; p75 = vals[int(0.75 * (k - 1))]
        raw_med[md] = med
        clim.append({"month_day": md, "median_mw": round(med, 2),
                     "iqr": {"p25_mw": round(p25, 2), "p75_mw": round(p75, 2)},
                     "n_years": k, "state": "data"})
    # circular ±7-day smoothing of the median curve (None days take neighbor mean)
    med_vals = [raw_med[md] for md in md_str]
    known = {i: v for i, v in enumerate(med_vals) if v is not None}
    smooth = []
    for i in range(n_md):
        window = []
        for off in range(-P.CAL_SMOOTH_DAYS, P.CAL_SMOOTH_DAYS + 1):
            j = (i + off) % n_md
            if j in known:
                window.append(known[j])
        smooth.append(round(sum(window) / len(window), 2) if window else None)

    # critical windows: >= 75th percentile of smoothed curve, min run 3, Dec-Jan wrap
    valid = [v for v in smooth if v is not None]
    if valid:
        s = sorted(valid)
        thr = s[int(P.WINDOW_PERCENTILE / 100 * (len(s) - 1))]
    else:
        thr = None
    flags_md = [thr is not None and v is not None and v >= thr for v in smooth]
    windows = []
    i = 0
    while i < n_md:
        if flags_md[i]:
            j = i
            while j + 1 < n_md and flags_md[j + 1]:
                j += 1
            if (j - i + 1) >= P.WINDOW_MIN_RUN_DAYS or (i == 0 and flags_md[-1]):
                start_i, end_i = i, j
                if i == 0 and flags_md[-1] and not flags_md[1]:
                    pass
                if i == 0 and j == n_md - 1:
                    windows = []
                    break
                wrap = start_i == 0 and flags_md[n_md - 1]
                if wrap:
                    k = n_md - 1
                    while k >= 0 and flags_md[k]:
                        k -= 1
                    start_i = k + 1
                windows.append({"start_md": md_str[start_i], "end_md": md_str[end_i],
                                "wraps_new_year": wrap,
                                "median_intensity_mw": round(max(0.0, sum(v for v in smooth[start_i:end_i + 1] if v is not None) / max(1, end_i - start_i + 1)), 2)})
                i = j + 1
                continue
            i = j + 1
        else:
            i += 1
    # Dec-Jan wrap continuation: if Jan head and Dec tail are both flagged, merge
    if len(windows) >= 2 and windows[0]["start_md"] == "01-01" and windows[-1]["end_md"] == "12-31":
        w0 = windows.pop()
        windows[0] = {"start_md": w0["start_md"], "end_md": windows[0]["end_md"],
                      "wraps_new_year": True,
                      "median_intensity_mw": w0["median_intensity_mw"]}

    # active years per window (provisional rule): smoothed index above threshold >=3 days
    for w in windows:
        w.update({"threshold_percentile": P.WINDOW_PERCENTILE, "years_active": None,
                  "years_eligible": len(elig_years)})

    cal = {"run_id": run_id, "model_version": model_version, "fixture": fixture,
           "metric": "harmonized_frp_sum_mw (index where denominator available)",
           "index_denominator_p95_training_mw": round(p95_ref, 2),
           "state_enum": ["data", "valid_zero", "retrieval_gap", "high_uncertainty",
                           "insufficient_support", "not_applicable"],
           "eligible_years": eligible_years,
           "years": years_out,
           "climatology": clim,
           "climatology_smoothed_median_mw": smooth,
           "critical_windows": windows,
           "boundary": ("Historical & descriptive — not predictive. Critical window is "
                         "not a safe-to-burn recommendation.")}
    out = Path(out_dir) / "calendar.json"
    out.write_text(json.dumps(cal, indent=2), encoding="utf-8")
    print(f"[calendar] years={len(years_out)} windows={len(windows)} -> {out.name}")
    return cal
