#!/usr/bin/env python3
"""Build all missing calendar.json and grid.json artifacts for all 17 Indonesian AOIs."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTS = ROOT / "artifacts"
CELL_DEG = 0.1

DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
POS_366 = []
for m_idx, max_d in enumerate(DAYS_IN_MONTH, 1):
    for d in range(1, max_d + 1):
        POS_366.append(f"{m_idx:02d}-{d:02d}")


def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def build_papua_selatan_series():
    art = ARTS / "papua_selatan"
    if (art / "accepted_series.csv").exists():
        return
    base_csv = art / "baseline_series.csv"
    if not base_csv.exists():
        return
    
    rows_out = []
    with open(base_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = row["date"]
            yr = dt[:4]
            m = int(dt[5:7])
            d = int(dt[8:10])
            # calculate position 1..366
            pos = sum(DAYS_IN_MONTH[:m-1]) + d
            modis = row.get("modis_frp_sum_mw", "")
            val = float(modis) if modis else 0.0
            rows_out.append({
                "date": dt,
                "year": yr,
                "position": str(pos),
                "source_flag": "insufficient_support",
                "value_mw": str(val),
                "index": "0.0",
                "harmonized_mw": str(val),
                "observed_modis_mw": str(val),
            })
    
    out_csv = art / "accepted_series.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "date", "year", "position", "source_flag", "value_mw",
            "index", "harmonized_mw", "observed_modis_mw"
        ])
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"Generated {out_csv} with {len(rows_out)} rows.")


def build_calendar_json(aoi: str):
    art = ARTS / aoi
    cal_json_path = art / "calendar.json"
    if cal_json_path.exists():
        return

    cal_csv_path = art / "calendar.csv"
    clim_path = art / "climatology.json"
    win_path = art / "windows.json"
    man_path = art / "run_manifest.json"
    series_path = art / "accepted_series.csv"

    if not cal_csv_path.exists() or not clim_path.exists():
        return

    clim_json = json.load(open(clim_path, encoding="utf-8"))
    win_json = json.load(open(win_path, encoding="utf-8")) if win_path.exists() else {}
    man_json = json.load(open(man_path, encoding="utf-8")) if man_path.exists() else {}

    # Read calendar.csv
    climatology = []
    climatology_smoothed = []
    with open(cal_csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            month = int(r["month"])
            day = int(r["day"])
            md = f"{month:02d}-{day:02d}"
            med_raw = float(r.get("index_median_raw") or 0.0)
            med_smooth = float(r.get("index_median_smoothed") or 0.0)
            p25 = float(r.get("index_p25") or 0.0)
            p75 = float(r.get("index_p75") or 0.0)
            n_yr = int(r.get("n_years") or 0)
            st = "data" if r.get("state") == "populated" else (r.get("state") or "data")

            climatology.append({
                "month_day": md,
                "median_mw": round(med_raw, 4),
                "iqr": {"p25_mw": round(p25, 4), "p75_mw": round(p75, 4)},
                "n_years": n_yr,
                "state": st,
            })
            climatology_smoothed.append(round(med_smooth, 4))

    # Read windows.json
    critical_windows = []
    for w in win_json.get("windows", []):
        critical_windows.append({
            "start_md": w.get("start_month_day", ""),
            "end_md": w.get("end_month_day", ""),
            "wraps_new_year": w.get("wraps_dec_jan", False),
            "median_intensity_mw": round(float(w.get("median_index_in_window") or 0.0), 2),
            "threshold_percentile": win_json.get("threshold", {}).get("percentile_of_smoothed_curve", 75),
            "years_active": len(win_json.get("activity", {}).get("years_active", [])),
            "years_eligible": len(win_json.get("years_eligible", [])),
        })

    # Read accepted_series.csv to index daily values
    series_by_date = {}
    years_seen = set()
    if series_path.exists():
        with open(series_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                dt = row.get("date", "")
                if not dt or len(dt) < 10:
                    continue
                yr = int(dt[:4])
                md = dt[5:10]
                years_seen.add(yr)
                val_raw = row.get("value_mw")
                val = float(val_raw) if val_raw not in (None, "") else None
                idx_raw = row.get("index")
                idx = float(idx_raw) if idx_raw not in (None, "") else None
                src = row.get("source_flag") or "harmonized_viirs"
                state = "data" if val and val > 0 else ("valid_zero" if val == 0 else "retrieval_gap")
                series_by_date[(yr, md)] = {
                    "month_day": md,
                    "value_mw": round(val, 2) if val is not None else None,
                    "state": state,
                    "source_flag": src,
                    "flags": [],
                    "reason": None,
                    "index": round(idx, 4) if idx is not None else None,
                }

    eligible_years_str = clim_json.get("years_eligible", [])
    eligible_years = [int(y) for y in eligible_years_str] if eligible_years_str else sorted(years_seen)
    if not eligible_years:
        eligible_years = list(range(2018, 2027))

    all_years = sorted(set(eligible_years) | years_seen)
    years_list = []
    for yr in all_years:
        pos_list = []
        is_leap = is_leap_year(yr)
        for md in POS_366:
            if md == "02-29" and not is_leap:
                pos_list.append({
                    "month_day": "02-29",
                    "value_mw": None,
                    "state": "not_applicable",
                    "source_flag": None,
                    "flags": [],
                    "reason": "non_leap_year",
                    "index": None,
                })
                continue
            
            p = series_by_date.get((yr, md))
            if p:
                pos_list.append(p)
            else:
                pos_list.append({
                    "month_day": md,
                    "value_mw": None,
                    "state": "retrieval_gap",
                    "source_flag": None,
                    "flags": [],
                    "reason": "outside_era",
                    "index": None,
                })

        years_list.append({
            "year": yr,
            "eligible": yr in eligible_years,
            "positions": pos_list,
        })

    payload = {
        "run_id": man_json.get("run_id", "PROTO-C01-v0.9"),
        "model_version": man_json.get("model_version", "b1_ratio_fit"),
        "fixture": "FIXTURE_REAL",
        "metric": "harmonized_frp_sum_mw (index where denominator available)",
        "index_denominator_p95_training_mw": clim_json.get("index", {}).get("denominator_mw", 100.0),
        "state_enum": ["data", "valid_zero", "retrieval_gap", "insufficient_support", "not_applicable"],
        "eligible_years": eligible_years,
        "years": years_list,
        "climatology": climatology,
        "climatology_smoothed_median_mw": climatology_smoothed,
        "critical_windows": critical_windows,
        "boundary": "Historical & descriptive — not predictive. Critical window is not a safe-to-burn recommendation."
    }

    cal_json_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"Generated {cal_json_path}")


def build_grid_json(aoi: str):
    art = ARTS / aoi
    grid_json_path = art / "grid.json"
    if grid_json_path.exists():
        return

    det_path = art / "detections.json"
    detections = []
    if det_path.exists():
        try:
            detections = json.load(open(det_path, encoding="utf-8")).get("detections", [])
        except Exception:
            detections = []

    cells_map = {}
    years_seen = set()
    for d in detections:
        l_idx = math.floor(d["lat"] / CELL_DEG + 1e-9)
        o_idx = math.floor(d["lon"] / CELL_DEG + 1e-9)
        cid = f"R{l_idx:05d}C{o_idx:05d}"
        yr = d["date"][:4]
        years_seen.add(yr)

        if cid not in cells_map:
            cells_map[cid] = {
                "cell_id": cid,
                "south": round(l_idx * CELL_DEG, 4),
                "west": round(o_idx * CELL_DEG, 4),
                "north": round((l_idx + 1) * CELL_DEG, 4),
                "east": round((o_idx + 1) * CELL_DEG, 4),
                "years": {},
                "dates": set(),
                "total_modis": 0.0,
                "total_viirs": 0.0,
            }
        
        c = cells_map[cid]
        c["dates"].add(d["date"])
        if yr not in c["years"]:
            c["years"][yr] = {"modis": 0.0, "viirs": 0.0, "dates": set()}
        yv = c["years"][yr]
        yv["dates"].add(d["date"])

        frp = float(d.get("frp", 0.0))
        if d.get("sensor") == "modis":
            c["total_modis"] += frp
            yv["modis"] += frp
        else:
            c["total_viirs"] += frp
            yv["viirs"] += frp

    cells_out = []
    for cid, c in cells_map.items():
        years_dict = {}
        for yr, yv in c["years"].items():
            years_dict[yr] = {
                "modis": round(yv["modis"], 2),
                "viirs": round(yv["viirs"], 2),
                "n_days": len(yv["dates"]),
            }
        cells_out.append({
            "cell_id": cid,
            "south": c["south"],
            "west": c["west"],
            "north": c["north"],
            "east": c["east"],
            "years": years_dict,
            "n_days": len(c["dates"]),
            "total_modis": round(c["total_modis"], 2),
            "total_viirs": round(c["total_viirs"], 2),
        })

    cells_out.sort(key=lambda x: (x["south"], x["west"]))
    payload = {
        "cell_deg": CELL_DEG,
        "years": sorted(years_seen) if years_seen else ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        "n_cells": len(cells_out),
        "scale_note": "raw sensor scale — per-cell harmonized does not exist",
        "cells": cells_out,
    }

    grid_json_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"Generated {grid_json_path} with {len(cells_out)} cells.")


def main():
    build_papua_selatan_series()
    
    aois = [p.name for p in sorted(ARTS.iterdir()) if p.is_dir() and p.name not in ("all", "indonesia")]
    for aoi in aois:
        build_calendar_json(aoi)
        build_grid_json(aoi)


if __name__ == "__main__":
    main()
