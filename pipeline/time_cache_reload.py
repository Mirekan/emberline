#!/usr/bin/env python3
"""Measure processed-cache reload time (Role B, task B-06 item 3).

PRD target: processed cache load within 5 seconds. This tool measures the
actual elapsed time of fully parsing every normalized.csv cache with the
stdlib csv module (no warm-up tricks; each file timed with time.monotonic),
records rows, bytes, hardware and cache conditions, and reports PASS/MISS
against the target. A miss is reported as a miss - the target is never
labeled achieved without this measurement.

Output: data/manifests/cache_reload_timing.json + console table.
"""

from __future__ import annotations

import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_PATH = ROOT / "data" / "manifests" / "cache_reload_timing.json"

TARGET_LOAD_SECONDS = 5.0  # PRD: processed cache load < 5 s


def timed_full_parse(path: Path):
    """Parse every row into dicts (what a real cache consumer does)."""
    t0 = time.monotonic()
    rows = 0
    columns = None
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        columns = reader.fieldnames
        for _row in reader:
            rows += 1
    elapsed = time.monotonic() - t0
    return rows, columns, elapsed, path.stat().st_size


def main(argv=None) -> int:
    if not PROCESSED_DIR.exists():
        sys.exit("ERROR: no data/processed yet - run pipeline/validate.py first")
    results = []
    for norm in sorted(PROCESSED_DIR.glob("*/*/normalized.csv")):
        source, slug = norm.parts[-3], norm.parts[-2]
        rows, columns, elapsed, size = timed_full_parse(norm)
        results.append({
            "source": source,
            "aoi_slug": slug,
            "file": norm.relative_to(ROOT).as_posix(),
            "rows": rows,
            "bytes": size,
            "columns": len(columns or []),
            "load_seconds": round(elapsed, 3),
        })
        print(f"[{source}/{slug}] rows={rows:>7} size={size/1e6:7.1f} MB "
              f"load={elapsed:6.2f}s  ({norm.name})")

    total = round(sum(r["load_seconds"] for r in results), 3)
    total_rows = sum(r["rows"] for r in results)
    total_bytes = sum(r["bytes"] for r in results)
    verdict = "PASS" if total < TARGET_LOAD_SECONDS else "MISS"
    print(f"\nTOTAL: {total}s for {len(results)} caches, {total_rows} rows, "
          f"{total_bytes/1e6:.1f} MB -> target <{TARGET_LOAD_SECONDS}s: {verdict}")

    record = {
        "measured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": ("time.monotonic() around a full stdlib-csv parse of every "
                   "data/processed/**/normalized.csv; no warm-up caching tricks"),
        "target_seconds": TARGET_LOAD_SECONDS,
        "total_load_seconds": total,
        "total_rows": total_rows,
        "total_bytes": total_bytes,
        "verdict": verdict,
        "hardware": {
            "machine": platform.machine(),
            "processor": platform.processor() or platform.machine(),
            "python": platform.python_version(),
            "os": platform.platform(),
        },
        "cache_conditions": "OS file cache state not forced; same-run sequential reads (warm cache)",
        "caches": results,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"[timing] -> {OUT_PATH.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
