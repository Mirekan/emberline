"""EmberLine C-04 — interpretable harmonization B2 + uncertainty
(PROTO-C01-v0.9, F-12/F-13/F-14, DEV-S03).

Owner: team member C. Contract test: tests/test_harmonization_leakage.py.

Model (frozen F-12), fitted on TRAINING cell-days only:
    log1p(S_modis) = a + b*log1p(S_viirs) + c*log1p(1 + n_viirs) + d*I_night
    monotone by construction: b >= 0, c >= 0 (negative OLS coefficients are
    projected to zero and the projection is recorded in the manifest)
    prediction per cell-day:  S_hat = max(0, k * expm1(y_hat))
      k = Duan smearing factor from TRAINING log-space residuals
    zero policy (v1): S_viirs == 0 and n_viirs == 0  ->  S_hat = 0
      ("no VIIRS signal in, no mapped signal out" — an interpretable stand-in
      for the two-part zero-inflation model, which is deferred; log1p embeds
      zeros in fitting)
    quantile correction: omitted in v1 (DEV-S03, recorded)

Uncertainty (frozen F-13): intervals are calibrated WHERE THEY ARE PUBLISHED —
AOI-daily. Training AOI-day residuals (observed minus predicted, linear MW,
both-retrieved days only) are day-level bootstrapped per day/night class with a
fixed seed; the 10th/90th percentiles form the NOMINAL 80% interval around the
AOI prediction. Cell bounds are never summed. Actual coverage is MEASURED at
C-05 on held-out days — 80% is a target to verify, not a promise.

Support policy: eligibility uses the F-9b/DEC-2 gate shared with C-03; if it
fails, the result is an explicit insufficient_data, never a fitted model on
thin support. Held-out cell-days with log1p(S_viirs) outside the training 1st-
99th percentile carry an `extrapolation` flag (F-13).

Source policy (F-14): this module only produces estimates for overlap days
(both sensors retrieved). Pre-VIIRS-era MODIS observations join the published
series from the per-sensor units at C-06/E; sensors are never blended.
"""
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from pipeline.baselines import (  # same-role reuse, allowed
    BaselineError,
    MIN_TEST_YEARS,
    MIN_TRAIN_YEARS,
    PROTOCOL_VERSION,
    TEST_START,
    TRAIN_END,
    _era_day_counts,
    aggregate_aoi_days,
    eligible_years,
    load_pairs,
)

MODEL_VERSION = "b2-primary"
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 42
INTERVAL_LO_Q = 0.10
INTERVAL_HI_Q = 0.90
EXTRAPOLATION_P = (0.01, 0.99)
REQUIRED_PAIR_COLUMNS = {
    "date", "daynight", "modis_frp_sum_mw", "viirs_frp_sum_mw",
    "viirs_detection_count", "state", "fitting_eligible",
}


def _num(row: dict, field: str) -> float | None:
    raw = row.get(field)
    return None if raw in (None, "") else float(raw)


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[1], check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _features(row: dict) -> list[float]:
    """[1, log1p(S_viirs), log1p(1+n_viirs), I_night] for one cell-day pair."""
    s_viirs = _num(row, "viirs_frp_sum_mw") or 0.0
    n_viirs = _num(row, "viirs_detection_count") or 0.0
    night = 1.0 if str(row.get("daynight")) == "night" else 0.0
    return [1.0, float(np.log1p(max(0.0, s_viirs))),
            float(np.log1p(max(0.0, 1.0 + n_viirs))), night]


