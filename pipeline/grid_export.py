#!/usr/bin/env python3
"""Grid export (O-02 map layer) — per-cell yearly FRP totals from matched.csv.

cell_id scheme from grid.py (F-4): R{lat_idx:05d}C{lon_idx:05d}, floor(x / 0.1),
half-open [south, north) x [west, east). Decode gives each cell's bounds directly.

RAW sensor columns only (modis_frp_sum / viirs_frp_sum) — per-cell harmonized does
not exist (harmonization is fit on AOI-wide aggregates), so the map layer is honest
raw-scale and must be labeled as such in the UI.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

CELL_DEG = 0.1


def decode_cell(cell_id: str) -> tuple[float, float, float, float]:
    """cell_id -> (south, west, north, east) bounds."""
    lat_idx = int(cell_id[1:6])
    lon_idx = int(cell_id[7:12])
    s = lat_idx * CELL_DEG
    w = lon_idx * CELL_DEG
    return s, w, s + CELL_DEG, w + CELL_DEG


def export_grid(matched_path: Path, out_path: Path) -> dict:
    years: set[str] = set()
    cells: dict[str, dict] = {}
    with open(matched_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["cell_id"]
            year = row["date"][:4]
            years.add(year)
            c = cells.setdefault(cid, {"cell_id": cid, "years": {}, "n_days": 0})
            yv = c["years"].setdefault(year, {"modis": 0.0, "viirs": 0.0, "n_days": 0})
            try:
                m = float(row.get("modis_frp_sum") or 0.0)
            except ValueError:
                m = 0.0
            try:
                v = float(row.get("viirs_frp_sum") or 0.0)
            except ValueError:
                v = 0.0
            yv["modis"] = round(yv["modis"] + m, 2)
            yv["viirs"] = round(yv["viirs"] + v, 2)
            yv["n_days"] += 1
            c["n_days"] += 1

    out = []
    for cid, c in cells.items():
        s, w, n, e = decode_cell(cid)
        out.append({
            "cell_id": cid,
            "south": round(s, 4), "west": round(w, 4),
            "north": round(n, 4), "east": round(e, 4),
            "years": c["years"],
            "n_days": c["n_days"],
            "total_modis": round(sum(y["modis"] for y in c["years"].values()), 2),
            "total_viirs": round(sum(y["viirs"] for y in c["years"].values()), 2),
        })
    out.sort(key=lambda x: x["cell_id"])
    payload = {
        "cell_deg": CELL_DEG,
        "years": sorted(years),
        "n_cells": len(out),
        "scale_note": "raw sensor scale — per-cell harmonized does not exist",
        "cells": out,
    }
    out_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return payload


if __name__ == "__main__":  # manual: python pipeline/grid_export.py riau
    import sys
    aoi = sys.argv[1] if len(sys.argv) > 1 else "riau"
    root = Path(__file__).resolve().parents[1]
    p = export_grid(root / "artifacts" / aoi / "matched.csv",
                    root / "artifacts" / aoi / "grid.json")
    print(f"[grid_export] {p['n_cells']} cells, years {p['years'][0]}..{p['years'][-1]}")
