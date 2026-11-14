#!/usr/bin/env python3
"""EmberLine validation and normalization (Role B: tasks B-04 and B-05).

Reads the immutable raw cache written by fetch_firms.py, validates rows
against source-specific schemas, dedupes true duplicate observations,
writes a normalized CSV, and produces evidence for gate G1:

  data/processed/<source>/<slug>/normalized.csv
  data/manifests/validation_report_<source>_<slug>.json   (git-ignored)
  data/manifests/ingest_evidence_<slug>.md                (git-ignored)

Aligned with config/params.yaml (PROTO-C01-v0.9):
- dedupe key = exact row identity per source:
  (source, satellite, version, acq_date, acq_time, latitude, longitude,
  daynight); coordinate rounding is FORBIDDEN in the key (rounding only
  in output formatting). Cross-platform / nearby-overpass detections are
  never deduplicated (the key includes satellite + acq_time).
- original confidence values kept verbatim in confidence_raw; their scale
  is recorded in conf_scale, never converted. Confidence filtering is C's
  decision (params.yaml confidence_filters), not applied here.
- four-state missingness (params.yaml): days_failed_retrieval maps to
  failed_request, days_zero_detections to success_zero_detections, days
  outside the requested range to unavailable_archive; B provides the
  retrieval masks per source/day in the JSON report.
- raw file hashes re-verified against the fetch ledger before use; a
  mismatched file is skipped and counted, never trusted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
LEDGER_DIR = ROOT / "data" / "manifests"
LEDGER_PATH = LEDGER_DIR / "fetch_ledger.jsonl"

REQUIRED_COLUMNS = [
    "latitude", "longitude", "scan", "track", "acq_date", "acq_time",
    "satellite", "instrument", "confidence", "version", "frp", "daynight",
]

SCHEMAS = {
    "MODIS_SP":         {"temp_col": "brightness", "t31_col": "bright_t31", "conf_scale": "percent", "allowed_satellites": {"Terra", "Aqua"}},
    "MODIS_NRT":        {"temp_col": "brightness", "t31_col": "bright_t31", "conf_scale": "letter",   "allowed_satellites": {"Terra", "Aqua"}},
    "VIIRS_SNPP_SP":    {"temp_col": "bright_ti4", "t31_col": "bright_ti5", "conf_scale": "letter",   "allowed_satellites": None},
    "VIIRS_SNPP_NRT":   {"temp_col": "bright_ti4", "t31_col": "bright_ti5", "conf_scale": "letter",   "allowed_satellites": None},
    "VIIRS_NOAA20_SP":  {"temp_col": "bright_ti4", "t31_col": "bright_ti5", "conf_scale": "letter",   "allowed_satellites": None},
    "VIIRS_NOAA20_NRT": {"temp_col": "bright_ti4", "t31_col": "bright_ti5", "conf_scale": "letter",   "allowed_satellites": None},
    "VIIRS_NOAA21_SP":  {"temp_col": "bright_ti4", "t31_col": "bright_ti5", "conf_scale": "letter",   "allowed_satellites": None},
    "VIIRS_NOAA21_NRT": {"temp_col": "bright_ti4", "t31_col": "bright_ti5", "conf_scale": "letter",   "allowed_satellites": None},
}

OUT_COLUMNS = [
    "source", "satellite", "instrument", "acq_datetime_utc", "acq_date", "acq_time_utc",
    "latitude", "longitude", "brightness_kelvin", "bright_t31_kelvin",
    "confidence_raw", "conf_scale", "frp_mw", "daynight", "scan", "track", "version", "type",
]

BBOX_TOL = 1e-4


def bbox_from_slug(slug: str):
    m = re.fullmatch(r"w(-?[\d.]+)_s(-?[\d.]+)_e(-?[\d.]+)_n(-?[\d.]+)", slug)
    if not m:
        sys.exit(f"ERROR: cannot parse bbox slug: {slug}")
    west, south, east, north = (float(v) for v in m.groups())
    return west, south, east, north


def ledger_windows(source: str, slug: str) -> list:
    entries = []
    if LEDGER_PATH.exists():
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("action") == "fetch" and entry.get("source") == source and slug in (entry.get("path") or ""):
                entries.append(entry)
    return entries


def day_retrieval_map(windows: list) -> dict:
    status = {}
    for w in windows:
        try:
            ws = date.fromisoformat(w["window_start"])
            we = date.fromisoformat(w["window_end"])
        except (KeyError, ValueError):
            continue
        st = "retrieved" if w.get("status") in ("ok", "ok_empty") else "failed"
        d = ws
        while d <= we:
            if st == "retrieved" or status.get(d) != "retrieved":
                status[d] = st
            d += timedelta(days=1)
    return status


def validate_row(row, source, schema, bbox, window_start, window_end, seen_keys):
    """Return (record, None) or (None, drop_reason)."""
    try:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
    except (TypeError, ValueError):
        return None, "bad_latlon"
    west, south, east, north = bbox
    if not (west - BBOX_TOL <= lon <= east + BBOX_TOL and south - BBOX_TOL <= lat <= north + BBOX_TOL):
        return None, "out_of_bbox"

    d = (row.get("acq_date") or "").strip()
    try:
        acq_d = date.fromisoformat(d)
    except ValueError:
        return None, "bad_acq_date"
    if not (window_start <= acq_d <= window_end):
        return None, "date_outside_window"

    t = (row.get("acq_time") or "").strip()
    if not t.isdigit() or len(t) > 4:
        return None, "bad_acq_time"
    t4 = t.zfill(4)
    if int(t4[:2]) > 23 or int(t4[2:]) > 59:
        return None, "bad_acq_time"

    try:
        frp = float(row["frp"])
    except (TypeError, ValueError):
        return None, "bad_frp"
    if frp < 0:
        return None, "negative_frp"

    sat = (row.get("satellite") or "").strip()
    if not sat or (schema["allowed_satellites"] and sat not in schema["allowed_satellites"]):
        return None, "unexpected_satellite"

    dn = (row.get("daynight") or "").strip()
    if dn not in ("D", "N"):
        return None, "bad_daynight"

    ver = (row.get("version") or "").strip()

    # Temperature is contextual, not the core metric: keep the row if absent.
    try:
        temp = f"{float(row[schema['temp_col']]):.2f}"
    except (TypeError, ValueError):
        temp = ""
    try:
        t31 = f"{float(row[schema['t31_col']]):.2f}"
    except (TypeError, ValueError):
        t31 = ""

    # PROTO-C01-v0.9 dedupe: exact row identity, coordinate rounding forbidden.
    # Windows are date-disjoint by construction, so per-file scope is sufficient.
    key = (source, sat, ver, d, t4, lat, lon, dn)
    if key in seen_keys:
        return None, "duplicate_observation"
    seen_keys.add(key)

    return {
        "source": source,
        "satellite": sat,
        "instrument": (row.get("instrument") or "").strip(),
        "acq_datetime_utc": f"{d}T{t4[:2]}:{t4[2:]}:00Z",
        "acq_date": d,
        "acq_time_utc": t4,
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "brightness_kelvin": temp,
        "bright_t31_kelvin": t31,
        "confidence_raw": (row.get("confidence") or "").strip(),
        "conf_scale": schema["conf_scale"],
        "frp_mw": f"{frp:.2f}",
        "daynight": dn,
        "scan": (row.get("scan") or "").strip(),
        "track": (row.get("track") or "").strip(),
        "version": ver,
        "type": (row.get("type") or "").strip(),
    }, None


def run_source(source: str, slug: str) -> dict:
    if source not in SCHEMAS:
        sys.exit(f"ERROR: unknown source schema: {source}")
    schema = SCHEMAS[source]
    bbox = bbox_from_slug(slug)
    raw_dir = RAW_DIR / source / slug
    files = sorted(raw_dir.glob("*.csv"))
    windows = ledger_windows(source, slug)
    ledger_by_path = {w.get("path"): w for w in windows if w.get("path")}

    counters = {
        "rows_raw": 0,
        "rows_kept": 0,
        "drop": Counter(),
        "schema_variants": Counter(),
        "per_year": defaultdict(Counter),
        "dates_with_detections": set(),
        "hash_checked": 0,
        "hash_mismatch": 0,
        "files_total": len(files),
        "files_missing_from_ledger": 0,
    }

    out_dir = PROCESSED_DIR / source / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "normalized.csv"

    with out_path.open("w", newline="", encoding="utf-8") as out_fh:
        writer = csv.DictWriter(out_fh, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        for path in files:
            try:
                ws = date.fromisoformat(path.stem.split("_")[0])
                we = date.fromisoformat(path.stem.split("_")[1])
            except (ValueError, IndexError):
                counters["drop"]["unparseable_filename"] += 1
                continue

            rel = path.relative_to(ROOT).as_posix()
            entry = ledger_by_path.get(rel)
            if entry is None:
                counters["files_missing_from_ledger"] += 1
            elif entry.get("sha256"):
                counters["hash_checked"] += 1
                if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                    counters["hash_mismatch"] += 1
                    with path.open(newline="", encoding="utf-8") as fh:
                        n = sum(1 for _ in csv.reader(fh)) - 1
                    counters["rows_raw"] += max(n, 0)
                    counters["drop"]["file_hash_mismatch"] += max(n, 0)
                    continue

            seen = set()
            with path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                fieldnames = reader.fieldnames or []
                counters["schema_variants"][",".join(fieldnames)] += 1
                needed = REQUIRED_COLUMNS + [schema["temp_col"], schema["t31_col"]]
                if any(c not in fieldnames for c in needed):
                    n = sum(1 for _ in reader)
                    counters["rows_raw"] += n
                    counters["drop"]["file_missing_columns"] += n
                    continue
                for row in reader:
                    counters["rows_raw"] += 1
                    rec, reason = validate_row(row, source, schema, bbox, ws, we, seen)
                    if rec is None:
                        counters["drop"][reason] += 1
                    else:
                        counters["rows_kept"] += 1
                        writer.writerow(rec)
                        year = rec["acq_date"][:4]
                        counters["per_year"][year]["total"] += 1
                        counters["per_year"][year][rec["satellite"]] += 1
                        counters["dates_with_detections"].add(rec["acq_date"])

    day_status = day_retrieval_map(windows)
    starts = [date.fromisoformat(w["window_start"]) for w in windows if w.get("window_start")]
    ends = [date.fromisoformat(w["window_end"]) for w in windows if w.get("window_end")]
    if not starts and files:
        starts = [date.fromisoformat(f.stem.split("_")[0]) for f in files]
        ends = [date.fromisoformat(f.stem.split("_")[1]) for f in files]
    if starts:
        req_start, req_end = min(starts), max(ends)
        days_total = (req_end - req_start).days + 1
    else:
        req_start = req_end = None
        days_total = 0
    retrieved_days = {d.isoformat() for d, st in day_status.items() if st == "retrieved"}
    failed_days = {d.isoformat() for d, st in day_status.items() if st == "failed"}
    det_days = counters["dates_with_detections"]  # already ISO date strings
    zero_days = retrieved_days - det_days

    satellite_totals = Counter()
    for year_counter in counters["per_year"].values():
        for sat, n in year_counter.items():
            if sat != "total":
                satellite_totals[sat] += n
    det_dates_sorted = sorted(det_days)

    report = {
        "source": source,
        "slug": slug,
        "bbox": ",".join(f"{v:g}" for v in bbox),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files_total": counters["files_total"],
        "hash_checked": counters["hash_checked"],
        "hash_mismatch": counters["hash_mismatch"],
        "files_missing_from_ledger": counters["files_missing_from_ledger"],
        "rows_raw": counters["rows_raw"],
        "rows_kept": counters["rows_kept"],
        "drop_counts": dict(counters["drop"]),
        "schema_variants": dict(counters["schema_variants"]),
        "coverage": {
            "requested_start": req_start.isoformat() if req_start else None,
            "requested_end": req_end.isoformat() if req_end else None,
            "days_total": days_total,
            "days_retrieved": len(retrieved_days),
            "days_failed_retrieval": len(failed_days),
            "days_with_detections": len(det_days & retrieved_days),
            "days_zero_detections": len(zero_days),
            "days_unavailable_archive": max(days_total - len(retrieved_days) - len(failed_days), 0),
        },
        "satellite_breakdown": dict(satellite_totals),
        "first_detection": det_dates_sorted[0] if det_dates_sorted else None,
        "last_detection": det_dates_sorted[-1] if det_dates_sorted else None,
        "per_year": {y: dict(c) for y, c in sorted(counters["per_year"].items())},
        "retrieval_mask": {d.isoformat(): st for d, st in sorted(day_status.items())},
        "failed_windows": [
            {"path": w.get("path"), "error": (w.get("error") or "")[:120]}
            for w in windows if w.get("status") == "failed"
        ][:20],
    }
    report_path = LEDGER_DIR / f"validation_report_{source}_{slug}.json"
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[{source}/{slug}] rows raw={counters['rows_raw']} kept={counters['rows_kept']} "
          f"drops={dict(counters['drop']) or 'none'}")
    print(f"[{source}/{slug}] coverage retrieved={len(retrieved_days)} failed={len(failed_days)} "
          f"zero={len(zero_days)} detections={len(det_days)} hash_mismatch={counters['hash_mismatch']}")
    print(f"[{source}/{slug}] normalized -> {out_path.relative_to(ROOT).as_posix()}")
    print(f"[{source}/{slug}] report    -> {report_path.relative_to(ROOT).as_posix()}")
    return report


def build_evidence(slug: str, sources: list) -> None:
    reports = {}
    for source in sources:
        rp = LEDGER_DIR / f"validation_report_{source}_{slug}.json"
        if rp.exists():
            reports[source] = json.loads(rp.read_text(encoding="utf-8"))
    lines = []
    a = lines.append
    a(f"# Ingest evidence - {slug} (B-05 / gate G1)")
    a("")
    a(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')} by pipeline/validate.py")
    a("")
    for source, rep in reports.items():
        cov = rep["coverage"]
        a(f"## {source}")
        a("")
        a(f"- requested range: {cov['requested_start']} .. {cov['requested_end']} ({cov['days_total']} days)")
        a(f"- retrieval: {cov['days_retrieved']} retrieved / {cov['days_failed_retrieval']} failed "
          f"/ {cov['days_zero_detections']} retrieved-with-zero-detections")
        a(f"- days with detections: {cov['days_with_detections']}")
        a(f"- rows: raw {rep['rows_raw']} -> kept {rep['rows_kept']}")
        drop_s = ", ".join(f"{k}={v}" for k, v in sorted(rep["drop_counts"].items()) if v) or "none"
        a(f"- drops: {drop_s}")
        a(f"- hash: {rep['hash_checked']} files checked, {rep['hash_mismatch']} mismatch")
        a(f"- satellite: {rep['satellite_breakdown'] or 'n/a'}")
        a(f"- detections span: {rep['first_detection']} .. {rep['last_detection']}")
        per_year = rep.get("per_year", {})
        if per_year:
            a("- per-year kept rows:")
            for y in sorted(per_year):
                a(f"  - {y}: {per_year[y].get('total', 0)}")
        a("")
    spans = {s: (r["first_detection"], r["last_detection"]) for s, r in reports.items() if r.get("first_detection")}
    if len(spans) >= 2:
        o_start = max(date.fromisoformat(v[0]) for v in spans.values())
        o_end = min(date.fromisoformat(v[1]) for v in spans.values())
        if o_start <= o_end:
            total_days = (o_end - o_start).days
            split = o_start + timedelta(days=round(0.6 * total_days))
            a("## Detection overlap (input for C-01)")
            a("")
            a(f"- overlap of actual detections: {o_start.isoformat()} .. {o_end.isoformat()} "
              f"({total_days / 365.25:.1f} years)")
            a(f"- suggested ~60/40 temporal split: train through {split.isoformat()}, test after "
              f"(C decides; freeze before fitting)")
            a("")
    a("## Missingness notes (read before using these numbers)")
    a("")
    a("- `days_failed_retrieval` are download failures - they do NOT mean 'no fires that day'.")
    a("- `days_zero_detections` means FIRMS returned a successful response with zero rows.")
    a("- Both are recorded per source; never zero-fill gaps or infer fire absence from missing rows.")
    a("- A detection is a hotspot observation, not necessarily a fire (plan section 0).")
    a("")
    out = LEDGER_DIR / f"ingest_evidence_{slug}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[evidence] -> {out.relative_to(ROOT).as_posix()}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", required=True, help="bbox slug, e.g. w100_s-2_e105_n1")
    parser.add_argument("--source", nargs="+", required=True, choices=sorted(SCHEMAS))
    args = parser.parse_args(argv)
    for source in args.source:
        run_source(source, args.slug)
    build_evidence(args.slug, args.source)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