def _fit_monotone_ols(x: np.ndarray, y: np.ndarray,
                      w: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Weighted OLS with b,c >= 0 enforced by projection (recorded, never silent).
    Weights reproduce duplicated-row semantics exactly (compact zero-fill)."""
    if w is None:
        w = np.ones(len(y))
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(x * sw[:, None], y * sw, rcond=None)
    projected: dict[str, str] = {}
    for idx, name in ((1, "b"), (2, "c")):
        if coef[idx] < 0:
            keep = [j for j in range(x.shape[1]) if j != idx]
            refit, *_ = np.linalg.lstsq(x[:, keep] * sw[:, None], y * sw, rcond=None)
            for out_i, in_i in enumerate(keep):
                coef[out_i] = refit[out_i]
            coef[idx] = 0.0
            projected[name] = "projected_to_zero"
    return coef, projected


def fit_b2_rows(train_rows: list[dict],
                zero_weights: dict[str, float] | None = None) -> dict:
    """Core fit on explicitly given TRAINING rows (no support gate — the gate
    belongs to the full run; LOYO folds call this directly).

    zero_weights: {"day": total_zero_cells, "night": total_zero_cells} — the
    compact zero-fill representation. Every zero-fill cell-day has identical
    features [1, 0, 0, I_night] and target 0, so weighting by count is
    mathematically IDENTICAL to materializing every per-cell row.
    """
    x = np.array([_features(r) for r in train_rows])
    y = np.array([np.log1p(max(0.0, _num(r, "modis_frp_sum_mw") or 0.0)) for r in train_rows])
    w = np.ones(len(train_rows))
    if zero_weights:
        for daynight, weight in zero_weights.items():
            if weight <= 0:
                continue
            night = 1.0 if daynight == "night" else 0.0
            x = np.vstack([x, np.array([[1.0, 0.0, 0.0, night]])])
            y = np.append(y, 0.0)
            w = np.append(w, float(weight))
    coef, projected = _fit_monotone_ols(x, y, w)
    residuals = y - x @ coef
    smearing_k = float(np.sum(w * np.exp(residuals)) / np.sum(w))  # weighted Duan, training-only

    a, b, c, d = (round(float(v), 8) for v in coef)
    return {
        "coefficients": {"a_intercept": a, "b_log1p_viirs": b, "c_log1p_count": c, "d_night": d},
        "monotone_projection": projected or "none_active",
        "smearing_k": round(smearing_k, 8),
        "fit_inputs": {
            "unit": "cell-day pairs, fitting-eligible only (F-6), training years only; "
                    "compact zero-fill entered as exact weights (identical to duplicated rows)",
            "n_train_rows": int(len(train_rows)),
            "zero_cells_weighted": {k: int(v) for k, v in (zero_weights or {}).items()},
        },
    }


def fit_b2(pairs: list[dict], eligible_years_set: set[str],
           zero_weights: dict[str, float] | None = None) -> dict | None:
    """Fit on TRAINING cell-days only, behind the F-9b support gate.
    Returns model dict or None if unsupportable."""
    train_rows = [
        r for r in pairs
        if str(r.get("fitting_eligible")).lower() == "true"
        and r["date"][:4] in eligible_years_set
        and r["date"] <= TRAIN_END
    ]
    train_years = sorted({r["date"][:4] for r in train_rows})
    test_years = sorted({
        r["date"][:4] for r in pairs
        if r["date"][:4] in eligible_years_set and r["date"] > TRAIN_END
    })
    if len(train_years) < MIN_TRAIN_YEARS or len(test_years) < MIN_TEST_YEARS:
        return None

    model = fit_b2_rows(train_rows, zero_weights)
    model["fit_inputs"]["train_years"] = train_years
    model["fit_inputs"]["test_years_recorded_never_fitted"] = test_years
    return model


def _predict_cell(coef: dict, smearing_k: float, row: dict) -> float:
    s_viirs = _num(row, "viirs_frp_sum_mw") or 0.0
    n_viirs = _num(row, "viirs_detection_count") or 0.0
    if s_viirs == 0.0 and n_viirs == 0.0:
        return 0.0  # zero policy (v1): no signal in, no mapped signal out
    night = 1.0 if str(row.get("daynight")) == "night" else 0.0
    y_hat = (coef["a_intercept"]
             + coef["b_log1p_viirs"] * float(np.log1p(max(0.0, s_viirs)))
             + coef["c_log1p_count"] * float(np.log1p(max(0.0, 1.0 + n_viirs)))
             + coef["d_night"] * night)
    return max(0.0, smearing_k * float(np.expm1(y_hat)))


def _aoi_day_series(pairs: list[dict], eligible: set[str], model: dict, aoi_id: str,
                    zero_fill: list[dict] | None = None) -> tuple[list[dict], list[float]]:
    """Group cell-day pairs into AOI-days (both-retrieved only), predict, and
    collect TRAINING AOI-day residuals for interval calibration. Compact
    zero-fill days become 0.0-value AOI-days (all cells predict 0 by policy) —
    no-fire days exist in the series without per-cell materialization."""
    by_day: dict[tuple[str, str], list[dict]] = {}
    for row in pairs:
        if row["date"][:4] not in eligible:
            continue
        if _num(row, "viirs_frp_sum_mw") is None or _num(row, "modis_frp_sum_mw") is None:
            continue  # not both-retrieved: no truth, no prediction here
        by_day.setdefault((row["date"], str(row["daynight"])), []).append(row)

    coef, k = model["coefficients"], model["smearing_k"]
    days: list[dict] = []
    train_residuals: list[float] = []
    for (day, daynight) in sorted(by_day):
        rows = by_day[(day, daynight)]
        observed = sum(_num(r, "modis_frp_sum_mw") or 0.0 for r in rows)
        predicted = sum(_predict_cell(coef, k, r) for r in rows)
        entry = {
            "aoi_id": rows[0].get("aoi_id", ""), "date": day, "daynight": daynight,
            "role": "train" if day <= TRAIN_END else "test",
            "source_flag": "harmonized_viirs",
            "n_cells_predicted": len(rows),
            "observed_modis_mw": round(observed, 6),
            "predicted_b2_mw": round(predicted, 6),
            "lo_mw": None, "hi_mw": None, "flags": [],
        }
        if entry["role"] == "train":
            train_residuals.append(observed - predicted)
        days.append(entry)
    for zf in zero_fill or []:
        key = (str(zf["date"]), str(zf["daynight"]))
        if str(zf["date"])[:4] not in eligible:
            continue
        existing = next((d for d in days if (d["date"], d["daynight"]) == key), None)
        if existing is None:
            day, daynight = key
            entry = {
                "aoi_id": aoi_id, "date": day, "daynight": daynight,
                "role": "train" if day <= TRAIN_END else "test",
                "source_flag": "harmonized_viirs",
                "n_cells_predicted": int(zf.get("n_zero_cells", 0)),
                "observed_modis_mw": 0.0, "predicted_b2_mw": 0.0,
                "lo_mw": None, "hi_mw": None, "flags": [],
            }
            if entry["role"] == "train":
                train_residuals.append(0.0)  # perfect zero prediction on an all-zero day
            days.append(entry)
        else:
            existing["n_cells_predicted"] += int(zf.get("n_zero_cells", 0))
    days.sort(key=lambda d: (d["date"], d["daynight"]))
    return days, train_residuals


def _apply_intervals(days: list[dict], train_residuals: list[float], daynight: str) -> dict:
    """Day-level bootstrap of TRAINING AOI-day residuals -> nominal 80% bounds."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    residuals = np.array(train_residuals)
    samples = rng.choice(residuals, size=BOOTSTRAP_DRAWS, replace=True)
    q_lo = float(np.quantile(samples, INTERVAL_LO_Q))
    q_hi = float(np.quantile(samples, INTERVAL_HI_Q))
    for entry in days:
        if entry["daynight"] != daynight:
            continue
        entry["lo_mw"] = round(max(0.0, entry["predicted_b2_mw"] + q_lo), 6)
        entry["hi_mw"] = round(entry["predicted_b2_mw"] + q_hi, 6)
        # bounds stay ordered and contain the estimate, with a visible flag
        if entry["hi_mw"] < entry["predicted_b2_mw"] or entry["lo_mw"] > entry["predicted_b2_mw"]:
            entry["hi_mw"] = max(entry["hi_mw"], entry["predicted_b2_mw"])
            entry["lo_mw"] = min(entry["lo_mw"], entry["predicted_b2_mw"])
            entry["flags"].append("interval_widened_to_contain_estimate")
    return {
        "daynight": daynight,
        "q10_mw": round(q_lo, 6), "q90_mw": round(q_hi, 6),
        "bootstrap_draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
        "nominal_target": 0.80,
        "note": "nominal 80% target calibrated on training AOI-day residuals "
                "(day-level bootstrap); actual held-out coverage is MEASURED at C-05, not promised",
    }


def _flag_extrapolation(pairs: list[dict], days: list[dict], eligible: set[str]) -> tuple[int, dict]:
    """F-13: flag held-out AOI-days whose cell inputs fall outside training support."""
    train_log_s = [
        float(np.log1p(max(0.0, _num(r, "viirs_frp_sum_mw") or 0.0)))
        for r in pairs
        if str(r.get("fitting_eligible")).lower() == "true"
        and r["date"][:4] in eligible and r["date"] <= TRAIN_END
    ]
    p_lo, p_hi = (float(v) for v in np.quantile(np.array(train_log_s), EXTRAPOLATION_P))
    index = {(d["date"], d["daynight"]): d for d in days}
    flagged = 0
    for row in pairs:
        key = (row["date"], str(row["daynight"]))
        if key not in index or row["date"] <= TRAIN_END:
            continue
        log_s = float(np.log1p(max(0.0, _num(row, "viirs_frp_sum_mw") or 0.0)))
        if (log_s < p_lo or log_s > p_hi) and "extrapolation" not in index[key]["flags"]:
            index[key]["flags"].append("extrapolation")
            flagged += 1
    return flagged, {"support_lo_log1p": round(p_lo, 4), "support_hi_log1p": round(p_hi, 4)}


def run(pairs_path: str | Path, out_dir: str | Path, aoi_id: str,
        run_ts: str | None = None, zero_fill_csv: str | Path | None = None) -> dict:
    """Full C-04 step: eligibility gate -> B2 fit -> AOI-day estimates + intervals."""
    pairs = load_pairs(pairs_path)
    if not pairs:
        raise BaselineError("matched pairs: no rows received (run C-02 first)")
    missing = REQUIRED_PAIR_COLUMNS - set(pairs[0])
    if missing:
        raise BaselineError(f"matched pairs schema mismatch — missing {sorted(missing)}")

    # compact zero-fill is part of coverage: read it BEFORE the F-9b gate so
    # retrieved all-zero days count toward the paired-retrieval fraction
    zero_fill_rows: list[dict] = []
    if zero_fill_csv and Path(zero_fill_csv).exists():
        with open(zero_fill_csv, newline="", encoding="utf-8") as handle:
            zero_fill_rows = [dict(row) for row in csv.DictReader(handle)]

    aoi_days_for_gate, _ = aggregate_aoi_days(pairs, zero_fill_rows)
    era_days = _era_day_counts([b["date"] for b in aoi_days_for_gate])
    eligible, year_report = eligible_years(aoi_days_for_gate, era_days)
    train_year_count = len({y for y in eligible if y <= TRAIN_END[:4]})
    test_year_count = len({y for y in eligible if y >= TEST_START[:4]})
    if train_year_count < MIN_TRAIN_YEARS or test_year_count < MIN_TEST_YEARS:
        outcome: dict = {"status": "insufficient_data",
                         "reason": "F-9b support gate failed — no model fitted (shared with C-03)",
                         "eligible_years": sorted(eligible)}
        days: list[dict] = []
    else:
        # compact zero-fill -> exact weights, filtered to TRAINING days only (F-11)
        zero_weights: dict[str, float] = {}
        for zf in zero_fill_rows:
            day = str(zf["date"])
            if day <= TRAIN_END and day[:4] in eligible:
                zero_weights[str(zf["daynight"])] = \
                    zero_weights.get(str(zf["daynight"]), 0.0) + float(zf.get("n_zero_cells", 0))
        model = fit_b2(pairs, eligible, zero_weights or None)
        if model is None:
            outcome = {"status": "insufficient_data",
                       "reason": "no training rows after eligibility/split — no model fitted"}
            days = []
        else:
            days, train_residuals = _aoi_day_series(pairs, eligible, model, aoi_id, zero_fill_rows)
            intervals = [_apply_intervals(days, train_residuals, cls)
                         for cls in ("day", "night") if train_residuals]
            flagged, support = _flag_extrapolation(pairs, days, eligible)
            outcome = {
                "status": "ok",
                "model": model,
                "intervals": intervals,
                "extrapolation_flagged_days": flagged,
                "support_bounds": support,
                "n_aoi_days": len(days),
            }

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "task": "C-04",
        "model_version": MODEL_VERSION,
        "run_id": f"{PROTOCOL_VERSION}_{MODEL_VERSION}_{run_ts or datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')}",
        "git_sha": git_sha(),
        "aoi_id": aoi_id,
        "frozen_split": {"train_end": TRAIN_END, "test_start": TEST_START},
        "year_eligibility": year_report,
        "eligible_years": sorted(eligible),
        "outcome": outcome,
        "source_policy": "F-14: MODIS reference before VIIRS support, mapped VIIRS in "
                         "validated coverage, explicit gaps otherwise; sensors never blended",
        "zero_policy": "v1: S_viirs==0 and n==0 -> prediction 0 (two-part zero-inflation model deferred)",
        "quantile_correction": "omitted in v1 (DEV-S03)",
        "scope_note": "FRP-sum is an aggregate of sampled radiative-power observations; "
                      "MODIS is the reference measurement, not fire ground truth",
    }
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "model_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    outputs = {"manifest": str(manifest_path)}
    if outcome.get("status") == "ok":
        columns = ["aoi_id", "date", "daynight", "role", "source_flag", "n_cells_predicted",
                   "observed_modis_mw", "predicted_b2_mw", "lo_mw", "hi_mw", "flags"]
        series_path = out_dir / "harmonized_daily.csv"
        with series_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(
                {k: (";".join(v) if isinstance(v, list) else v) for k, v in entry.items()}
                for entry in days
            )
        outputs["series"] = str(series_path)
    return {"manifest": manifest, "outputs": outputs, "days": days}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-04 harmonization B2 + intervals")
    parser.add_argument("--pairs", required=True, help="C-02 matched_pairs.csv")
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--out", default=None, help="default artifacts/<aoi-id>/")
    args = parser.parse_args(argv)
    out_dir = args.out or f"artifacts/{args.aoi_id}"
    result = run(args.pairs, out_dir, args.aoi_id)
    print(json.dumps({"outcome_status": result["manifest"]["outcome"]["status"],
                      "outputs": result["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
