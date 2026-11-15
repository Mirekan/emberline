#!/usr/bin/env python3
"""Build FIXTURE_SYNTHETIC (clearly labeled; NEVER a claimed result).

Generates detection rows in the EXACT schema written by pipeline/validate.py
(OUT_COLUMNS) so C/D/E can build and test the app end-to-end before the real
validated caches are shared. Seasonal shape mimics the Riau peatland fire
regime (Aug-Oct peak + small Feb bump) but every value is INVENTED.

Outputs under data/fixtures/FIXTURE_SYNTHETIC/riau/:
  MODIS_SP/w100_s-2_e105_n1/normalized.csv      (satellite Aqua + a little Terra)
  VIIRS_SNPP_SP/w100_s-2_e105_n1/normalized.csv (satellite N)
  fetch_ledger.jsonl   (ok/ok_empty + a few failed windows; sha256 per file)
  provenance.json      (FIXTURE_SYNTHETIC label + never-a-result note)

Stdlib only. Run:  python pipeline/build_synthetic_fixture.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AOI_CONFIGS = {
    "riau": {
        "slug": "w100_s-2_e105_n1",
        "west": 100.0, "south": -2.0, "east": 105.0, "north": 1.0,
        # Accurate peatland fire centers in Riau province (Pelalawan, Siak, Bengkalis, Kampar, Inhil)
        "centers": [(102.4, 0.45), (102.0, 0.75), (101.8, 0.92), (101.5, 0.38), (102.9, -0.25)],
    },
    "central_kalimantan": {
        "slug": "w113_s-3_e116_n0",
        "west": 113.0, "south": -3.0, "east": 116.0, "north": 0.0,
        # Accurate peatland fire centers in Central Kalimantan (Pulang Pisau MRP, Kapuas, Sebangau)
        "centers": [(114.1, -2.3), (114.5, -2.6), (113.8, -2.0), (113.7, -2.5), (114.8, -2.2)],
    },
    "south_sumatra": {
        "slug": "w103_s-5_e106_n-2",
        "west": 103.0, "south": -5.0, "east": 106.0, "north": -2.0,
        # Accurate peatland fire centers in South Sumatra (Ogan Komering Ilir / OKI, Banyuasin)
        "centers": [(105.0, -3.4), (105.3, -3.6), (104.8, -3.1), (105.1, -3.8), (104.4, -2.8)],
    },
    "jambi": {
        "slug": "w102_s-3_e104.5_n-1",
        "west": 102.0, "south": -3.0, "east": 104.5, "north": -1.0,
        # Accurate peatland fire centers in Jambi (Muaro Jambi, Tanjung Jabung)
        "centers": [(103.8, -1.4), (103.5, -1.6), (104.0, -1.3), (103.6, -1.8), (103.2, -1.5)],
    },
    "merauke": {
        "slug": "w137_s-9_e141_n-7",
        "west": 137.0, "south": -9.0, "east": 141.0, "north": -7.0,
        # Accurate savanna fire centers in Merauke, Southern Papua
        "centers": [(140.4, -8.3), (140.2, -8.1), (139.8, -8.0), (140.5, -7.8), (140.0, -7.5)],
    },
}

START = date(2012, 1, 20)
END = date(2026, 7, 31)
SEED = 20261114

OUT_COLUMNS = ["source", "satellite", "instrument", "acq_datetime_utc", "acq_date",
               "acq_time_utc", "latitude", "longitude", "brightness_kelvin",
               "bright_t31_kelvin", "confidence_raw", "conf_scale", "frp_mw",
               "daynight", "scan", "track", "version", "type"]

# Seasonal shape: peak DOY ~258 (mid Sep), width ~34d; small Feb bump.
def season(d: date) -> float:
    doy = d.timetuple().tm_yday
    g = lambda c, w: math.exp(-((doy - c) / w) ** 2)
    return 1.9 * g(258, 34) + 0.42 * g(60, 16) + 0.08

# A few hotspot centers inside the AOI (invented).
CENTERS = [(101.8, -0.6), (102.9, -1.4), (104.1, -0.2), (101.0, -1.8)]

def conf_modis(rnd) -> str:
    u = rnd.random()
    if u < 0.68: return str(rnd.randint(30, 100))
    if u < 0.98: return str(rnd.randint(0, 29))
    return "unknown"          # exercised: excluded & counted downstream

def conf_viirs(rnd) -> str:
    u = rnd.random()
    if u < 0.75: return "h"
    if u < 0.97: return "n"
    return "l"

def gen_source(source: str, rnd, cfg: dict):
    rows = []
    is_modis = source.startswith("MODIS")
    day = START
    west, south, east, north = cfg["west"], cfg["south"], cfg["east"], cfg["north"]
    centers = cfg["centers"]
    while day <= END:
        s = season(day)
        if is_modis:
            n = int(9 * s * (0.7 + 0.6 * rnd.random()))
        else:
            n = int(16 * s * (0.7 + 0.6 * rnd.random()))
        # A few windows with zero detections at random (exercises valid_zero).
        if rnd.random() < 0.03:
            n = 0
        for _ in range(n):
            cx, cy = centers[rnd.randrange(len(centers))]
            lat = round(min(max(cy + rnd.gauss(0, 0.18), south + 0.01), north - 0.01), 5)
            lon = round(min(max(cx + rnd.gauss(0, 0.22), west + 0.01), east - 0.01), 5)
            frp = round(max(0.2, rnd.expovariate(1 / 6.5)), 2)
            if is_modis:
                sat = "Aqua" if rnd.random() < 0.58 else "Terra"
                t = "1330" if (rnd.random() < 0.5) == (sat == "Aqua") else "0130" if sat == "Aqua" else "2230" if rnd.random() < 0.5 else "1030"
                if sat == "Terra":
                    t = rnd.choice(["1030", "2230"])
                conf, scale = conf_modis(rnd), "percent"
                temp = round(310 + rnd.random() * 40, 2)
            else:
                sat = "N"
                t = "1330" if rnd.random() < 0.5 else "0130"
                conf, scale = conf_viirs(rnd), "letter"
                temp = round(320 + rnd.random() * 50, 2)
            dn = "D" if 600 <= int(t) < 1800 else "N"
            hh, mm = t[:2], t[2:]
            rows.append({
                "source": source, "satellite": sat, "instrument": "MODIS" if is_modis else "VIIRS",
                "acq_datetime_utc": f"{day.isoformat()}T{hh}:{mm}:00Z",
                "acq_date": day.isoformat(), "acq_time_utc": t,
                "latitude": f"{lat:.5f}", "longitude": f"{lon:.5f}",
                "brightness_kelvin": f"{temp:.2f}",
                "bright_t31_kelvin": f"{temp - rnd.uniform(5, 25):.2f}",
                "confidence_raw": conf, "conf_scale": scale,
                "frp_mw": f"{frp:.2f}", "daynight": dn,
                "scan": f"{rnd.uniform(0.3, 2.0):.2f}", "track": f"{rnd.uniform(0.3, 2.0):.2f}",
                "version": "6.1" if is_modis else "2", "type": "0",
            })
        day += timedelta(days=1)
    return rows

def write_norm(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
        w.writeheader()
        w.writerows(rows)

def build_for_aoi(aoi: str, rnd: random.Random) -> None:
    cfg = AOI_CONFIGS[aoi]
    slug = cfg["slug"]
    out_dir = ROOT / "data" / "fixtures" / "FIXTURE_SYNTHETIC" / aoi
    out_dir.mkdir(parents=True, exist_ok=True)
    rel_files = {}
    ledgers = []
    for source in ("MODIS_SP", "VIIRS_SNPP_SP"):
        rows = gen_source(source, rnd, cfg)
        rel = f"data/fixtures/FIXTURE_SYNTHETIC/{aoi}/{source}/{slug}/normalized.csv"
        write_norm(ROOT / rel, rows)
        body = (ROOT / rel).read_bytes()
        rel_files[rel] = hashlib.sha256(body).hexdigest()
        print(f"[fixture] {aoi} {source}: {len(rows)} rows -> {rel}")

    bbox_str = f"{cfg['west']},{cfg['south']},{cfg['east']},{cfg['north']}"
    window = START
    day_status = {}
    while window <= END:
        we = min(window + timedelta(days=4), END)
        d = window
        while d <= we:
            s = season(d)
            day_status[d] = "ok_empty" if s < 0.10 and rnd.random() < 0.6 else "ok"
            d += timedelta(days=1)
        status = "ok_empty" if all(v == "ok_empty" for v in day_status.values() if True) else "ok"
        rel = f"data/fixtures/FIXTURE_SYNTHETIC/{aoi}/MODIS_SP/{slug}/{window.isoformat()}_{we.isoformat()}.csv"
        ledgers.append({"action": "fetch", "source": "MODIS_SP", "bbox": bbox_str,
                        "window_start": window.isoformat(), "window_end": we.isoformat(),
                        "days": (we - window).days + 1, "path": rel, "status": status,
                        "sha256": rel_files.get(rel, "")})
        window = we + timedelta(days=1)
    for fw in ((date(2013, 6, 10), date(2013, 6, 14)), (date(2017, 11, 3), date(2017, 11, 7)),
               (date(2021, 1, 2), date(2021, 1, 6))):
        ledgers.append({"action": "fetch", "source": "MODIS_SP", "bbox": bbox_str,
                        "window_start": fw[0].isoformat(), "window_end": fw[1].isoformat(),
                        "days": (fw[1] - fw[0]).days + 1,
                        "path": f"data/fixtures/FIXTURE_SYNTHETIC/{aoi}/MODIS_SP/{slug}/{fw[0].isoformat()}_{fw[1].isoformat()}.csv",
                        "status": "failed", "error": "HTTP 503; retried after 30s (synthetic)"})
    led_path = out_dir / "fetch_ledger.jsonl"
    with led_path.open("w", encoding="utf-8") as fh:
        for e in ledgers:
            fh.write(json.dumps(e) + "\n")

    prov = {
        "fixture_id": "FIXTURE_SYNTHETIC",
        "aoi": aoi,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "pipeline/build_synthetic_fixture.py",
        "seed": SEED,
        "use_note": ("Every value is INVENTED. This fixture exists so D/E can build and "
                     "test the app end-to-end before real validated caches are shared. "
                     "It is NEVER a claimed result and the UI must show the MOCK badge "
                     "whenever fixture data is served."),
        "shape": "seasonal Aug-Oct peak + small Feb bump; 3 failed windows for gap states",
    }
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"[fixture] {aoi} ledger -> {led_path.relative_to(ROOT).as_posix()}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aoi", default="all", choices=["riau", "central_kalimantan", "south_sumatra", "jambi", "merauke", "all"])
    args = ap.parse_args()
    rnd = random.Random(SEED)
    aois = list(AOI_CONFIGS.keys()) if args.aoi == "all" else [args.aoi]
    for a in aois:
        build_for_aoi(a, rnd)
    print(f"[fixture] label   -> FIXTURE_SYNTHETIC (never a claimed result)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
