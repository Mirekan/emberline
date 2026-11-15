#!/usr/bin/env python3
"""EmberLine FIRMS ingestion tool (Role B: tasks B-01, B-03; B-02 config support).

Resumable FIRMS Area API downloader with an immutable raw cache, per-file
SHA-256 verification, and an append-only fetch ledger. Standard library
only - no pip dependencies.

Default run (no arguments; this is what `make data` calls):
  read config/aois.yaml -> fetch every AOI's full date range (resumable,
  skips windows already verified in the ledger) -> validate + normalize
  each source -> write ingest evidence -> write data/raw/MANIFEST.json
  (the one committed manifest; raw bytes stay out of git).

Subcommands:
  availability   Query keyed source date coverage, save it as a manifest.
  fetch          Download one source/bbox/range into data/raw/, or --aoi <id>.
  inspect        Summarize a downloaded CSV (columns, satellites, dates, FRP).
  manifest       (Re)write data/raw/MANIFEST.json from the fetch ledger.

The MAP_KEY is read from the FIRMS_MAP_KEY environment variable or .env.
It is never printed, logged, or written into file names.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
LEDGER_DIR = ROOT / "data" / "manifests"
LEDGER_PATH = LEDGER_DIR / "fetch_ledger.jsonl"
AOIS_PATH = ROOT / "config" / "aois.yaml"

BASE_URL = "https://firms.modaps.eosdis.nasa.gov"

# B-03 source allowlist. SP = standard processing (archive), NRT = near real time.
# Availability probe 2026-11-14 (B-01): MODIS_SP 2000-11-01..2026-08-31,
# VIIRS_SNPP_SP 2012-01-20..2026-07-31. NRT sources cover only recent months
# and are never blended into the harmonization era (see config/params.yaml).
ALLOWED_SOURCES = {
    "MODIS_NRT", "MODIS_SP",
    "VIIRS_SNPP_NRT", "VIIRS_SNPP_SP",
    "VIIRS_NOAA20_NRT", "VIIRS_NOAA20_SP",
    "VIIRS_NOAA21_NRT", "VIIRS_NOAA21_SP",
}

MAX_DAY_RANGE = 5             # live API documents DAY_RANGE 1..5; do not raise
THROTTLE_SECONDS = 1.0        # conservative pause between requests
FAILURE_BACKOFF_S = 20        # sustained-failure pause (rate-limit defense) — applies
FAILURE_STREAK_LIMIT = 5      # on the failure path too, not only successes
MAX_RETRIES = 3
RETRY_BACKOFF_S = (2, 8, 30)
HTTP_TIMEOUT_S = 120
SOFT_MAX_SPAN_DEG = 5.0       # grid.yaml aoi_limits.bbox_cap_deg


class FetchError(RuntimeError):
    """Request failed after bounded retries, or returned an unusable payload."""


def load_map_key() -> str:
    key = os.environ.get("FIRMS_MAP_KEY", "").strip()
    if key:
        return key
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("FIRMS_MAP_KEY") and "=" in line:
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    print("MAP_KEY loaded from .env (value never printed)")
                    return value
    sys.exit(
        "ERROR: FIRMS_MAP_KEY is not set.\n"
        "Get a free key at https://firms.modaps.eosdis.nasa.gov/api/map_key/\n"
        "then copy .env.example to .env and fill it in. Never commit or paste the key."
    )


def redact(url: str, key: str) -> str:
    return url.replace(key, "***") if key else url


def git_sha() -> str:
    try:
        import subprocess
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def load_aois():
    """Parse the minimal YAML subset used by config/aois.yaml (stdlib only).

    Supports: top-level `key:` sections, `notes:` as a list of plain strings,
    and one list of flat mapping items under `aois:`. No nesting beyond that.
    """
    if not AOIS_PATH.exists():
        sys.exit("ERROR: config/aois.yaml not found (task B-02 owns this file)")
    items: list = []
    notes: list = []
    current = None
    section = None
    for raw in AOIS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped.startswith("- "):
            body = stripped[2:]
            if ":" in body:
                k, v = body.split(":", 1)
                k, v = k.strip(), v.strip().strip('"')
                if indent <= 2 and section == "aois":
                    current = {k: v}
                    items.append(current)
                elif current is not None:
                    current[k] = v
            elif section == "notes":
                notes.append(body.strip().strip('"'))
            continue
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"')
            if indent == 0:
                section = k
                current = None
            elif current is not None and v:
                current[k] = v

    aois = []
    for item in items:
        try:
            bbox = (float(item["west"]), float(item["south"]),
                    float(item["east"]), float(item["north"]))
        except KeyError as err:
            sys.exit(f"ERROR: AOI {item.get('id', '?')} is missing coordinate {err}")
        if not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
            sys.exit(f"ERROR: AOI {item.get('id')} bbox invalid: {bbox}")
        span = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        if span > SOFT_MAX_SPAN_DEG:
            print(f"WARNING: AOI {item.get('id')} span {span:.1f} deg exceeds the "
                  f"{SOFT_MAX_SPAN_DEG:.0f} deg cap in config/grid.yaml")
        sources = [s for s in str(item.get("sources", "")).split() if s]
        unknown = [s for s in sources if s not in ALLOWED_SOURCES]
        if unknown:
            sys.exit(f"ERROR: AOI {item.get('id')} has sources outside the allowlist: {unknown}")
        if not item.get("start") or not item.get("end"):
            sys.exit(f"ERROR: AOI {item.get('id')} needs start/end dates")
        aois.append({
            "id": item["id"],
            "name": item.get("name", item["id"]),
            "bbox": bbox,
            "bbox_str": ",".join(f"{v:g}" for v in bbox),
            "sources": sources,
            "start": item["start"],
            "end": item["end"],
        })
    if not aois:
        sys.exit("ERROR: no AOIs parsed from config/aois.yaml")
    return aois, notes


def bbox_slug(bbox) -> str:
    return "w{}_s{}_e{}_n{}".format(*(f"{v:g}" for v in bbox))


def http_get(url: str):
    """GET with bounded retries. Returns (status, body_bytes) or raises FetchError."""
    last_error = "request failed"
    for attempt in range(MAX_RETRIES):
        try:
            req = Request(url, headers={"User-Agent": "EmberLine-data-engineering/2.0"})
            with urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
                return resp.status, resp.read()
        except HTTPError as err:
            detail = b""
            try:
                detail = err.read()[:200]
            except Exception:
                pass
            if err.code in (429, 500, 502, 503, 504):
                wait = RETRY_BACKOFF_S[min(attempt, len(RETRY_BACKOFF_S) - 1)]
                last_error = f"HTTP {err.code}; retried after {wait}s"
                time.sleep(wait)
                continue
            hint = " - check FIRMS_MAP_KEY" if err.code in (401, 403) else ""
            raise FetchError(f"HTTP {err.code}: {detail.decode('utf-8', 'replace')}{hint}")
        except OSError as err:
            # Covers URLError, TimeoutError (read timeouts), ConnectionError, etc.
            wait = RETRY_BACKOFF_S[min(attempt, len(RETRY_BACKOFF_S) - 1)]
            reason = getattr(err, "reason", None) or err
            last_error = f"network error: {reason}; retried after {wait}s"
            time.sleep(wait)
    raise FetchError(last_error)


def parse_payload(body: bytes):
    """Return (data_rows, field_names, is_empty). Raises on non-CSV payloads."""
    text = body.decode("utf-8", "replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return 0, [], True
    if not lines[0].lower().startswith("latitude"):
        raise FetchError(f"unexpected payload (not FIRMS CSV): {lines[0][:120]}")
    fields = lines[0].split(",")
    return len(lines) - 1, fields, len(lines) == 1


def ledger_append(entry: dict) -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    entry["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=True) + "\n")


def load_verified() -> dict:
    """Map of already-verified relative paths -> sha256 from the ledger."""
    verified = {}
    if LEDGER_PATH.exists():
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("action") == "fetch" and entry.get("status") in ("ok", "ok_empty") and entry.get("path"):
                verified[entry["path"]] = entry.get("sha256")
    return verified


def fetch_range(key, source, bbox, bbox_str, start, end,
                day_range=MAX_DAY_RANGE, limit_windows=None) -> Counter:
    """Fetch every missing window for one source/bbox/date-range. Resumable."""
    slug = bbox_slug(bbox)
    today = datetime.now(timezone.utc).date()
    if end > today:
        print(f"NOTE: end clamped to today ({today}); FIRMS cannot serve future dates")
        end = today
    verified = load_verified()
    counters = Counter()
    consecutive_failures = 0
    window_start = start
    while window_start <= end:
        window_end = min(window_start + timedelta(days=day_range - 1), end)
        days = (window_end - window_start).days + 1
        rel = (RAW_DIR / source / slug / f"{window_start.isoformat()}_{window_end.isoformat()}.csv").relative_to(ROOT)
        path = ROOT / rel
        base_entry = {
            "action": "fetch",
            "source": source,
            "bbox": bbox_str,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "days": days,
            "path": rel.as_posix(),
        }
        if verified.get(rel.as_posix()) and path.exists():
            counters["skipped_verified"] += 1
        else:
            url = f"{BASE_URL}/api/area/csv/{key}/{source}/{bbox_str}/{days}/{window_start.isoformat()}"
            try:
                _status, body = http_get(url)
                rows, fields, is_empty = parse_payload(body)
            except FetchError as err:
                ledger_append({**base_entry, "status": "failed", "error": str(err)[:300],
                               "url": redact(url, key)})
                counters["failed"] += 1
                consecutive_failures += 1
                print(f"[{source}] {window_start}..{window_end}: FAILED - {err}")
                # throttle on the FAILURE path too — instant 400s otherwise let the
                # loop hammer FIRMS unbounded (12 parallel processes once produced
                # ~36k failed requests). Sustained failures = rate-limit signal:
                # back off progressively instead of racing.
                if consecutive_failures >= FAILURE_STREAK_LIMIT:
                    print(f"[{source}] {consecutive_failures} failures beruntun -> "
                          f"backoff {FAILURE_BACKOFF_S}s (rate-limit defense)")
                    time.sleep(FAILURE_BACKOFF_S)
                else:
                    time.sleep(THROTTLE_SECONDS)
            else:
                consecutive_failures = 0
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_name(path.name + ".part")
                tmp.write_bytes(body)
                os.replace(tmp, path)
                ledger_append({**base_entry,
                               "status": "ok_empty" if is_empty else "ok",
                               "rows": rows,
                               "bytes": len(body),
                               "sha256": hashlib.sha256(body).hexdigest(),
                               "fields": fields})
                counters["ok_empty" if is_empty else "ok"] += 1
                print(f"[{source}] {window_start}..{window_end}: {rows} rows -> {rel.as_posix()}")
                time.sleep(THROTTLE_SECONDS)
                if limit_windows is not None and (counters["ok"] + counters["ok_empty"]) >= limit_windows:
                    break
        window_start = window_end + timedelta(days=1)
    return counters


def write_manifest() -> Path:
    entries = []
    if LEDGER_PATH.exists():
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("action") == "fetch":
                entries.append({k: entry.get(k) for k in
                                ("path", "source", "bbox", "window_start", "window_end",
                                 "days", "status", "rows", "bytes", "sha256", "ts")})
    totals = Counter(e.get("status") for e in entries)
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "tool": "pipeline/fetch_firms.py",
        "description": ("Immutable raw FIRMS downloads; one entry per <=5-day request window. "
                        "Raw bytes stay out of git; this manifest is the committed record. "
                        "status ok_empty = successful response with zero detections "
                        "(NOT the same as a failed request)."),
        "totals": dict(totals),
        "windows": entries,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / "MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[manifest] -> {out.relative_to(ROOT).as_posix()} ({len(entries)} windows)")
    return out


def cmd_availability(args) -> int:
    key = load_map_key()
    url = f"{BASE_URL}/api/data_availability/csv/{key}/all"
    try:
        _status, body = http_get(url)
    except FetchError as err:
        print(f"ERROR: {err}")
        return 1
    text = body.decode("utf-8", "replace")
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = LEDGER_DIR / f"data_availability_{stamp}.csv"
    out.write_text(text, encoding="utf-8")
    ledger_append({
        "action": "availability",
        "status": "ok",
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "path": out.relative_to(ROOT).as_posix(),
        "url": redact(url, key),
    })
    print(text)
    print(f"\nSaved: {out.relative_to(ROOT).as_posix()}")
    return 0


def cmd_fetch(args) -> int:
    key = load_map_key()
    if args.aoi:
        aois, _ = load_aois()
        match = next((a for a in aois if a["id"] == args.aoi), None)
        if match is None:
            sys.exit(f"ERROR: unknown AOI id: {args.aoi}")
        bbox = match["bbox"]
        bbox_str = match["bbox_str"]
        sources = args.source if args.source else match["sources"]
        start_s = args.start or match["start"]
        end_s = args.end or match["end"]
    else:
        if not (args.bbox and args.source and args.start and args.end):
            sys.exit("ERROR: fetch needs --bbox/--source/--start/--end, or --aoi <id>")
        bbox = None
        bbox_str = args.bbox
        sources = args.source
        start_s, end_s = args.start, args.end
    try:
        start = date.fromisoformat(start_s)
        end = date.fromisoformat(end_s)
    except (ValueError, TypeError) as err:
        sys.exit(f"ERROR: invalid date: {err}")
    if start > end:
        sys.exit("ERROR: start is after end")
    if bbox is None:
        bbox = parse_bbox(bbox_str)
        bbox_str = ",".join(f"{v:g}" for v in bbox)

    total = Counter()
    for source in sources:
        total.update(fetch_range(key, source, bbox, bbox_str, start, end,
                                 args.day_range, args.limit_windows))
    print("\nSummary:", dict(total))
    print("Ledger:", LEDGER_PATH.relative_to(ROOT).as_posix())
    return 1 if total["failed"] else 0


def parse_bbox(raw: str):
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        sys.exit("ERROR: bbox must be west,south,east,north  e.g. 100.0,-2.0,105.0,1.0")
    try:
        west, south, east, north = (float(p) for p in parts)
    except ValueError:
        sys.exit("ERROR: bbox coordinates must be numbers")
    if not (-180 <= west < east <= 180):
        sys.exit("ERROR: bbox longitude must satisfy -180 <= west < east <= 180 (no antimeridian crossing)")
    if not (-90 <= south < north <= 90):
        sys.exit("ERROR: bbox latitude must satisfy -90 <= south < north <= 90")
    return west, south, east, north


def cmd_inspect(args) -> int:
    path = Path(args.path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        sys.exit(f"ERROR: file not found: {path}")
    satellites: Counter = Counter()
    daynight: Counter = Counter()
    confidence: Counter = Counter()
    dates = []
    frp = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        rows = 0
        for row in reader:
            rows += 1
            satellites[row.get("satellite") or "?"] += 1
            daynight[row.get("daynight") or "?"] += 1
            confidence[row.get("confidence") or "?"] += 1
            if row.get("acq_date"):
                dates.append(row["acq_date"])
            try:
                frp.append(float(row["frp"]))
            except (TypeError, ValueError):
                pass
    print(f"file      : {path.relative_to(ROOT).as_posix()}")
    print(f"rows      : {rows}")
    print(f"fields    : {', '.join(fields)}")
    print(f"satellite : {dict(satellites)}")
    print(f"daynight  : {dict(daynight)}")
    print(f"confidence: {dict(confidence)}")
    if dates:
        print(f"acq_date  : {min(dates)} .. {max(dates)} ({len(dates)} rows with dates)")
    if frp:
        print(f"frp       : min={min(frp):.2f} max={max(frp):.2f} ({len(frp)} numeric)")
    return 0


def cmd_verify(args) -> int:
    """Check the local raw cache against data/raw/MANIFEST.json.

    For teammates who received data/ via a shared drive instead of running
    `make data`, and for A-07 reproduction: every ok/ok_empty window must
    exist and hash-match the committed manifest. Exit 1 on any problem.
    """
    manifest_path = RAW_DIR / "MANIFEST.json"
    if not manifest_path.exists():
        sys.exit("ERROR: data/raw/MANIFEST.json not found - run `python pipeline/fetch_firms.py manifest` first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counters = Counter()
    problems = []
    expected = set()
    for w in manifest.get("windows", []):
        rel = w.get("path")
        if not rel:
            continue
        expected.add(rel)
        if w.get("status") == "failed":
            counters["manifest_failed_windows"] += 1
            continue
        path = ROOT / rel
        if not path.exists():
            counters["missing"] += 1
            problems.append(f"missing   {rel}")
            continue
        sha = w.get("sha256")
        if not sha:
            counters["no_hash_in_manifest"] += 1
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            counters["hash_mismatch"] += 1
            problems.append(f"MISMATCH  {rel}")
        else:
            counters["verified"] += 1
    for src_dir in sorted(RAW_DIR.glob("*/*/*")):
        if src_dir.is_dir():
            for f in sorted(src_dir.glob("*.csv")):
                rel = f.relative_to(ROOT).as_posix()
                if rel not in expected:
                    counters["extra_local_files"] += 1
                    problems.append(f"extra     {rel}")
    print(f"manifest  : {manifest.get('generated_utc')} git_sha={manifest.get('git_sha')}")
    print(f"summary   : {dict(counters)}")
    for line in problems[:20]:
        print(f"  {line}")
    if len(problems) > 20:
        print(f"  ... and {len(problems) - 20} more")
    ok = counters["verified"]
    print(f"RESULT    : {ok} windows verified against the committed manifest")
    return 1 if (counters["missing"] or counters["hash_mismatch"]) else 0


def cmd_default() -> int:
    """`make data`: fetch all configured AOIs, validate, write evidence + MANIFEST."""
    key = load_map_key()
    aois, _notes = load_aois()
    total = Counter()
    for aoi in aois:
        print(f"\n=== AOI {aoi['id']} ({aoi['name']}) {aoi['bbox_str']} "
              f"{aoi['start']}..{aoi['end']}")
        for source in aoi["sources"]:
            total.update(fetch_range(key, source, aoi["bbox"], aoi["bbox_str"],
                                     date.fromisoformat(aoi["start"]),
                                     date.fromisoformat(aoi["end"])))
    # Validate + evidence (same-owner module: pipeline/validate.py)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import validate as validate_mod
    for aoi in aois:
        slug = bbox_slug(aoi["bbox"])
        for source in aoi["sources"]:
            try:
                validate_mod.run_source(source, slug)
            except SystemExit as err:
                print(f"[validate] {source}/{slug}: {err}")
                total["failed"] += 1
        validate_mod.build_evidence(slug, aoi["sources"])
    write_manifest()
    print("\nDefault run summary:", dict(total))
    return 1 if total["failed"] else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd")

    p_av = sub.add_parser("availability", help="query keyed source date coverage")
    p_av.set_defaults(func=cmd_availability)

    p_fx = sub.add_parser("fetch", help="download windows into data/raw/")
    p_fx.add_argument("--source", nargs="+", choices=sorted(ALLOWED_SOURCES),
                      help="one or more sources (defaults to the AOI's configured sources)")
    p_fx.add_argument("--aoi", help="AOI id from config/aois.yaml, e.g. riau")
    p_fx.add_argument("--bbox", help="west,south,east,north  e.g. 100.0,-2.0,105.0,1.0")
    p_fx.add_argument("--start", help="YYYY-MM-DD")
    p_fx.add_argument("--end", help="YYYY-MM-DD")
    p_fx.add_argument("--day-range", type=int, default=MAX_DAY_RANGE, choices=range(1, MAX_DAY_RANGE + 1),
                      help=f"days per request, 1..{MAX_DAY_RANGE} (default {MAX_DAY_RANGE})")
    p_fx.add_argument("--limit-windows", type=int, default=None, metavar="N",
                      help="stop after N successful new windows (smoke tests)")
    p_fx.set_defaults(func=cmd_fetch)

    p_in = sub.add_parser("inspect", help="summarize a downloaded CSV")
    p_in.add_argument("path", help="CSV path, absolute or relative to the project root")
    p_in.set_defaults(func=cmd_inspect)

    p_mf = sub.add_parser("manifest", help="(re)write data/raw/MANIFEST.json from the ledger")
    p_mf.set_defaults(func=lambda args: (write_manifest(), 0)[1])

    p_vf = sub.add_parser("verify", help="check the local raw cache against data/raw/MANIFEST.json")
    p_vf.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    if args.cmd is None:
        return cmd_default()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
