"""EmberLine API (D-03/D-04) — serves versioned artifacts from artifacts/.

RULES (repo README / DEV-S05):
- never imports pipeline/ or recomputes science at request time;
- payloads follow contracts/*.example.json; every payload carries run_id,
  model_version and a `fixture` passthrough (UI shows MOCK when set);
- null means explicit gap WITH a reason — never a silent 0;
- statuses: queued · running · complete · failed · insufficient_data ·
  unsupported · expired;
- sanitized errors only; FIRMS_MAP_KEY never leaves the server.

Run:  python -m uvicorn api.app:app --port 8300   (from repo root)
"""
from __future__ import annotations

import csv
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
AOIS_PATH = ROOT / "config" / "aois.yaml"

app = FastAPI(title="EmberLine API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

# In-process job store (bounded; DEV-S05 — no queue, no DB)
JOBS: dict = {}
JOB_TTL_MIN = 30
MAX_JOBS = 4


def _aoi_meta(aoi: str):
    """Parse the minimal YAML subset of config/aois.yaml (never imports pipeline)."""
    if not AOIS_PATH.exists():
        raise HTTPException(500, detail="config/aois.yaml missing")
    current = None
    for raw in AOIS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        s = line.strip()
        if s.startswith("- id:"):
            current = {"id": s.split(":", 1)[1].strip()}
            if current["id"] == aoi:
                continue
        if current and current.get("id") == aoi:
            if s.startswith("- "):
                break
            if s and ":" in s:
                k, v = s.split(":", 1)
                if k.strip() in ("name", "sources", "start", "end", "west", "south", "east", "north"):
                    try:
                        current[k.strip()] = float(v.strip())
                    except ValueError:
                        current[k.strip()] = v.strip().strip('"')
            if current.get("end"):
                return current
    return None


def _load(aoi: str, name: str):
    p = ARTIFACTS / aoi / name
    if not p.exists():
        raise HTTPException(404, detail=f"Data artefak '{name}' untuk wilayah '{aoi}' belum tersedia. Silakan pilih wilayah lain yang sudah siap.")
    return json.loads(p.read_text(encoding="utf-8"))


def _series(aoi: str):
    p = ARTIFACTS / aoi / "harmonized_daily.csv"
    if not p.exists():
        raise HTTPException(404, detail=f"Data deret waktu untuk wilayah '{aoi}' belum tersedia. Silakan pilih wilayah lain yang sudah siap.")
    rows = []
    with p.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for k in ("raw_modis_frp_mw", "raw_modis_n", "raw_viirs_frp_mw",
                      "raw_viirs_n", "harmonized_lo_mw", "harmonized_estimate_mw",
                      "harmonized_hi_mw"):
                if r.get(k) == "":
                    r[k] = None
                else:
                    try:
                        r[k] = float(r[k]) if k.endswith("mw") else int(r[k])
                    except ValueError:
                        pass
            if r.get("flags"):
                r["flags"] = r["flags"].split("|") if "|" in r["flags"] else (
                    [r["flags"]] if r["flags"] else [])
            else:
                r["flags"] = []
            rows.append(r)
    return rows


def _envelope(aoi: str):
    man = _load(aoi, "run_manifest.json")
    try:
        model_version = _load(aoi, "model.json").get("method")
    except HTTPException:
        model_version = None
    return {"run_id": man["run_id"], "model_version": model_version,
            "fixture": man.get("fixture"),
            "mock": bool(man.get("fixture")),
            "boundary": "Historical & descriptive — not predictive."}


# ---------------- endpoints ----------------

@app.get("/api/health")
def health():
    aois = sorted((p.name for p in ARTIFACTS.glob("*") if p.is_dir()), )
    return {"status": "ok", "aois_with_artifacts": aois,
            "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


@app.get("/api/aoi/presets")
def presets():
    out = []
    if AOIS_PATH.exists():
        cur = None
        for raw in AOIS_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].rstrip()
            s = line.strip()
            if s.startswith("- id:"):
                if cur:
                    out.append(cur)
                cur = {"id": s.split(":", 1)[1].strip()}
                continue
            if cur is not None:
                if s.startswith("- "):
                    out.append(cur); cur = None
                    continue
                if s and ":" in s:
                    k, v = s.split(":", 1)
                    k = k.strip()
                    try:
                        cur[k] = float(v.strip())
                    except ValueError:
                        cur[k] = v.strip().strip('"')
        if cur:
            out.append(cur)
    for p in out:
        has = (ARTIFACTS / p["id"]).is_dir()
        p["artifact_status"] = "available" if has else "queued"
        p["mock"] = _load(p["id"], "run_manifest.json").get("fixture") if has else None
    return {"presets": out}


@app.get("/api/aoi/{aoi}/series")
def series(aoi: str, mock: bool | None = Query(default=None)):
    env = _envelope(aoi)
    rows = _series(aoi)
    return {"aoi_id": aoi, **env, "n_days": len(rows), "days": rows}


@app.get("/api/aoi/{aoi}/calendar")
def calendar(aoi: str):
    cal = _load(aoi, "calendar.json")
    return {**_envelope(aoi), **cal}


@app.get("/api/aoi/{aoi}/climatology")
def climatology(aoi: str):
    cal = _load(aoi, "calendar.json")
    return {**_envelope(aoi),
            "smoothing_days": 7,
            "positions": cal["climatology"],
            "smoothed_median_mw": cal["climatology_smoothed_median_mw"]}


@app.get("/api/aoi/{aoi}/windows")
def windows(aoi: str):
    return {**_envelope(aoi), **_load(aoi, "windows.json")}


@app.get("/api/aoi/{aoi}/stress")
def stress(aoi: str):
    return {**_envelope(aoi), **_load(aoi, "stress_test.json")}


@app.get("/api/aoi/{aoi}/grid")
def api_grid(aoi: str):
    """Per-cell yearly raw FRP totals (O-02 map layer). Raw sensor scale."""
    return _load(aoi, "grid.json")


@app.get("/api/aoi/{aoi}/detections")
def api_detections(aoi: str):
    """Validated hotspot detections — one entry = one satellite pixel, not one fire."""
    return _load(aoi, "detections.json")


@app.get("/api/aoi/{aoi}/export")
def export(aoi: str, what: str = "series"):
    if what not in ("series", "windows", "calendar"):
        raise HTTPException(400, detail="what must be series|windows|calendar")
    if what == "series":
        rows = _series(aoi)
        man = _load(aoi, "run_manifest.json")
        header = ",".join(rows[0].keys())
        lines = [header]
        for r in rows:
            lines.append(",".join("" if v is None else (("|".join(v)) if isinstance(v, list) else str(v)) for v in r.values()))
        body = "\n".join(lines)
        fname = f"emberline_{aoi}_series.csv"
        provenance = (f"# run_id={man['run_id']} model={man.get('fixture') or man.get('run_id')} "
                      f"source=NASA FIRMS (MODIS C6.1, VIIRS 375m) boundary='Historical & descriptive — not predictive.'")
        return PlainTextResponse(provenance + "\n" + body, media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    data = _load(aoi, f"{what}.json" if what == "windows" else "calendar.json")
    return PlainTextResponse(json.dumps(data, indent=2), media_type="application/json",
                             headers={"Content-Disposition": f"attachment; filename=emberline_{aoi}_{what}.json"})


@app.get("/api/method")
def method(aoi: str | None = None):
    aoi = aoi or next((p.name for p in sorted(ARTIFACTS.glob("*")) if p.is_dir()), None)
    if aoi is None:
        raise HTTPException(404, detail="Belum ada data artefak yang tersedia. Silakan pilih wilayah lain yang sudah siap.")
    man = _load(aoi, "run_manifest.json")
    
    # Load model from model_manifest.json (new) or model.json (fallback)
    try:
        model = _load(aoi, "model_manifest.json")
        fit_inputs = model.get("outcome", {}).get("model", {}).get("fit_inputs", {})
        train_years = fit_inputs.get("train_years") or model.get("split", {}).get("train_years", [])
        test_years = fit_inputs.get("test_years_recorded_never_fitted") or model.get("split", {}).get("test_years", [])
        split = {
            "train_years": train_years,
            "test_years": test_years
        }
        coefficients = model.get("outcome", {}).get("model", {}).get("coefficients") or model.get("coefficients", {})
        interval = model.get("outcome", {}).get("intervals") or model.get("interval", {})
    except HTTPException:
        model = _load(aoi, "model.json")
        split = model.get("split", {"train_years": [], "test_years": []})
        coefficients = model.get("coefficients", {})
        interval = model.get("interval", {})
        
    # Load metrics from harmonization_metrics.json (new) or metrics.json (fallback)
    try:
        raw_m = _load(aoi, "harmonization_metrics.json")
        outcome_m = raw_m.get("outcome", {}).get("metrics", {})
        b1 = outcome_m.get("b1", {})
        b2 = outcome_m.get("b2", {})
        b0 = outcome_m.get("b0", {})
        metrics = {
            "mean_log_ratio_bias": b1.get("mean_log_ratio_bias", {}).get("value"),
            "smape": b1.get("smape", {}).get("value"),
            "pearson_daily": b1.get("pearson_daily", {}).get("value"),
            "pearson_weekly": b1.get("pearson_weekly", {}).get("value"),
            "spearman_daily": b1.get("spearman_daily", {}).get("value"),
            "spearman_weekly": b1.get("spearman_weekly", {}).get("value"),
            "log_space_r2": b1.get("log_space_r2", {}).get("value"),
            "ks_statistic": b1.get("ks_statistic", {}).get("value"),
            "wasserstein_distance": b1.get("wasserstein_distance", {}).get("value"),
            "calendar_pattern_correlation": b1.get("calendar_pattern_correlation", {}).get("value"),
            "interval_coverage_empirical": b2.get("interval_coverage_empirical", {}).get("value"),
            "b0_naive_splice_level_shift": b0.get("mean_log_ratio_bias", {}).get("value"),
            "b1_naive_splice_level_shift": b1.get("mean_log_ratio_bias", {}).get("value"),
            "b2_naive_splice_level_shift": b2.get("mean_log_ratio_bias", {}).get("value"),
        }
    except HTTPException:
        metrics = _load(aoi, "metrics.json").get("metrics", {})

    # Load stress tests
    try:
        stress_raw = _load(aoi, "splice_stress_test.json")
        stress_tests = stress_raw.get("tests", stress_raw.get("results", []))
    except HTTPException:
        stress_tests = _load(aoi, "stress_test.json").get("results", [])

    return {
        **_envelope(aoi),
        "protocol_id": man.get("protocol_version") or "PROTO-C01-v0.9",
        "split": split,
        "method_form": "log1p(S_modis) = a + b*log1p(S_viirs) + c*log1p(1+n_viirs) + d*I_night (monotone; B1 fallback = global ratio)",
        "coefficients": coefficients,
        "interval": interval,
        "metrics": metrics,
        "stress_tests": stress_tests,
        "limitations": [
            "Harmonized values are model estimates — not ground truth; every value ships with its interval.",
            "DEC-6: B1 training-fitted ratio accepted; B2 monotone mapping displayed honestly as a negative result.",
            "Detections are never summed into a physical fire count across sensors.",
            "Gaps are flagged, never interpolated; failed retrieval is not zero.",
            "Aqua-reference calibration limits claims strictly to what satellite evidence supports."
        ],
        "citations": "NASA FIRMS — MODIS C6.1 (Giglio et al. 2016); VIIRS 375 m VNP14IMG (Schroeder et al. 2014)."
    }


@app.post("/api/aoi/analyze")
def analyze(body: dict):
    bbox = body.get("bbox") or {}
    try:
        w, s, e, n = (float(bbox[k]) for k in ("west", "south", "east", "north"))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, detail={"code": "bad_bbox", "message": "bbox needs numeric west,south,east,north.", "retryable": False})
    if not (-180 <= w < e <= 180) or not (-90 <= s < n <= 90):
        raise HTTPException(400, detail={"code": "bad_bbox", "message": "bbox must satisfy west<east, south<north; antimeridian crossing is not supported.", "retryable": False})
    if max(e - w, n - s) > 5.0:
        raise HTTPException(422, detail={"code": "bbox_too_large",
            "message": f"Custom areas are limited to 5° × 5°. Your box is {e-w:.1f}° × {n-s:.1f}°.", "retryable": False})
    if len(JOBS) >= MAX_JOBS:
        raise HTTPException(429, detail={"code": "queue_full", "message": "Job queue is full (bounded). Try again in a few minutes.", "retryable": True})
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    JOBS[job_id] = {"job_id": job_id, "status": "queued",
                    "created": datetime.now(timezone.utc),
                    "expires": datetime.now(timezone.utc) + timedelta(minutes=JOB_TTL_MIN),
                    "bbox": body.get("bbox"), "aoi_id": body.get("aoi_id")}
    return {"job_id": job_id, "status": "queued", "poll": f"/api/jobs/{job_id}",
            "note": "Bounded in-process job; expired jobs are reported expired, never stuck."}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, detail={"code": "unknown_job", "message": "Unknown job id.", "retryable": False})
    now = datetime.now(timezone.utc)
    if job["status"] in ("queued", "running") and now > job["expires"]:
        job["status"] = "expired"
        job["error"] = {"code": "job_expired",
                        "message": "This job expired after 30 minutes without finishing. Run the analysis again — nothing was saved half-way.",
                        "retryable": True}
    return {k: v for k, v in job.items() if k not in ("created", "expires")} | \
           {"poll": f"/api/jobs/{job_id}"}
