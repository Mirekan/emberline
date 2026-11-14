#!/usr/bin/env python3
"""EmberLine science pipeline orchestrator (C-07) — PROTO-C01-v0.9.

Raw validated caches -> matched units -> harmonized daily series (B0/B1/B2,
training-only law) -> held-out metrics -> 366-day calendar + climatology ->
critical windows -> splice stress tests -> versioned artifacts + run manifest.

Usage:
  python pipeline/run.py --aoi riau
  python pipeline/run.py --aoi riau --data-root data/fixtures/FIXTURE_SYNTHETIC/riau \
      --fixture FIXTURE_SYNTHETIC --sources MODIS_SP VIIRS_SNPP_SP

Data root layout (as written by validate.py / the synthetic fixture builder):
  <data_root>/<source>/<slug>/normalized.csv
  <data_root>/fetch_ledger.jsonl
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import emberline_proto as P
import match as match_mod
import harmonize as harm_mod
import metrics as metrics_mod
import calendar as cal_mod
import stress_test as stress_mod

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
AOIS_PATH = ROOT / "config" / "aois.yaml"


def _git_sha():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _aoi_bbox(aoi: str):
    if AOIS_PATH.exists():
        current = None
        for raw in AOIS_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].rstrip()
            s = line.strip()
            if s.startswith("- id:"):
                current = s.split(":", 1)[1].strip()
                continue
            if current == aoi and s and ":" in s and not s.startswith("-"):
                k, v = s.split(":", 1)
                if k.strip() in ("west", "south", "east", "north"):
                    yield float(v.strip())
    return


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--aoi", required=True)
    ap.add_argument("--sources", nargs="+", default=["MODIS_SP", "VIIRS_SNPP_SP"])
    ap.add_argument("--slug", default=None, help="bbox slug; default parsed from config/aois.yaml")
    ap.add_argument("--data-root", default=None,
                    help="override data root (e.g. a fixture dir); default data/processed")
    ap.add_argument("--fixture", default=None, help="fixture label if data is synthetic")
    args = ap.parse_args(argv)

    coords = list(_aoi_bbox(args.aoi))
    slug = args.slug
    if slug is None and len(coords) == 4:
        w, s, e, n = coords
        slug = f"w{w:g}_s{s:g}_e{e:g}_n{n:g}"
    if slug is None:
        raise SystemExit("ERROR: cannot derive slug — pass --slug")

    data_root = Path(args.data_root) if args.data_root else ROOT / "data" / "processed"
    out_dir = ARTIFACTS / args.aoi
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. match
    matched_path, coverage = match_mod.run_match(data_root, tuple(args.sources), slug, out_dir)

    # 2. harmonize
    model, series, p95_ref, train_years, test_years = harm_mod.run_harmonize(
        matched_path, coverage, out_dir, fixture=args.fixture)

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    run_id = f"{P.PROTO_ID}_{run_ts}_{model['method']}"
    if args.fixture:
        run_id += "_FIXTURE"

    # 3. metrics (held-out)
    metrics = metrics_mod.compute_metrics(series, test_years)
    (out_dir / "metrics.json").write_text(json.dumps({
        "run_id": run_id, "fixture": args.fixture, "metrics": metrics}, indent=2), encoding="utf-8")

    # 4. calendar + windows
    cal = cal_mod.run_calendar(series, p95_ref, train_years, model["split"]["eligible_years"],
                               out_dir, run_id, model["method"], args.fixture)
    (out_dir / "windows.json").write_text(json.dumps({
        "run_id": run_id, "fixture": args.fixture,
        "windows": cal["critical_windows"]}, indent=2), encoding="utf-8")

    # 5. stress tests
    stress_mod.run_stress(series, test_years, coverage, out_dir, run_id, args.fixture)

    # 6. manifest
    input_hashes = {}
    for src in args.sources:
        norm = data_root / src / slug / "normalized.csv"
        if norm.exists():
            try:
                rel = norm.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                rel = norm.resolve().as_posix()
            input_hashes[rel] = hashlib.sha256(norm.read_bytes()).hexdigest()
    manifest = {
        "run_id": run_id,
        "git_sha": _git_sha(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aoi_bbox_date_range": {"aoi": args.aoi, "slug": slug, "bbox": coords or None,
                                 "coverage": {"first": coverage["first_date"],
                                               "last": coverage["last_date"]}},
        "sources": args.sources,
        "input_sha256": input_hashes,
        "params_hash": hashlib.sha256((ROOT / "config" / "params.yaml").read_bytes()).hexdigest()
                       if (ROOT / "config" / "params.yaml").exists() else None,
        "train_years": train_years,
        "test_years": test_years,
        "metrics_path": f"artifacts/{args.aoi}/metrics.json",
        "library_versions": {"python": "stdlib-only", "numpy": "not-used", "pandas": "not-used"},
        "seeds": {"bootstrap": 20261114},
        "fixture": args.fixture,
        "boundary": "Historical & descriptive — not predictive.",
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[run] artifacts -> artifacts/{args.aoi}/ (run_id={run_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
