"""EmberLine C-07 — one-command reproducible pipeline + run manifest
(PROTO-C01-v0.9, F-19).

Owner: team member C. Contract test: tests/test_run_manifest.py.

Orchestrates the full science chain for one AOI and records PROVENANCE for
every number it produces:

    make reproduce AOI=riau        (or: python3 -m pipeline.run --aoi riau)

    match -> baselines -> harmonize -> metrics -> splice_stress -> calendar -> windows

Every stage's status (ok / insufficient_data / deferred) is recorded — a stage
that honestly cannot run is NEVER skipped silently. The run manifest carries
the F-19 provenance fields: run_id, git SHA, created UTC, AOI/bbox/date range,
sources, SHA-256 input hashes, params hash, train/test years, metrics path,
library versions and seeds. Re-running the same inputs yields the same params
hash and artifact content (deterministic seeds; run_id timestamp aside).
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas
import yaml

from pipeline import baselines, calendar_climatology, harmonize, metrics, serving_db, splice_stress, windows
from pipeline.match import run as match_run, write_outputs as match_write, read_table

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = baselines.PROTOCOL_VERSION
BOOTSTRAP_SEED = harmonize.BOOTSTRAP_SEED


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
    except Exception:
        return "unknown"


def _aoi_config(aoi_id: str) -> dict:
    cfg = yaml.safe_load((ROOT / "config" / "aois.yaml").read_text())
    for aoi in cfg.get("aois", []):
        if aoi["id"] == aoi_id:
            return aoi
    raise FileNotFoundError(f"AOI '{aoi_id}' not in config/aois.yaml (B-02)")


def _slug(bbox: dict) -> str:
    def fmt(v):
        return str(int(v)) if float(v) == int(v) else str(v).replace("-", "n")
    # B's convention: w100_s-2_e105_n1 (minus kept for south/north)
    return f"w{int(bbox['west'])}_s{int(bbox['south'])}_e{int(bbox['east'])}_n{int(bbox['north'])}"


def discover_inputs(aoi_id: str) -> dict:
    aoi = _aoi_config(aoi_id)
    slug = _slug(aoi)
    data = ROOT / "data"
    return {
        "aoi": aoi,
        "detections": [
            data / "processed" / "MODIS_SP" / slug / "normalized.csv",
            data / "processed" / "VIIRS_SNPP_SP" / slug / "normalized.csv",
        ],
        "mask": data / "manifests" / f"retrieval_mask_{aoi_id}.csv",
        "ledger": data / "manifests" / "fetch_ledger.jsonl",
        "bbox_str": f"{int(aoi['west'])},{int(aoi['south'])},{int(aoi['east'])},{int(aoi['north'])}",
    }


def run(aoi_id: str, run_ts: str | None = None, detections: list[Path] | None = None,
        mask_path: Path | None = None) -> dict:
    created = run_ts or datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    if run_ts:  # frozen clock -> fully deterministic provenance (tests/audit reruns)
        created_utc = datetime.strptime(run_ts, "%Y%m%dT%H%MZ").replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
    else:
        created_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = discover_inputs(aoi_id)
    detections = detections or inputs["detections"]
    mask_path = mask_path or inputs["mask"]
    artifacts = ROOT / "artifacts" / aoi_id
    c02_dir = ROOT / "data" / "processed" / aoi_id / "c02"
    stages: dict[str, dict] = {}

    # -- reset derived artifacts: every reproduce rebuilds them from canonical
    #    inputs. Stale files from interrupted runs must NEVER mix into a fresh
    #    chain (F-15: held-out rows identical across B0/B1/B2).
    for name in ("baseline_series.csv", "harmonized_daily.csv",
                 "harmonization_metrics.json", "splice_stress_test.json",
                 "splice_stress_test_b2.json", "accepted_series.csv",
                 "calendar.csv", "climatology.json", "windows.json",
                 "serving.db", "run_manifest.json"):
        stale = artifacts / name
        if stale.exists():
            stale.unlink()

    # -- stage 1: C-02 match ------------------------------------------------------
    det_paths = [p for p in detections if p.exists()]
    if not mask_path.exists() or not det_paths:
        stages["c02_match"] = {"status": "skipped",
                               "reason": f"missing inputs: detections={[str(p.name) for p in detections if not p.exists()]}, "
                                         f"mask={'present' if mask_path.exists() else 'missing'}"}
        pairs_path = None
    else:
        detections_rows: list[dict] = []
        for p in det_paths:
            detections_rows.extend(read_table(p))
        # delivered window per source -> mask clipped so zero-fill never covers
        # dates whose detections were not delivered (F-9: zeros need retrievals)
        delivered_ranges: dict[str, tuple[str, str]] = {}
        for row in detections_rows:
            fam = "modis" if "modis" in str(row.get("source", "")).lower() else \
                  ("viirs" if "viirs" in str(row.get("source", "")).lower() else None)
            if fam is None:
                continue
            day = str(row.get("acq_date") or str(row.get("acq_datetime_utc", ""))[:10])
            lo, hi = delivered_ranges.get(fam, (day, day))
            delivered_ranges[fam] = (min(lo, day), max(hi, day))
        result = match_run(detections_rows, read_table(mask_path), aoi_id,
                           float(inputs["aoi"]["west"]), float(inputs["aoi"]["south"]),
                           float(inputs["aoi"]["east"]), float(inputs["aoi"]["north"]),
                           delivered_ranges=delivered_ranges or None)
        paths = match_write(result, c02_dir)
        pairs_path = Path(paths["matched_pairs"])  # match_write returns strings
        stages["c02_match"] = {"status": "ok", "outputs": paths,
                               "pair_states": result["summary"]["pair_states"]}

    # -- stage 2: C-03 baselines ----------------------------------------------------
    stage_pairs = pairs_path or (c02_dir / "matched_pairs.csv")
    zero_fill_csv = c02_dir / "zero_fill_days.csv"
    if stage_pairs.exists():
        b = baselines.run(stage_pairs, artifacts, aoi_id,
                          zero_fill_csv=zero_fill_csv if zero_fill_csv.exists() else None)
        stages["c03_baselines"] = {"status": b["manifest"]["outcome"].get("status"),
                                   "outputs": b["outputs"]}
    else:
        stages["c03_baselines"] = {"status": "skipped", "reason": "no matched_pairs.csv"}

    # -- stage 3: C-04 harmonize ------------------------------------------------------
    if stage_pairs.exists():
        h = harmonize.run(stage_pairs, artifacts, aoi_id,
                          zero_fill_csv=zero_fill_csv if zero_fill_csv.exists() else None)
        stages["c04_harmonize"] = {"status": h["manifest"]["outcome"].get("status"),
                                   "outputs": h["outputs"]}
    else:
        stages["c04_harmonize"] = {"status": "skipped", "reason": "no matched_pairs.csv"}

    # -- stages 4/5: C-05 metrics + stress (F-15 mismatch recorded honestly,
    #    never crashes the whole reproduce batch) ---------------------------------------
    series_b = artifacts / "baseline_series.csv"
    series_h = artifacts / "harmonized_daily.csv"
    try:
        m = metrics.run(series_b, series_h, stage_pairs if stage_pairs.exists() else None,
                        artifacts, aoi_id)["manifest"]
        stages["c05_metrics"] = {"status": m.get("status") or m.get("outcome", {}).get("status"),
                                 "outputs": {"metrics": str(artifacts / "harmonization_metrics.json")}}
    except ValueError as err:
        stages["c05_metrics"] = {"status": "mismatch", "error": str(err)[:300],
                                 "note": "F-15 violation recorded honestly — rebuild via make reproduce"}
    try:
        # B1 (accepted, DEC-6) = published stress artifact — B1 values live in
        # baseline_series.csv; B2 kept visible (negative result, separate file)
        stages["c05_splice_stress"] = {"status": splice_stress.run(
            series_b, series_b, artifacts, aoi_id,
            harmonized_column="B1_ratio_pred_mw", out_name="splice_stress_test.json",
            method_label="B1 (accepted)")["manifest"].get("status")}
        splice_stress.run(series_b, series_h, artifacts, aoi_id,
                          harmonized_column="predicted_b2_mw",
                          out_name="splice_stress_test_b2.json", method_label="B2")
    except ValueError as err:
        stages["c05_splice_stress"] = {"status": "mismatch", "error": str(err)[:300],
                                       "note": "recorded honestly — rebuild via make reproduce"}

    # -- stage 6: C-06 calendar + windows --------------------------------------------------
    units_csv = c02_dir / "units_per_sensor.csv"
    cal = calendar_climatology.run(series_h, units_csv if units_csv.exists() else None, artifacts, aoi_id)
    stages["c06_calendar"] = {"status": cal["manifest"].get("status"), "outputs": cal["outputs"]}
    stages["c06_windows"] = {"status": windows.run(artifacts, artifacts)["manifest"].get("status")}

    # -- stage 7: C-07 derived SQLite serving artifact ------------------------------------
    serving_stats = serving_db.build(artifacts, aoi_id)
    stages["c07_serving_db"] = {
        "status": "ok",
        "sha256": serving_stats["sha256"],
        "tables": serving_stats["tables"],
        "missing_sources": serving_stats["missing_sources"],
        "outputs": {"db": serving_stats["db"]},
    }

    # -- provenance manifest (F-19) ----------------------------------------------------------
    train_years = test_years = None
    if stages["c04_harmonize"].get("status") == "ok":
        gate = json.loads((artifacts / "model_manifest.json").read_text())
        outcome_model = gate["outcome"].get("model", {}).get("fit_inputs", {})
        train_years = outcome_model.get("train_years")
        test_years = outcome_model.get("test_years_recorded_never_fitted")
    input_hashes = {str(p.relative_to(ROOT)): _sha256(p)
                    for p in ([mask_path] if mask_path.exists() else []) + det_paths}
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "task": "C-07",
        "run_id": f"{PROTOCOL_VERSION}_{git_sha()}_{created}",
        "git_sha": git_sha(),
        "created_utc": created_utc,
        "aoi_id": aoi_id,
        "aoi_bbox_date_range": {
            "bbox": inputs["bbox_str"],
            "start": str(inputs["aoi"].get("start")),
            "end": str(inputs["aoi"].get("end")),
        },
        "sources": ["MODIS_SP", "VIIRS_SNPP_SP"],
        "input_sha256": input_hashes,
        "params_hash": _sha256(ROOT / "config" / "params.yaml"),
        "train_years": train_years,
        "test_years": test_years,
        "metrics_path": str(artifacts / "harmonization_metrics.json"),
        "library_versions": {"numpy": np.__version__, "pandas": pandas.__version__,
                             "python": sys.version.split()[0]},
        "seeds": {"interval_bootstrap": BOOTSTRAP_SEED},
        "serving_db_sha256": serving_stats["sha256"],
        "stage_statuses": stages,
        "honesty_note": "stage statuses are recorded verbatim — insufficient_data/deferred "
                        "stages are NOT failures or passes, they are the actual state",
    }
    artifacts.mkdir(parents=True, exist_ok=True)
    manifest_path = artifacts / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"manifest": manifest, "outputs": {"run_manifest": str(manifest_path)}}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-07 one-command reproducible pipeline")
    parser.add_argument("--aoi", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    result = run(args.aoi)
    print(json.dumps({k: result["manifest"][k] for k in
                      ("run_id", "stage_statuses")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
