#!/usr/bin/env python3
"""Match & aggregate (C-02) — pairing unit (0.1 deg cell, UTC day, day/night).

Reads normalized.csv files (validate.py schema), applies PROTO-C01 filters
(Aqua-only reference for MODIS; confidence filters; unknown excluded+counted),
aggregates per unit separately per sensor, and writes:
  <out>/matched.csv   one row per unit with both sensors' aggregates + one_sided
  <out>/coverage.json day retrieval mask from the fetch ledger + filter counts
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import grid
import emberline_proto as P


def _read_ledger_mask(ledger_path: Path, start: date, end: date):
    """Day -> retrieved/failed from fetch ledger windows."""
    mask = {}
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("action") != "fetch":
                continue
            try:
                ws = date.fromisoformat(e["window_start"])
                we = date.fromisoformat(e["window_end"])
            except (KeyError, ValueError):
                continue
            st = "retrieved" if e.get("status") in ("ok", "ok_empty") else "failed"
            d = ws
            while d <= we:
                if st == "retrieved" or mask.get(d) != "retrieved":
                    mask[d] = st
                d += timedelta(days=1)
    return mask


def run_match(data_root: Path, sources: tuple, slug: str, out_dir: Path):
    counts = {"rows_read": 0, "modis_terra_excluded": 0,
              "conf_modis_excluded": 0, "conf_viirs_excluded": 0,
              "conf_unknown_excluded": 0}
    # sensor -> (date, cell_id, daynight) -> [n, frp_sum, frp_max, scan_sum]
    agg = {s: defaultdict(lambda: [0, 0.0, 0.0, 0.0]) for s in sources}
    dets: list = []
    dates_min, dates_max = None, None

    for source in sources:
        norm = data_root / source / slug / "normalized.csv"
        if not norm.exists():
            raise SystemExit(f"ERROR: missing normalized cache: {norm}")
        with norm.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                counts["rows_read"] += 1
                sat = row["satellite"]
                if source.startswith("MODIS") and sat != P.REFERENCE_SENSOR:
                    counts["modis_terra_excluded"] += 1
                    continue
                conf = (row["confidence_raw"] or "").strip()
                if conf.lower() == "unknown":
                    counts["conf_unknown_excluded"] += 1
                    continue
                if source.startswith("MODIS"):
                    if row["conf_scale"] == "percent":
                        try:
                            if int(conf) < P.CONF_MODIS_MIN_NUMERIC:
                                counts["conf_modis_excluded"] += 1
                                continue
                        except ValueError:
                            counts["conf_unknown_excluded"] += 1
                            continue
                    else:
                        counts["conf_unknown_excluded"] += 1
                        continue
                else:
                    if conf not in P.CONF_VIIRS_KEEP:
                        counts["conf_viirs_excluded"] += 1
                        continue
                try:
                    frp = float(row["frp_mw"])
                    lat = float(row["latitude"]); lon = float(row["longitude"])
                except ValueError:
                    continue
                cid = grid.cell_id(lat, lon)
                dets.append({"date": row["acq_date"], "lat": lat, "lon": lon,
                             "frp": round(frp, 2),
                             "sensor": "modis" if source.startswith("MODIS") else "viirs",
                             "conf": conf, "daynight": row["daynight"]})
                key = (row["acq_date"], cid, row["daynight"])
                a = agg[source][key]
                a[0] += 1; a[1] += frp
                a[2] = max(a[2], frp)
                try:
                    a[3] += float(row["scan"]); 
                except ValueError:
                    pass
                d = row["acq_date"]
                dates_min = d if dates_min is None or d < dates_min else dates_min
                dates_max = d if dates_max is None or d > dates_max else dates_max

    mask = _read_ledger_mask(data_root / "fetch_ledger.jsonl",
                             date.fromisoformat(dates_min) if dates_min else date(2012, 1, 1),
                             date.fromisoformat(dates_max) if dates_max else date(2026, 7, 31))

    keys = sorted(set(agg[sources[0]]) | set(agg[sources[1]]) if len(sources) > 1 else set(agg[sources[0]]),
                  key=lambda k: (k[0], k[1], k[2]))
    out_dir.mkdir(parents=True, exist_ok=True)
    matched_path = out_dir / "matched.csv"
    n_pairs = 0
    with matched_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "cell_id", "daynight",
                    "modis_n", "modis_frp_sum", "modis_frp_max", "modis_mean_scan",
                    "viirs_n", "viirs_frp_sum", "viirs_frp_max", "viirs_mean_scan",
                    "one_sided"])
        for (d, cid, dn) in keys:
            m = agg[sources[0]].get((d, cid, dn), [0, 0.0, 0.0, 0.0])
            v = agg[sources[1]].get((d, cid, dn), [0, 0.0, 0.0, 0.0]) if len(sources) > 1 else m
            m_scan = round(m[3] / m[0], 3) if m[0] else ""
            v_scan = round(v[3] / v[0], 3) if v[0] else ""
            one_sided = int((m[0] > 0) != (v[0] > 0))
            n_pairs += 1
            w.writerow([d, cid, dn, m[0], f"{m[1]:.2f}", f"{m[2]:.2f}", m_scan,
                        v[0], f"{v[1]:.2f}", f"{v[2]:.2f}", v_scan, one_sided])

    detections_path = out_dir / "detections.json"
    detections_path.write_text(json.dumps({
        "n_detections": len(dets),
        "note": "one entry = one validated satellite hotspot detection — an observation, not necessarily a fire",
        "detections": dets,
    }, separators=(",", ":")), encoding="utf-8")

    coverage = {
        "days_retrieved": sum(1 for st in mask.values() if st == "retrieved"),
        "days_failed": sum(1 for st in mask.values() if st == "failed"),
        "first_date": dates_min, "last_date": dates_max,
        "filter_counts": counts,
        "retrieval_mask": {d.isoformat(): st for d, st in sorted(mask.items())},
    }
    (out_dir / "coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    print(f"[match] units={n_pairs} rows_read={counts['rows_read']} "
          f"excluded={ {k: v for k, v in counts.items() if k != 'rows_read' and v} }")
    return matched_path, coverage
