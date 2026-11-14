"""EmberLine C-05 — predetermined splice stress tests (PROTO-C01-v0.9, F-16).

Owner: team member C. Contract test: tests/test_splice_stress.py.

For every sufficiently covered AOI, ≥3 pseudo-transitions are selected by a rule
frozen BEFORE any prediction is looked at:

    T_i = the peak observed-MODIS FRP-sum day within each of 3 equal segments
    of the HELD-OUT (test-era) span.

Validity per test: the ±14-day window must lie fully inside the held-out span
and retain >= 70% paired-retrieved days. Each test compares, over the window:

    naive splice       A: observed MODIS before T, raw VIIRS after T
    harmonized splice  B: observed MODIS before T, B2 prediction after T
    continued MODIS    C: observed MODIS throughout  (the TRUTH reference)

    shift(X) = mean(log1p X after T) - mean(log1p X before T)
    error_naive    = shift(A) - shift(C)
    error_harm     = shift(B) - shift(C)
    error_ratio    = |error_harm| / |error_naive|   (N/A if |error_naive| ~ 0:
                     "naive error ~ 0 — nothing for harmonization to fix")

Changepoint significance: NOT IMPLEMENTED in v1 (no manufactured p-values);
recorded as such. Invalid/too-short windows are reported failed/deferred with
the exact shortfall — never renamed a pass. Unfavorable results (error_ratio
>= 1) stay visible: a valid negative result is acceptable evidence.
"""
from __future__ import annotations

import csv
import json
from datetime import date as _date, timedelta
from pathlib import Path

import numpy as np

from pipeline.baselines import PROTOCOL_VERSION
from pipeline.metrics import na, ok

WINDOW_DAYS = 14
MIN_WINDOW_FRACTION = 0.70
N_TRANSITIONS = 3
TOL = 1e-12


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _num(v) -> float | None:
    return None if v in (None, "") else float(v)


def _shift(rows: list[dict], value_field: str) -> dict:
    """mean(log1p after) - mean(log1p before) inside the window."""
    before, after = [], []
    for row in rows:
        v = _num(row[value_field])
        if v is None:
            continue
        (after if row["_after"] else before).append(v)
    if not before or not after:
        return na("window missing a before/after side")
    shift = float(np.mean(np.log1p(after)) - np.mean(np.log1p(before)))
    return ok(shift, len(before) + len(after))


