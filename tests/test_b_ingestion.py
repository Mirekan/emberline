"""B-04/B-05 ingestion test — EmberLine Role B.

Tests pipeline/validate.py against a small SYNTHETIC fixture clearly labeled
FIXTURE_SYNTHETIC. Synthetic rows live only under this test; they are never
used as download or evidence data (plan: a fixture is never a claimed result).

Checks the contract C relies on (config/params.yaml PROTO-C01-v0.9):
- exact-identity dedupe (satellite, version, date, time, lat, lon, daynight)
- original confidence kept verbatim, scale recorded, never converted
- drops counted per reason; nothing silently discarded
- failed retrieval vs zero detections vs out-of-range days stay distinct
- hash mismatch -> file quarantined, never trusted

Run standalone:  python tests/test_b_ingestion.py
Run under pytest: python -m pytest tests/test_b_ingestion.py -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_validate():
    spec = importlib.util.spec_from_file_location("validate", ROOT / "pipeline" / "validate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_fetch():
    spec = importlib.util.spec_from_file_location("fetch_firms", ROOT / "pipeline" / "fetch_firms.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MODIS_HEADER = ("latitude,longitude,brightness,scan,track,acq_date,acq_time,"
                "satellite,instrument,confidence,version,bright_t31,frp,daynight,type")

# FIXTURE_SYNTHETIC — invented values, NOT from any FIRMS download.
GOOD_A = "-0.50000,102.50000,320.5,0.42,0.38,2015-09-01,0315,Aqua,MODIS,84,6.1,290.1,12.50,D,0"
GOOD_B = "-0.60000,102.60000,321.5,0.42,0.38,2015-09-02,2110,Aqua,MODIS,55,6.1,291.2,3.25,N,0"
DUP_A = "-0.50000,102.50000,320.5,0.42,0.38,2015-09-01,0315,Aqua,MODIS,84,6.1,290.1,12.50,D,0"
BAD_LAT = "NOT_A_NUMBER,102.50000,320.5,0.42,0.38,2015-09-01,0315,Aqua,MODIS,84,6.1,290.1,12.50,D,0"
NEG_FRP = "-0.70000,102.70000,320.5,0.42,0.38,2015-09-01,0315,Aqua,MODIS,84,6.1,290.1,-4.00,D,0"
BAD_TIME = "-0.80000,102.80000,320.5,0.42,0.38,2015-09-01,2500,Aqua,MODIS,84,6.1,290.1,1.00,D,0"
OUTSIDE_DAY = "-0.90000,102.90000,320.5,0.42,0.38,2015-09-20,0315,Aqua,MODIS,84,6.1,290.1,1.00,D,0"
NEARBY_LEGIT = "-0.50002,102.50003,321.0,0.42,0.38,2015-09-01,0315,Aqua,MODIS,60,6.1,290.4,9.00,D,0"


def build_fixture(tmp: Path):
    validate = _load_validate()
    slug = "w102_s-1_e103_n0"
    raw_dir = tmp / "data" / "raw" / "MODIS_SP" / slug
    raw_dir.mkdir(parents=True)
    body = "\n".join([MODIS_HEADER, GOOD_A, GOOD_B, DUP_A, BAD_LAT,
                      NEG_FRP, BAD_TIME, OUTSIDE_DAY, NEARBY_LEGIT]) + "\n"
    path = raw_dir / "2015-09-01_2015-09-05.csv"
    path.write_text(body, encoding="utf-8")

    manifests = tmp / "data" / "manifests"
    manifests.mkdir(parents=True)
    ledger = manifests / "fetch_ledger.jsonl"
    # Hash the actual written bytes (write_text may translate newlines on Windows).
    file_bytes = path.read_bytes()
    entry = {
        "action": "fetch", "source": "MODIS_SP", "bbox": "102,-1,103,0",
        "window_start": "2015-09-01", "window_end": "2015-09-05", "days": 5,
        "path": f"data/raw/MODIS_SP/{slug}/2015-09-01_2015-09-05.csv",
        "status": "ok", "rows": 8, "bytes": len(file_bytes),
        "sha256": hashlib.sha256(file_bytes).hexdigest(),
    }
    ledger.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    # Redirect the module's paths into the temp sandbox.
    validate.ROOT = tmp
    validate.RAW_DIR = tmp / "data" / "raw"
    validate.PROCESSED_DIR = tmp / "data" / "processed"
    validate.LEDGER_DIR = manifests
    validate.LEDGER_PATH = ledger
    return validate, slug, body


def run_all_checks() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        checks.append((name, bool(cond), detail))

    validate = _load_validate()
    fetch = _load_fetch()

    # -- parse_payload: empty vs failure vs non-CSV --------------------------
    rows, fields, empty = fetch.parse_payload(b"")
    check("empty payload recognized", rows == 0 and empty, f"rows={rows} empty={empty}")
    rows, fields, empty = fetch.parse_payload(f"{MODIS_HEADER}\n{GOOD_A}\n".encode())
    check("payload rows counted", rows == 1 and "latitude" in fields[0],
          f"rows={rows} fields={fields[:2]}")
    try:
        fetch.parse_payload(b"<html>error page</html>")
        check("non-CSV payload rejected", False, "no exception raised")
    except fetch.FetchError:
        check("non-CSV payload rejected", True)

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        mod, slug, body = build_fixture(tmp)

        report = mod.run_source("MODIS_SP", slug)
        out_csv = mod.PROCESSED_DIR / "MODIS_SP" / slug / "normalized.csv"
        lines = out_csv.read_text(encoding="utf-8").strip().splitlines()

        # -- core counts: 9 raw rows -> 4 kept (A, B, nearby legit) ----------
        check("raw rows counted", report["rows_raw"] == 8, f"got {report['rows_raw']}")
        check("kept = good rows + nearby legit (3)",
              report["rows_kept"] == 3, f"got {report['rows_kept']}")
        check("exact-identity duplicate dropped",
              report["drop_counts"].get("duplicate_observation") == 1,
              str(report["drop_counts"]))
        check("nearby legitimate detection NOT deduped",
              report["drop_counts"].get("duplicate_observation", 0) == 1,
              "NEARBY_LEGIT differs beyond forbidden rounding tolerance")
        check("out-of-range latitude dropped",
              report["drop_counts"].get("bad_latlon") == 1, str(report["drop_counts"]))
        check("negative FRP dropped",
              report["drop_counts"].get("negative_frp") == 1, str(report["drop_counts"]))
        check("invalid acq_time dropped",
              report["drop_counts"].get("bad_acq_time") == 1, str(report["drop_counts"]))
        check("date outside window dropped",
              report["drop_counts"].get("date_outside_window") == 1, str(report["drop_counts"]))
        check("hash verified against ledger",
              report["hash_checked"] == 1 and report["hash_mismatch"] == 0,
              f"checked={report['hash_checked']} mismatch={report['hash_mismatch']}")

        # -- confidence contract ---------------------------------------------
        header = lines[0].split(",")
        conf_idx = header.index("confidence_raw")
        scale_idx = header.index("conf_scale")
        values = [ln.split(",") for ln in lines[1:]]
        check("confidence kept verbatim (percent scale)",
              all(v[conf_idx].isdigit() and int(v[conf_idx]) <= 100 for v in values)
              and all(v[scale_idx] == "percent" for v in values),
              f"conf={[v[conf_idx] for v in values]}")
        sat_idx = header.index("satellite")
        check("satellite preserved (Aqua filter possible downstream)",
              all(v[sat_idx] == "Aqua" for v in values))

        # -- four-state missingness ------------------------------------------
        cov = report["coverage"]
        check("retrieved days counted", cov["days_retrieved"] == 5, str(cov))
        check("zero-detection days counted separately from detections",
              cov["days_zero_detections"] == 3 and cov["days_with_detections"] == 2,
              f"zero={cov['days_zero_detections']} det={cov['days_with_detections']}")

        # -- hash mismatch quarantine ----------------------------------------
        mismatched = (tmp / "data" / "raw" / "MODIS_SP" / slug / "2015-09-06_2015-09-10.csv")
        bad = f"{MODIS_HEADER}\n{GOOD_A}\n".encode()
        mismatched.write_bytes(bad)
        entry_bad = {
            "action": "fetch", "source": "MODIS_SP", "bbox": "102,-1,103,0",
            "window_start": "2015-09-06", "window_end": "2015-09-10", "days": 5,
            "path": f"data/raw/MODIS_SP/{slug}/2015-09-06_2015-09-10.csv",
            "status": "ok", "rows": 1, "bytes": len(bad),
            "sha256": hashlib.sha256(b"tampered").hexdigest(),
        }
        with mod.LEDGER_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry_bad) + "\n")
        report2 = mod.run_source("MODIS_SP", slug)
        check("hash-mismatch file quarantined, rows never trusted",
              report2["hash_mismatch"] == 1
              and report2["drop_counts"].get("file_hash_mismatch") == 1,
              f"mismatch={report2['hash_mismatch']} drops={report2['drop_counts']}")

    return checks


def main() -> int:
    checks = run_all_checks()
    failed = 0
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{mark}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    print(f"\nB ingestion contract: {len(checks) - failed}/{len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
