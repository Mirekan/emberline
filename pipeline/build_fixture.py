#!/usr/bin/env python3
"""Build FIXTURE_REAL_SAMPLE (Role B, task B-06 item 2).

A compact, clearly labeled integration fixture cut from REAL validated rows
(not synthetic). Purpose: give D/E a small legitimate dataset to run the
integration check before the full five-preset caches land, and give A a
fast traceable smoke path.

What it contains (per AOI x source):
  normalized slice of one documented peak week (2015-09-01 .. 2015-09-07,
  El Nino), capped at --rows-per-file rows, provenance CSV columns intact.
  provenance.json records: source AOI/bbox, source window files + their
  sha256 from MANIFEST.json, parent normalized.csv hash, row counts, and
  the FIRMS data use note.

What the fixture CAN test: endpoint wiring, CSV roundtrip, column contract,
hash/provenance chain, UI rendering with real-shaped data.
What it CANNOT test: full-era coverage, calendar climatology over 15 years,
five-preset status semantics, performance at production scale. It is a
fixture, never a claimed result.

Output: data/fixtures/FIXTURE_REAL_SAMPLE/ (git-ignored, shareable via drive)
plus a committed description doc reference in docs/handoffs/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw"
FIXTURE_DIR = ROOT / "data" / "fixtures" / "FIXTURE_REAL_SAMPLE"

# Documented choice: first week of the Sept-Oct 2015 El Nino fire peak.
FIXTURE_START = "2015-09-01"
FIXTURE_END = "2015-09-07"
FIXTURE_SLUGS = {
    "riau": "w100_s-2_e105_n1",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build(aoi: str, slug: str, sources: list, rows_per_file: int) -> dict:
    out = {
        "aoi": aoi,
        "slug": slug,
        "sources": {},
        "fixture_start": FIXTURE_START,
        "fixture_end": FIXTURE_END,
        "rows_per_file_cap": rows_per_file,
    }
    for source in sources:
        norm = PROCESSED_DIR / source / slug / "normalized.csv"
        if not norm.exists():
            print(f"[fixture] SKIP {source}/{slug}: normalized.csv not found (run validate.py first)")
            continue
        kept = []
        with norm.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if FIXTURE_START <= row["acq_date"] <= FIXTURE_END:
                    kept.append(row)
                    if len(kept) >= rows_per_file:
                        break
        fixture_csv = FIXTURE_DIR / f"{aoi}_{source}.csv"
        if kept:
            with fixture_csv.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(kept[0].keys()))
                writer.writeheader()
                writer.writerows(kept)
        dates = sorted({r["acq_date"] for r in kept})
        raw_windows = sorted((RAW_DIR / source / slug).glob("*.csv"))
        window_hashes = {w.name: sha256_file(w) for w in raw_windows
                         if not (w.stem.split("_")[1] < FIXTURE_START or w.stem.split("_")[0] > FIXTURE_END)}
        out["sources"][source] = {
            "fixture_rows": len(kept),
            "fixture_file": fixture_csv.name if kept else None,
            "fixture_sha256": sha256_file(fixture_csv) if kept else None,
            "fixture_dates": f"{dates[0]}..{dates[-1]}" if dates else None,
            "parent_normalized_csv_sha256": sha256_file(norm),
            "source_raw_windows_in_week": window_hashes,
        }
        print(f"[fixture] {aoi}/{source}: {len(kept)} rows -> {fixture_csv.name}")
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows-per-file", type=int, default=400, help="cap per source file (default 400)")
    args = parser.parse_args(argv)
    if not PROCESSED_DIR.exists():
        sys.exit("ERROR: no data/processed yet - run pipeline/validate.py first")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for aoi, slug in FIXTURE_SLUGS.items():
        results[aoi] = build(aoi, slug, ["MODIS_SP", "VIIRS_SNPP_SP"], args.rows_per_file)
    provenance = {
        "fixture_id": "FIXTURE_REAL_SAMPLE",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "pipeline/build_fixture.py",
        "data_origin": "NASA FIRMS Area API (SP archives), keyed requests, validated by pipeline/validate.py",
        "use_note": ("NASA FIRMS active fire data; hotspot observation is not necessarily a fire. "
                     "Fixture is for integration testing only - never presented as a result."),
        "aois": results,
    }
    prov_path = FIXTURE_DIR / "provenance.json"
    prov_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    readme = FIXTURE_DIR / "README.md"
    readme.write_text(
        "# FIXTURE_REAL_SAMPLE\n\n"
        f"Built {provenance['created_utc']} from REAL validated FIRMS rows "
        f"(El Nino week {FIXTURE_START}..{FIXTURE_END}, Riau, cap "
        f"{args.rows_per_file} rows/source).\n\n"
        "- CAN test: endpoint wiring, CSV roundtrip, column contract, provenance/hash chain.\n"
        "- CANNOT test: full-era coverage, 15-year climatology, five-preset statuses,\n"
        "  production-scale performance. This is a fixture, never a claimed result.\n\n"
        "See provenance.json for the full hash chain back to raw windows and MANIFEST.json.\n",
        encoding="utf-8")
    print(f"[fixture] provenance -> {prov_path.relative_to(ROOT).as_posix()}")
    print(f"[fixture] readme     -> {readme.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
