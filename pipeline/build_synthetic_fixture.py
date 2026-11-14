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

import csv
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fixtures" / "FIXTURE_SYNTHETIC" / "riau"
SLUG = "w100_s-2_e105_n1"
START = date(2012, 1, 20)
END = date(2026, 7, 31)
WEST, SOUTH, EAST, NORTH = 100.0, -2.0, 105.0, 1.0
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

def gen_source(source: str, rnd):
    rows = []
    is_modis = source.startswith("MODIS")
    day = START
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
            cx, cy = CENTERS[rnd.randrange(len(CENTERS))]
            lat = round(min(max(cy + rnd.gauss(0, 0.35), SOUTH + 0.01), NORTH - 0.01), 5)
            lon = round(min(max(cx + rnd.gauss(0, 0.45), WEST + 0.01), EAST - 0.01), 5)
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

def main() -> int:
    rnd = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    rel_files = {}
    ledgers = []
    for source in ("MODIS_SP", "VIIRS_SNPP_SP"):
        rows = gen_source(source, rnd)
        rel = f"data/fixtures/FIXTURE_SYNTHETIC/riau/{source}/{SLUG}/normalized.csv"
        write_norm(ROOT / rel, rows)
        body = (ROOT / rel).read_bytes()
        rel_files[rel] = hashlib.sha256(body).hexdigest()
        print(f"[fixture] {source}: {len(rows)} rows -> {rel}")

    # Ledger: every requested day retrieved (ok/ok_empty by day), plus 3 failed
    # windows to exercise retrieval-gap states downstream.
    window = START
    day_status = {}
    while window <= END:
        we = min(window + timedelta(days=4), END)
        day_rows = 0
        d = window
        while d <= we:
            # reconstructed from what gen_source produced is expensive; mark ok_empty
            # unless the season says detections are plausible (approximation is fine:
            # the ledger only drives missingness masks, not row contents).
            s = season(d)
            day_status[d] = "ok_empty" if s < 0.10 and rnd.random() < 0.6 else "ok"
            d += timedelta(days=1)
        status = "ok_empty" if all(v == "ok_empty" for v in day_status.values() if True) else "ok"
        rel = f"data/fixtures/FIXTURE_SYNTHETIC/riau/MODIS_SP/{SLUG}/{window.isoformat()}_{we.isoformat()}.csv"
        ledgers.append({"action": "fetch", "source": "MODIS_SP", "bbox": "100,-2,105,1",
                        "window_start": window.isoformat(), "window_end": we.isoformat(),
                        "days": (we - window).days + 1, "path": rel, "status": status,
                        "sha256": rel_files.get(rel, "")})
        window = we + timedelta(days=1)
    for fw in ((date(2013, 6, 10), date(2013, 6, 14)), (date(2017, 11, 3), date(2017, 11, 7)),
               (date(2021, 1, 2), date(2021, 1, 6))):
        ledgers.append({"action": "fetch", "source": "MODIS_SP", "bbox": "100,-2,105,1",
                        "window_start": fw[0].isoformat(), "window_end": fw[1].isoformat(),
                        "days": (fw[1] - fw[0]).days + 1,
                        "path": f"data/fixtures/FIXTURE_SYNTHETIC/riau/MODIS_SP/{SLUG}/{fw[0].isoformat()}_{fw[1].isoformat()}.csv",
                        "status": "failed", "error": "HTTP 503; retried after 30s (synthetic)"})
    led_path = OUT / "fetch_ledger.jsonl"
    with led_path.open("w", encoding="utf-8") as fh:
        for e in ledgers:
            fh.write(json.dumps(e) + "\n")

    prov = {
        "fixture_id": "FIXTURE_SYNTHETIC",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "pipeline/build_synthetic_fixture.py",
        "seed": SEED,
        "use_note": ("Every value is INVENTED. This fixture exists so D/E can build and "
                     "test the app end-to-end before real validated caches are shared. "
                     "It is NEVER a claimed result and the UI must show the MOCK badge "
                     "whenever fixture data is served."),
        "shape": "seasonal Aug-Oct peak + small Feb bump; 3 failed windows for gap states",
    }
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"[fixture] ledger  -> {led_path.relative_to(ROOT).as_posix()}")
    print(f"[fixture] label   -> FIXTURE_SYNTHETIC (never a claimed result)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