def select_transitions(test_rows: list[dict]) -> tuple[list[str], list[str] | None, list[dict] | None]:
    """Predetermined rule: peak observed-MODIS day of each equal third segment.
    Returns (dates, transition_dates_or_None, deferred_slots_or_None)."""
    dates = sorted({r["date"] for r in test_rows})
    if len(dates) < N_TRANSITIONS * (2 * WINDOW_DAYS + 1):
        return dates, None, [{"segment": i, "status": "deferred",
                              "reason": f"held-out span ({len(dates)} days) too short for "
                                        f"{N_TRANSITIONS} independent ±{WINDOW_DAYS}-day windows"}
                             for i in range(N_TRANSITIONS)]
    segments = [dates[i * len(dates) // N_TRANSITIONS:(i + 1) * len(dates) // N_TRANSITIONS]
                for i in range(N_TRANSITIONS)]
    peak_rows = {r["date"]: r for r in test_rows}
    transitions = []
    for i, segment in enumerate(segments):
        peak = max(segment, key=lambda d: _num(peak_rows[d]["modis_frp_sum_mw"]) or 0.0)
        transitions.append(peak)
    return dates, transitions, None


def run_test(test_rows: list[dict], date_index: dict[str, list[dict]],
             transition: str) -> dict:
    start = (_date.fromisoformat(transition) - timedelta(days=WINDOW_DAYS)).isoformat()
    end = (_date.fromisoformat(transition) + timedelta(days=WINDOW_DAYS)).isoformat()
    window_dates = [(_date.fromisoformat(start) + timedelta(days=i)).isoformat()
                    for i in range(2 * WINDOW_DAYS + 1)]
    present = [d for d in window_dates if d in date_index]
    fraction = len(present) / len(window_dates)
    if _date.fromisoformat(start) < _date.fromisoformat(min(date_index)) or \
            _date.fromisoformat(end) > _date.fromisoformat(max(date_index)):
        return {"transition_date": transition, "status": "deferred",
                "reason": f"window {start}..{end} exceeds held-out span", "window": [start, end]}
    if fraction < MIN_WINDOW_FRACTION:
        return {"transition_date": transition, "status": "deferred",
                "reason": f"window paired-retrieval fraction {fraction:.2f} < {MIN_WINDOW_FRACTION}",
                "window": [start, end]}
    window = []
    for d in window_dates:
        if d not in date_index:
            continue
        day_rows = date_index[d]
        merged = dict(day_rows[0])
        merged["_after"] = d >= transition
        window.append(merged)
    shift_naive = _shift(window, "B0_naive_splice_mw")
    shift_harm = _shift(window, "B2_predicted_mw")
    shift_truth = _shift(window, "modis_frp_sum_mw")
    result: dict = {"transition_date": transition, "status": "ok",
                    "window": [start, end], "window_days_present": len(present),
                    "window_fraction": round(fraction, 4),
                    "shift_naive": shift_naive, "shift_harmonized": shift_harm,
                    "shift_truth_continued_modis": shift_truth,
                    "truth_note": "continued MODIS is the reference measurement, not fire ground truth"}
    if shift_naive["value"] == "N/A" or shift_harm["value"] == "N/A" or shift_truth["value"] == "N/A":
        result["status"] = "deferred"
        result["reason"] = "window lacks a before/after side"
        return result
    e_naive = shift_naive["value"] - shift_truth["value"]
    e_harm = shift_harm["value"] - shift_truth["value"]
    result["error_naive"] = round(e_naive, 6)
    result["error_harmonized"] = round(e_harm, 6)
    if abs(e_naive) < TOL:
        result["error_ratio"] = "N/A"
        result["error_ratio_reason"] = "naive error ~ 0 — nothing for harmonization to fix"
    else:
        result["error_ratio"] = round(abs(e_harm) / abs(e_naive), 6)
        result["interpretation"] = ("harmonization reduces the splice artifact"
                                    if abs(e_harm) < abs(e_naive)
                                    else "NEGATIVE RESULT: harmonization does not reduce the artifact here")
    return result


def run(baselines_csv: str | Path, harmonized_csv: str | Path,
        out_dir: str | Path, aoi_id: str, run_ts: str | None = None,
        harmonized_field: str = "B2_predicted_mw",
        out_name: str = "splice_stress_test.json",
        method_label: str = "B2") -> dict:
    baselines_csv, harmonized_csv = Path(baselines_csv), Path(harmonized_csv)
    if not baselines_csv.exists() or not harmonized_csv.exists():
        manifest = {
            "protocol_version": PROTOCOL_VERSION, "task": "C-05 stress", "aoi_id": aoi_id,
            "status": "deferred",
            "reason": "C-03/C-04 artifacts absent (insufficient_data upstream) — stress tests "
                      "deferred pending full-era data; machinery verified on synthetic tests",
            "changepoint_significance": "not_implemented (no p-values manufactured)",
        }
    else:
        base_rows = _read_csv(baselines_csv)
        harm_index = {(r["date"], r["daynight"]): r for r in _read_csv(harmonized_csv)}
        test_rows = []
        for r in base_rows:
            if r["role"] != "test":
                continue
            h = harm_index.get((r["date"], r["daynight"]))
            if h is None:
                raise ValueError(f"harmonized series missing held-out day {r['date']}/{r['daynight']}")
            merged = dict(r)
            merged["B2_predicted_mw"] = _num(h.get(harmonized_field))
            test_rows.append(merged)
        date_index: dict[str, list[dict]] = defaultdict_groups(test_rows)
        dates, transitions, deferred = select_transitions(test_rows)
        tests = deferred if deferred else [run_test(test_rows, date_index, t) for t in transitions]
        manifest = {
            "protocol_version": PROTOCOL_VERSION, "task": "C-05 stress", "aoi_id": aoi_id,
            "status": "ok" if any(t.get("status") == "ok" for t in tests) else "deferred",
            "method": method_label,
            "selection_rule": "T_i = peak observed-MODIS FRP-sum day of each equal third "
                              "of the held-out span (predetermined, no peeking at predictions)",
            "heldout_span": [dates[0], dates[-1]] if dates else None,
            "n_heldout_days": len(dates),
            "tests": tests,
            "changepoint_significance": "not_implemented (no p-values manufactured)",
            "negative_results_note": "error_ratio >= 1 or N/A entries stay visible in the "
                                     "demo and method page — valid negative results are evidence",
        }
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / out_name
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"manifest": manifest, "outputs": {"stress": str(path)}}


def defaultdict_groups(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["date"], []).append(row)
    return groups


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-05 splice stress tests")
    parser.add_argument("--baselines", required=True)
    parser.add_argument("--harmonized", required=True)
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out_dir = args.out or f"artifacts/{args.aoi_id}"
    result = run(args.baselines, args.harmonized, out_dir, args.aoi_id)
    print(json.dumps({"status": result["manifest"]["status"],
                      "outputs": result["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
