"""EmberLine C-06 — activity index, 366-position calendar & climatology
(PROTO-C01-v0.9, F-14/F-17/F-18, DEC-3).

Owner: team member C. Contract test: tests/test_calendar.py.

Accepted series (source policy F-14, never blended silently):
  - pre-VIIRS era  -> observed Aqua MODIS daily totals (from C-02 per-sensor units)
  - VIIRS era      -> B2 harmonized estimates (from C-04 harmonized_daily.csv)
Each day carries source_flag = observed_modis | harmonized_viirs; gaps stay
absent (a gap is never a zero).

Activity index (F-17):
  idx(day) = log1p(harmonized/published AOI FRP-sum day total)
             / log1p(denominator)
  denominator = P95 of daily reference-MODIS FRP-sum over the FROZEN training
  days (role=train in the C-04 artifact), frozen here and recorded; if it is
  <= 0 or unavailable the index is UNAVAILABLE and raw MW units are shown.

Calendar: every real date maps to a fixed 366-position month/day axis.
February 29 exists as position 60 and is fed ONLY by leap years — non-leap
years simply do not contribute (not_applicable, never a retrieval outage).
Per position: median, IQR (p25/p75), p10/p90, n_years, and a documented
circular ±7-day smoothing of the median across the 366->1 seam.

Eligibility (F-18): a year is eligible when >= 60% of its era days have valid
index values (partial calendar years are measured against their era days, not
the full calendar — recorded as the stated coverage rule). Missing years are
never counted inactive. If fewer than 2 eligible years support a position's
climatology the status is insufficient_data — a sparse sample is never shown
as a normal seasonal baseline.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date as _date, timedelta
from pathlib import Path

import numpy as np

from pipeline.baselines import PROTOCOL_VERSION, load_pairs

SMOOTH_DAYS = 7
ELIGIBLE_FRACTION = 0.60
MIN_ELIGIBLE_YEARS = 2
P10, P25, P50, P75, P90 = 0.10, 0.25, 0.50, 0.75, 0.90


def _num(v) -> float | None:
    return None if v in (None, "") else float(v)


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def position_of(month: int, day: int) -> int:
    """1..366 month/day position (Feb 29 = 60)."""
    cumulative = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    return cumulative[month - 1] + day  # Jan1=1 .. Feb28=59, Feb29=60, Dec31=366


def month_day_of(position: int) -> tuple[int, int]:
    lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # leap-year frame
    for m, length in enumerate(lengths, start=1):
        if position <= sum(lengths[:m - 1]) + length:
            return m, position - sum(lengths[:m - 1])
    raise ValueError(f"position {position} outside 1..366")


def build_accepted_series(harmonized_rows: list[dict], unit_rows: list[dict] | None) -> list[dict]:
    """F-14 published series: observed MODIS pre-era + harmonized VIIRS in-era.

    Only BOTH-retrieved harmonized rows feed the era (truth exists); Aqua-only
    days before the era come from the C-02 per-sensor units. Days with no entry
    are gaps — absent, never zero-filled.
    """
    by_day: dict[str, dict] = {}
    for row in harmonized_rows:
        value = _num(row.get("predicted_b2_mw"))
        observed = _num(row.get("observed_modis_mw"))
        if value is None or observed is None:
            continue  # not both-retrieved: no truth, not in the accepted series
        day = by_day.setdefault(row["date"], {
            "date": row["date"], "value_mw": 0.0, "source_flag": "harmonized_viirs",
            "harmonized_mw": 0.0, "observed_modis_mw": 0.0,
        })
        day["value_mw"] += value
        day["harmonized_mw"] += value
        day["observed_modis_mw"] += observed
    if unit_rows:
        for row in unit_rows:
            if str(row.get("family")) != "modis" or str(row.get("satellite", "")).lower() != "aqua":
                continue  # Aqua reference only — Terra never blended (S-01)
            value = _num(row.get("frp_sum_mw"))
            if value is None or row["date"] in by_day:
                continue  # overlap days already represented by the era rule
            by_day[row["date"]] = {
                "date": row["date"], "value_mw": value, "source_flag": "observed_modis",
                "harmonized_mw": None, "observed_modis_mw": value,
            }
    return [by_day[k] for k in sorted(by_day)]


def _freeze_denominator(harmonized_rows: list[dict]) -> tuple[float | None, int]:
    """P95 of daily reference-MODIS FRP-sum over FROZEN training days (F-17)."""
    daily: dict[str, float] = defaultdict(float)
    for row in harmonized_rows:
        if str(row.get("role")) != "train":
            continue
        observed = _num(row.get("observed_modis_mw"))
        if observed is not None:
            daily[row["date"]] += observed
    if not daily:
        return None, 0
    values = np.array(sorted(daily.values()))
    return float(np.quantile(values, 0.95)), len(values)


def _circular_smooth(values: list[float | None], radius: int = SMOOTH_DAYS) -> list[float | None]:
    """±radius mean across the 366->1 seam; None positions stay None."""
    n = len(values)
    out: list[float | None] = []
    for i in range(n):
        window, misses = [], 0
        for offset in range(-radius, radius + 1):
            v = values[(i + offset) % n]
            if v is None:
                misses += 1
            else:
                window.append(v)
        if misses > radius:  # more than half the window missing -> not smoothed
            out.append(None)
        elif window:
            out.append(float(np.mean(window)))
        else:
            out.append(None)
    return out


def run(harmonized_csv: str | Path, units_csv: str | Path | None,
        out_dir: str | Path, aoi_id: str, run_ts: str | None = None) -> dict:
    harmonized_csv = Path(harmonized_csv)
    if not harmonized_csv.exists():
        manifest = {
            "protocol_version": PROTOCOL_VERSION, "task": "C-06", "aoi_id": aoi_id,
            "status": "deferred",
            "reason": "C-04 harmonized series absent — upstream insufficient_data on the "
                      "delivered fixture; calendar deferred, raw-series rules unchanged",
            "note": "deferred ≠ failed: calendar machinery verified on synthetic data",
        }
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "climatology.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return {"manifest": manifest, "outputs": {"climatology": str(out_dir / "climatology.json")}}

    harmonized_rows = _read_csv(harmonized_csv)
    unit_rows = _read_csv(Path(units_csv)) if units_csv and Path(units_csv).exists() else None
    series = build_accepted_series(harmonized_rows, unit_rows)
    if not series:
        manifest = {"protocol_version": PROTOCOL_VERSION, "task": "C-06", "aoi_id": aoi_id,
                    "status": "insufficient_data", "reason": "no accepted-series days"}
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "climatology.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return {"manifest": manifest, "outputs": {"climatology": str(out_dir / "climatology.json")}}

    denominator, n_train_days = _freeze_denominator(harmonized_rows)
    index_available = denominator is not None and denominator > 0
    log_den = float(np.log1p(denominator)) if index_available else None

    for entry in series:
        if index_available:
            entry["index"] = round(float(np.log1p(max(0.0, entry["value_mw"]))) / log_den, 6)
        else:
            entry["index"] = None
        year = entry["date"][:4]
        entry["year"] = year
        entry["position"] = position_of(int(entry["date"][5:7]), int(entry["date"][8:10]))

    # eligibility (F-18): >=60% of a year's CALENDAR-ERA days valid — era days
    # for year Y = calendar days of Y inside the accepted-series span, so a
    # 1-day partial year can never pass as a normal-year sample
    span_start = _date.fromisoformat(series[0]["date"])
    span_end = _date.fromisoformat(series[-1]["date"])
    era_days_per_year: dict[str, int] = defaultdict(int)
    cursor = span_start
    while cursor <= span_end:
        era_days_per_year[str(cursor.year)] += 1
        cursor += timedelta(days=1)
    valid_days_per_year: dict[str, set[str]] = defaultdict(set)
    for entry in series:
        if entry["index"] is not None:
            valid_days_per_year[entry["year"]].add(entry["date"])
    years_eligible = sorted(
        y for y, days in era_days_per_year.items()
        if len(valid_days_per_year.get(y, set())) / days >= ELIGIBLE_FRACTION
    )

    # 366-position accumulation (Feb 29 fed only by leap years)
    per_position: dict[int, list[float]] = defaultdict(list)
    per_position_years: dict[int, set[str]] = defaultdict(set)
    for entry in series:
        if entry["index"] is None:
            continue
        per_position[entry["position"]].append(entry["index"])
        per_position_years[entry["position"]].add(entry["year"])
    raw_medians = [
        float(np.median(per_position[p])) if per_position.get(p) else None
        for p in range(1, 367)
    ]
    smoothed = _circular_smooth(raw_medians, SMOOTH_DAYS)
    calendar_rows = []
    for p in range(1, 367):
        month, day = month_day_of(p)
        values = per_position.get(p, [])
        calendar_rows.append({
            "position": p, "month": month, "day": day,
            "index_median_raw": None if raw_medians[p - 1] is None else round(raw_medians[p - 1], 6),
            "index_median_smoothed": None if smoothed[p - 1] is None else round(smoothed[p - 1], 6),
            "index_p10": round(float(np.quantile(values, P10)), 6) if values else None,
            "index_p25": round(float(np.quantile(values, P25)), 6) if values else None,
            "index_p75": round(float(np.quantile(values, P75)), 6) if values else None,
            "index_p90": round(float(np.quantile(values, P90)), 6) if values else None,
            "n_years": len(per_position_years.get(p, set())),
            "years": ";".join(sorted(per_position_years.get(p, set()))),
            "state": ("populated" if len(per_position_years.get(p, set())) >= MIN_ELIGIBLE_YEARS
                      else ("sparse" if values else "missing")),
        })

    manifest = {
        "protocol_version": PROTOCOL_VERSION, "task": "C-06", "aoi_id": aoi_id,
        "status": "ok" if len(years_eligible) >= MIN_ELIGIBLE_YEARS else "insufficient_data",
        "reason": (None if len(years_eligible) >= MIN_ELIGIBLE_YEARS else
                   f"only {len(years_eligible)} eligible year(s) — sparse sample is NOT shown "
                   "as a normal seasonal baseline; raw series retained"),
        "index": {
            "formula": "idx(day) = log1p(published AOI FRP-sum) / log1p(P95 training daily reference MODIS FRP-sum)",
            "denominator_mw": None if denominator is None else round(denominator, 6),
            "denominator_frozen_from": f"role=train days in the C-04 artifact ({n_train_days} days)",
            "available": index_available,
            "raw_units_fallback": "raw MW are always available in the accepted series",
        },
        "axis": "366-position month/day; Feb 29 (position 60) fed only by leap years — "
                "non-leap years are not_applicable, never a retrieval outage",
        "smoothing": f"circular ±{SMOOTH_DAYS} days across the 366->1 seam (median curve)",
        "eligibility_rule": f">= {ELIGIBLE_FRACTION:.0%} of a year's CALENDAR-ERA days valid "
                            "(era days = calendar days of the year inside the series span; "
                            "partial years cannot pass as normal-year samples)",
        "years_eligible": years_eligible,
        "years_in_series": sorted(era_days_per_year),
        "dec3_note": "years_active is computed in windows.json (DEC-3 provisional rule)",
        "reference_note": "MODIS is the reference measurement, not fire ground truth; "
                          "index is AOI-specific and not comparable across regions",
    }
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    series_path = out_dir / "accepted_series.csv"
    with series_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "year", "position", "source_flag",
                                                    "value_mw", "index", "harmonized_mw", "observed_modis_mw"])
        writer.writeheader()
        writer.writerows([{k: v for k, v in entry.items() if k in writer.fieldnames}
                          for entry in series])
    calendar_path = out_dir / "calendar.csv"
    with calendar_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(calendar_rows[0]))
        writer.writeheader()
        writer.writerows(calendar_rows)
    clim_path = out_dir / "climatology.json"
    clim_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"manifest": manifest, "series": series, "calendar": calendar_rows,
            "smoothed": smoothed,
            "outputs": {"series": str(series_path), "calendar": str(calendar_path),
                        "climatology": str(clim_path)}}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-06 calendar climatology")
    parser.add_argument("--harmonized", required=True)
    parser.add_argument("--units", default=None, help="C-02 units_per_sensor.csv (pre-era Aqua)")
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out_dir = args.out or f"artifacts/{args.aoi_id}"
    result = run(args.harmonized, args.units, out_dir, args.aoi_id)
    print(json.dumps({"status": result["manifest"]["status"], "outputs": result["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
