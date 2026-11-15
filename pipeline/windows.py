"""EmberLine C-06 — critical burning windows (PROTO-C01-v0.9, F-18, DEC-3).

Owner: team member C. Contract test: tests/test_windows.py.

Runs on the smoothed climatology median curve produced by pipeline/calendar.py:

  threshold = the configured percentile (default 75th) of the smoothed curve
              over all 366 positions — a DESCRIPTIVE seasonal percentile,
              never a safety threshold
  windows   = contiguous runs of >= min_run_days (default 3) positions at or
              above the threshold; a run crossing position 366 -> 1 is a
              December-January window (wraps_dec_jan = true) and stays contiguous

  years_active  (DEC-3 PROVISIONAL): a year is ACTIVE when its own daily index
                exceeds the threshold on >= 3 of its era days; missing years
                are never counted inactive; denominator is years_eligible.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pipeline.baselines import PROTOCOL_VERSION
from pipeline.calendar import month_day_of

DEFAULT_THRESHOLD_PERCENTILE = 75
MIN_RUN_DAYS = 3
ACTIVE_MIN_DAYS = 3


def find_windows(smoothed: list[float | None], threshold: float,
                 min_run_days: int = MIN_RUN_DAYS) -> list[dict]:
    """Contiguous above-threshold runs; Dec->Jan wrapping supported."""
    n = len(smoothed)
    # STRICTLY above the threshold (F-18: "above the configured percentile") —
    # ties at the threshold do not count, otherwise flat curves form 366-day runs
    above = [v is not None and v > threshold for v in smoothed]
    windows = []
    visited = [False] * n
    for start in range(n):
        if not above[start] or visited[start]:
            continue
        length = 0
        pos = start
        while length < n and above[pos]:
            visited[pos] = True
            length += 1
            pos = (pos + 1) % n  # circular: 366 -> 1 wrap
        if length < min_run_days:
            continue
        positions = [(start + k) % n + 1 for k in range(length)]  # 1-based positions
        wraps = any(p2 < p1 for p1, p2 in zip(positions, positions[1:]))
        values = [smoothed[p - 1] for p in positions]
        months_days = [month_day_of(p) for p in positions]
        windows.append({
            "start_position": positions[0], "end_position": positions[-1],
            "start_month_day": f"{months_days[0][0]:02d}-{months_days[0][1]:02d}",
            "end_month_day": f"{months_days[-1][0]:02d}-{months_days[-1][1]:02d}",
            "length_days": length,
            "wraps_dec_jan": wraps,
            "median_index_in_window": round(float(np.median(values)), 6),
            "max_index_in_window": round(float(np.max(values)), 6),
        })
    windows.sort(key=lambda w: w["start_position"])
    return windows


def years_active(series: list[dict], smoothed: list[float | None], threshold: float) -> dict:
    """DEC-3 provisional rule: year's own daily index >= threshold on >= 3 era days."""
    counts: dict[str, int] = {}
    for entry in series:
        if entry["index"] is None:
            continue
        # compare the year's own index to the threshold (smoothed curve is the
        # climatological shape; per-year activity uses the year's own values)
        pos = int(entry["position"]) - 1
        reference = smoothed[pos] if smoothed[pos] is not None else entry["index"]
        # a day counts when the year's value AND the climatological shape are high
        if entry["index"] >= threshold and reference >= threshold:
            counts[entry["year"]] = counts.get(entry["year"], 0) + 1
    active = sorted(y for y, c in counts.items() if c >= ACTIVE_MIN_DAYS)
    return {
        "rule": f"years_active = year's daily index >= window threshold on >= {ACTIVE_MIN_DAYS} "
                "era days (DEC-3 PROVISIONAL; frozen with this artifact)",
        "threshold_rule": f"{DEFAULT_THRESHOLD_PERCENTILE}th percentile of the smoothed "
                          "climatology median curve (descriptive, NOT a safety threshold)",
        "active_days_per_year": {y: counts.get(y, 0) for y in sorted(counts)},
        "years_active": active,
        "missing_years_note": "years absent from the accepted series are never counted inactive",
    }


def run(calendar_out_dir: str | Path, out_dir: str | Path | None = None,
        threshold_percentile: int = DEFAULT_THRESHOLD_PERCENTILE) -> dict:
    """Consume calendar.py outputs (climatology.json + calendar.csv) -> windows.json."""
    calendar_dir = Path(calendar_out_dir)
    clim_path = calendar_dir / "climatology.json"
    cal_path = calendar_dir / "calendar.csv"
    out_dir = Path(out_dir) if out_dir else calendar_dir

    if not clim_path.exists() or not cal_path.exists():
        manifest = {
            "protocol_version": PROTOCOL_VERSION, "task": "C-06 windows", "aoi_id": calendar_dir.name,
            "status": "deferred",
            "reason": "calendar artifacts absent — C-06 upstream deferred/insufficient",
        }
    else:
        clim = json.loads(clim_path.read_text())
        with cal_path.open(newline="", encoding="utf-8") as handle:
            import csv
            cal_rows = [dict(row) for row in csv.DictReader(handle)]
        smoothed = [float(r["index_median_smoothed"]) if r["index_median_smoothed"] else None
                    for r in sorted(cal_rows, key=lambda r: int(r["position"]))]
        values = [v for v in smoothed if v is not None]
        if len(values) < 30:
            manifest = {
                "protocol_version": PROTOCOL_VERSION, "task": "C-06 windows",
                "aoi_id": clim.get("aoi_id"),
                "status": "insufficient_data",
                "reason": f"only {len(values)} populated positions — no defensible seasonal curve",
                "raw_series_note": "raw accepted series retained; sparse sample not shown as normal baseline",
            }
        else:
            threshold = float(np.quantile(np.array(values), threshold_percentile / 100.0))
            windows = find_windows(smoothed, threshold)
            import csv as _csv
            series_rows = []
            series_path = calendar_dir / "accepted_series.csv"
            if series_path.exists():
                with series_path.open(newline="", encoding="utf-8") as handle:
                    series_rows = [dict(row) for row in _csv.DictReader(handle)]
            for row in series_rows:
                row["index"] = None if row["index"] in (None, "", "None") else float(row["index"])
            activity = years_active(series_rows, smoothed, threshold)
            manifest = {
                "protocol_version": PROTOCOL_VERSION, "task": "C-06 windows",
                "aoi_id": clim.get("aoi_id"),
                "status": "ok",
                "threshold": {
                    "percentile_of_smoothed_curve": threshold_percentile,
                    "value": round(threshold, 6),
                    "meaning": "descriptive seasonal percentile — NOT a safety threshold; "
                               "stated in UI and exports",
                },
                "windows": windows,
                "n_windows": len(windows),
                "years_eligible": clim.get("years_eligible", []),
                "activity": activity,
            }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "windows.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"manifest": manifest, "outputs": {"windows": str(path)}}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-06 critical windows")
    parser.add_argument("--calendar-dir", required=True, help="dir with climatology.json + calendar.csv")
    parser.add_argument("--out", default=None)
    parser.add_argument("--threshold-percentile", type=int, default=DEFAULT_THRESHOLD_PERCENTILE)
    args = parser.parse_args(argv)
    result = run(args.calendar_dir, args.out, args.threshold_percentile)
    print(json.dumps({"status": result["manifest"]["status"],
                      "outputs": result["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
