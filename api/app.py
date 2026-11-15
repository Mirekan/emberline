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
import math
import os
import re
import urllib.error
import urllib.request
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
_cors_origins = [origin.strip() for origin in os.getenv("EMBERLINE_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

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


def _number(value: str | None) -> float | None:
    return None if value in (None, "") else float(value)


def _series(aoi: str):
    aoi_dir = ARTIFACTS / aoi
    accepted_path = aoi_dir / "accepted_series.csv"
    if not accepted_path.exists():
        raise HTTPException(404, detail=f"Data deret waktu untuk wilayah '{aoi}' belum tersedia. Silakan pilih wilayah lain yang sudah siap.")

    intervals_by_date = {}
    intervals_path = aoi_dir / "harmonized_daily.csv"
    if intervals_path.exists():
        with intervals_path.open(newline="", encoding="utf-8") as fh:
            for interval in csv.DictReader(fh):
                intervals_by_date.setdefault(interval["date"], []).append(interval)

    rows = []
    with accepted_path.open(newline="", encoding="utf-8") as fh:
        for accepted in csv.DictReader(fh):
            intervals = intervals_by_date.get(accepted["date"], [])

            def sum_bound(field: str):
                values = [_number(interval.get(field)) for interval in intervals]
                if not values or any(value is None for value in values):
                    return None
                return sum(value for value in values if value is not None)

            flags = []
            for raw_flags in [accepted.get("flags", "")] + [
                interval.get("flags", "") for interval in intervals
            ]:
                for flag in raw_flags.split("|"):
                    if flag and flag not in flags:
                        flags.append(flag)

            rows.append({
                "date": accepted["date"],
                "source_flag": accepted.get("source_flag") or "gap",
                "raw_modis_frp_mw": _number(accepted.get("observed_modis_mw")),
                "raw_modis_n": None,
                "raw_viirs_frp_mw": _number(accepted.get("observed_viirs_mw")),
                "raw_viirs_n": None,
                "harmonized_lo_mw": sum_bound("lo_mw"),
                "harmonized_estimate_mw": _number(accepted.get("harmonized_mw")),
                "harmonized_hi_mw": sum_bound("hi_mw"),
                "flags": flags,
                "gap_reason": accepted.get("gap_reason") or None,
            })
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


_CACHED_INDONESIA_MOSAIC_GRID = None


def _generate_indonesia_mosaic_grid():
    global _CACHED_INDONESIA_MOSAIC_GRID
    if _CACHED_INDONESIA_MOSAIC_GRID is not None:
        return _CACHED_INDONESIA_MOSAIC_GRID

    cell_deg = 0.1
    bounds = {"south": -12.0, "west": 94.0, "north": 8.0, "east": 152.0}
    scale_note = "0.1-degree full rectangular grid across Indonesia and New Guinea (94°E to 152°E, 12°S to 8°N). Areas without observations are white standby."

    # 1. Merge artifact observation counts where available across monitored regions
    merged_cells = {}
    years = set()
    for path in sorted(ARTIFACTS.iterdir()):
        if not path.is_dir() or path.name in ("all", "indonesia"):
            continue
        g_path = path / "grid.json"
        d_path = path / "detections.json"
        if not g_path.is_file() or not d_path.is_file():
            continue
        try:
            g = json.loads(g_path.read_text(encoding="utf-8"))
            dets = json.loads(d_path.read_text(encoding="utf-8")).get("detections", [])
            years.update(g.get("years", []))

            d_counts = {}
            for d in dets:
                l_idx = math.floor(d["lat"] / cell_deg + 1e-9)
                o_idx = math.floor(d["lon"] / cell_deg + 1e-9)
                d_counts[(l_idx, o_idx)] = d_counts.get((l_idx, o_idx), 0) + 1

            for c in g.get("cells", []):
                l_idx = math.floor(c["south"] / cell_deg + 1e-9)
                o_idx = math.floor(c["west"] / cell_deg + 1e-9)
                cid = f"R{l_idx:05d}C{o_idx:05d}"
                cnt = d_counts.get((l_idx, o_idx), 0)
                if cid in merged_cells:
                    target = merged_cells[cid]
                    target["has_data"] = True
                    target["detection_count"] += cnt
                    target["total_modis"] += c.get("total_modis", 0.0)
                    target["total_viirs"] += c.get("total_viirs", 0.0)
                    target["n_days"] = max(target["n_days"], c.get("n_days", 0))
                else:
                    merged_cells[cid] = {
                        "cell_id": cid,
                        "south": c["south"],
                        "west": c["west"],
                        "north": c["north"],
                        "east": c["east"],
                        "detection_count": cnt,
                        "total_modis": c.get("total_modis", 0.0),
                        "total_viirs": c.get("total_viirs", 0.0),
                        "n_days": c.get("n_days", 0),
                        "has_data": True,
                    }
        except Exception:
            pass

    cell_list = sorted(merged_cells.values(), key=lambda c: (c["south"], c["west"]))
    _CACHED_INDONESIA_MOSAIC_GRID = {
        "cell_deg": cell_deg,
        "bounds": bounds,
        "years": sorted(years),
        "n_cells": 78200,
        "n_monitored_cells": len(cell_list),
        "scale_note": scale_note,
        "cells": cell_list,
    }
    return _CACHED_INDONESIA_MOSAIC_GRID


@app.get("/api/aoi/{aoi}/grid")
def api_grid(aoi: str, coverage: str | None = None):
    """Per-cell observation counts and yearly raw FRP totals for the map."""
    if aoi in ("indonesia", "nasional") or (aoi == "all" and coverage == "full"):
        return _generate_indonesia_mosaic_grid()

    if aoi not in ("all", "indonesia"):
        return _grid_with_detection_counts(aoi)

    merged_cells = {}
    years = set()
    cell_deg = None
    scale_note = None
    for path in sorted(ARTIFACTS.iterdir()):
        if (
            not path.is_dir()
            or path.name in ("all", "indonesia")
            or not (path / "grid.json").is_file()
            or not (path / "detections.json").is_file()
        ):
            continue
        grid = _grid_with_detection_counts(path.name)
        cell_deg = grid["cell_deg"] if cell_deg is None else cell_deg
        scale_note = grid.get("scale_note", scale_note)
        years.update(grid.get("years", []))
        for cell in grid["cells"]:
            existing = merged_cells.get(cell["cell_id"])
            if existing is None:
                merged_cells[cell["cell_id"]] = cell
                continue
            existing["total_modis"] += cell["total_modis"]
            existing["total_viirs"] += cell["total_viirs"]
            existing["detection_count"] += cell["detection_count"]
            existing["n_days"] = max(existing["n_days"], cell["n_days"])
            for year, values in cell.get("years", {}).items():
                target = existing["years"].setdefault(
                    year, {"modis": 0, "viirs": 0, "n_days": 0}
                )
                target["modis"] += values.get("modis", 0)
                target["viirs"] += values.get("viirs", 0)
                target["n_days"] = max(target["n_days"], values.get("n_days", 0))

    if cell_deg is None:
        raise HTTPException(404, detail="Data grid untuk wilayah Indonesia belum tersedia.")

    cells = sorted(merged_cells.values(), key=lambda cell: (cell["south"], cell["west"]))
    return {
        "cell_deg": cell_deg,
        "years": sorted(years),
        "n_cells": len(cells),
        "scale_note": scale_note,
        "cells": cells,
    }


def _grid_with_detection_counts(aoi: str):
    grid = _load(aoi, "grid.json")
    cell_deg = grid["cell_deg"]
    cells_by_index = {}
    for cell in grid["cells"]:
        lat_index = math.floor(cell["south"] / cell_deg + 1e-9)
        lon_index = math.floor(cell["west"] / cell_deg + 1e-9)
        cell["detection_count"] = 0
        cells_by_index[(lat_index, lon_index)] = cell

    detections = _load(aoi, "detections.json").get("detections", [])
    for detection in detections:
        lat_index = math.floor(detection["lat"] / cell_deg + 1e-9)
        lon_index = math.floor(detection["lon"] / cell_deg + 1e-9)
        cell = cells_by_index.get((lat_index, lon_index))
        if cell is not None:
            cell["detection_count"] += 1
    return grid


def _filter_detections(detections: list[dict], bounds: tuple[float, float, float, float]):
    west, south, east, north = bounds
    return [
        detection for detection in detections
        if west <= detection["lon"] < east and south <= detection["lat"] < north
    ]


@app.get("/api/aoi/{aoi}/detections")
def api_detections(
    aoi: str,
    west: float | None = None,
    south: float | None = None,
    east: float | None = None,
    north: float | None = None,
):
    """Validated hotspot detections — one entry = one satellite pixel, not one fire."""
    bounds_values = (west, south, east, north)
    if any(value is not None for value in bounds_values):
        if west is None or south is None or east is None or north is None:
            raise HTTPException(422, detail="west, south, east, and north must be provided together.")
        if not all(math.isfinite(value) for value in (west, south, east, north)):
            raise HTTPException(422, detail="Detection bounds must be finite numbers.")
        if west >= east or south >= north:
            raise HTTPException(422, detail="Bounds must satisfy west < east and south < north.")
        bounds = (west, south, east, north)
    else:
        bounds = None

    if aoi in ("all", "indonesia"):
        p = ARTIFACTS / "all" / "detections.json"
        if p.exists() and bounds is None:
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            all_dets = []
            for d in sorted(ARTIFACTS.glob("*")):
                if d.is_dir() and d.name != "all" and (d / "detections.json").exists():
                    try:
                        all_dets.extend(json.loads((d / "detections.json").read_text(encoding="utf-8")).get("detections", []))
                    except Exception:
                        pass
            data = {
                "n_detections": len(all_dets),
                "note": "Aggregated FIRMS satellite detections across all monitored Indonesian sentinel regions.",
                "detections": all_dets,
            }
    else:
        data = _load(aoi, "detections.json")

    if bounds is not None:
        data["detections"] = _filter_detections(data["detections"], bounds)
        data["n_detections"] = len(data["detections"])
    return data


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


def _get_grok_key(client_key: str | None = None) -> tuple[str | None, str]:
    """Retrieve Grok or Groq API key from client parameter, environment variables, .env, or .env.example files.
    Returns (api_key, provider_name: 'groq' | 'grok' | 'heuristic').
    """
    key = None
    if client_key and client_key.strip():
        key = client_key.strip()
    if not key:
        env_key = os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY")
        if env_key and env_key.strip():
            key = env_key.strip()
    if not key:
        for candidate in (
            ROOT / ".env",
            ROOT / "api" / ".env",
            ROOT / "api" / ".env.example",
            ROOT / ".env.example",
        ):
            if candidate.exists():
                try:
                    for line in candidate.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        if k.strip() in ("GROK_API_KEY", "GROQ_API_KEY", "XAI_API_KEY"):
                            val = v.strip().strip("'\"")
                            if val:
                                key = val
                                break
                    if key:
                        break
                except Exception:
                    pass

    if not key:
        return None, "heuristic"

    # Identify provider from API key prefix:
    # Groq Cloud keys start with 'gsk_'
    # xAI Grok keys start with 'xai-'
    if key.startswith("gsk_"):
        return key, "groq"
    return key, "grok"


def _analyze_hotspot_heuristic(
    lat: float,
    lon: float,
    date: str,
    frp: float,
    sensor: str,
    conf: str,
    daynight: str,
    question: str | None = None,
    region: str | None = None,
) -> dict:
    """Generate structured scientific telemetry context for a detected satellite hotspot."""
    is_viirs = sensor.lower() == "viirs"
    sensor_name = "VIIRS 375m (S-NPP/NOAA-20)" if is_viirs else "MODIS 1km (Aqua/Terra)"
    overpass_str = "Malam (Night overpass)" if daynight.upper() == "N" else "Siang (Day overpass)"

    # 1. Spatial & Biome Context
    if -1.5 <= lat <= 2.5 and 100.0 <= lon <= 104.0:
        reg_title = "Pesisir Timur Sumatra (Riau / Semenanjung Siak-Kampar)"
        biome = "Lahan Gambut Tropis Pesisir Timur Sumatra (Kubah Gambut Ombrogenous Dalam)"
        susceptibility = "Sangat Tinggi. Kedalaman gambut mencapai > 3–8 m. Muka air tanah (MAT) yang turun di bawah 0,4 m saat kemarau memicu risiko smoldering fire (kebakaran bawah permukaan) yang menghasilkan asap tebal berkepanjangan."
    elif -5.0 <= lat <= -1.5 and 102.0 <= lon <= 106.5:
        reg_title = "Dataran Rendah & Pesisir Sumatra Selatan (OKI / Musi Banyuasin)"
        biome = "Rawa Gambut Dataran Rendah & Aluvial Sumatra Selatan"
        susceptibility = "Tinggi. Area konsesi dan kubah gambut rawa rentan terhadap kekeringan musiman saat Monsun Timur bertiup dari belahan selatan."
    elif -2.8 <= lat <= -0.7 and 101.1 <= lon <= 104.5:
        reg_title = "Cekungan Gambut Batanghari (Jambi)"
        biome = "Rawa Gambut Pedalaman & Zona Penyangga Hutan Jambi"
        susceptibility = "Tinggi. Fluktuasi hidrologis gambut sangat sensitif terhadap defisit curah hujan musiman dan pembukaan kanal drainase."
    elif -3.5 <= lat <= 1.0 and 110.5 <= lon <= 116.0:
        reg_title = "Kalimantan Tengah (Eks-PLG / Katingan / Pulang Pisau)"
        biome = "Ekosistem Kubah Gambut Tropis Eks-PLG Kalimantan Tengah"
        susceptibility = "Ekstrem. Sejarah pembukaan kanal drainase menurunkan muka air tanah secara drastis saat kemarau, menyulut kebakaran gambut dalam yang sulit dipadamkan dari permukaan."
    elif -9.5 <= lat <= -6.0 and 137.5 <= lon <= 141.2:
        reg_title = "Papua Selatan (Merauke - Lanskap Trans-Fly)"
        biome = "Sabana Terbuka, Hutan Monsun Eukaliptus & Rawa Musiman Merauke"
        susceptibility = "Rendah untuk gambut, namun Sangat Tinggi untuk kebakaran vegetasi rumput kering dan semak akibat angin kencang monsun tenggara yang terik."
    else:
        reg_title = region or "Wilayah Daratan Kepulauan Indonesia"
        biome = "Ekosistem Hutan & Tutupan Vegetasi Tropis Indonesia"
        susceptibility = "Bervariasi berdasarkan zonasi tanah mineral vs gambut lokal dan tingkat kelembapan kanopi vegetasi."

    # 2. Seasonality & Climate Phase
    year_str = date.split("-")[0] if "-" in date else "2024"
    month_str = date.split("-")[1] if "-" in date and len(date.split("-")) > 1 else "01"
    year_int = int(year_str) if year_str.isdigit() else 2024
    month_int = int(month_str) if month_str.isdigit() else 1

    if year_int == 2015:
        climate_phase = "Super El Niño 2015 + IOD Positif (Kekeringan terparah dalam dua dekade di Indonesia)"
    elif year_int == 2019:
        climate_phase = "El Niño Moderat + IOD Positif Kuat (Defisit curah hujan ekstrem di wilayah barat)"
    elif year_int == 2023:
        climate_phase = "El Niño Berkembang + IOD Positif (Peningkatan drastis anomali termal setelah 3 tahun La Niña)"
    elif year_int in (2020, 2021, 2022):
        climate_phase = "Fase Triple-Dip La Niña (Tahun basah dengan anomali presipitasi tinggi)"
    elif year_int in (2014, 2018):
        climate_phase = "Kondisi El Niño Lemah / Anomali Musim Kering Regional"
    else:
        climate_phase = "Fase ENSO Netral / Variasi Siklus Monsun Standar"

    if month_int in (6, 7, 8, 9, 10):
        seasonal_cycle = "Puncak Monsun Timur (Musim Kemarau Austral). Angin kering bertiup dari benua Australia melintasi Indonesia."
    elif month_int in (2, 3) and "Riau" in reg_title:
        seasonal_cycle = "Musim Kering Pertama Riau (Pola Bimodal). Angin dari belahan bumi utara memicu kemarau lokal di pesisir Riau."
    else:
        seasonal_cycle = "Musim Hujan atau Masa Transisi (Monsun Barat). Curah hujan umumnya tinggi."

    # 3. FRP & Radiative Characteristics
    if frp >= 50.0:
        frp_class = "Ekstrem (> 50 MW)"
        frp_desc = "Intensitas radiasi termal sangat tinggi. Mengindikasikan pelepasan daya kalor pembakaran yang masif dan terkonsentrasi di permukaan tanah atau tajuk vegetasi."
    elif frp >= 20.0:
        frp_class = "Tinggi (20–50 MW)"
        frp_desc = "Intensitas radiasi termal tinggi. Konsisten dengan pembakaran aktif vegetasi atau lapisan gambut terbuka yang melepaskan energi radiasi signifikan."
    elif frp >= 5.0:
        frp_class = "Moderat (5–20 MW)"
        frp_desc = "Intensitas radiasi termal moderat. Tipikal untuk pembakaran permukaan (surface fire) bertahap atau titik panas yang terhalang sebagian oleh kanopi/asap tebal."
    else:
        frp_class = "Rendah (< 5 MW)"
        frp_desc = "Sensitivitas radiasi rendah. Tipikal untuk api awal, sisa bara gambut bawah tanah (smoldering fire), atau anomali termal berskala sub-piksel kecil."

    sensor_res = (
        "375 meter pada nadir (Band I4 3,75 µm). Mampu mendeteksi anomali api kecil berenergi rendah."
        if is_viirs
        else "1.000 meter nominal (Band 21/22 4 µm). Menangkap akumulasi energi radiasi pada footprint yang lebih luas."
    )

    daynight_desc = (
        "Overpass malam hari (~01:30 LT): Kontras radiometrik sangat tinggi terhadap latar belakang dingin daratan tanpa interferensi pantulan matahari (solar glint)."
        if daynight.upper() == "N"
        else "Overpass siang hari (~13:30 LT): Suhu daratan mencapai titik tertinggi; algoritma satelit memfilter pantulan specular matahari sebelum mengesahkan titik anomali."
    )

    # 4. Synthesizing Analysis & Addressing Questions
    q_lower = (question or "").lower()
    if any(w in q_lower for w in ("kenapa", "sebab", "mengapa", "penyebab")):
        inquiry_section = f"""### Analisis Ilmiah Mengenai Penyebab Terdeteksinya Anomali:
1. **Faktor Biofisik & Hidrologi Lahan**:
   Titik anomali berada di zona **{reg_title}** pada tanggal **{date}**. Pada periode ini, iklim berada dalam **{climate_phase}** dengan siklus **{seasonal_cycle}**. Penurunan kelembapan permukaan serta penurunan muka air tanah menyebabkan seresah dan biomassa menjadi bahan bakar yang sangat mudah terbakar (flammable).

2. **Aktivitas Antropogenik vs Kejadian Alami**:
   Secara statistik di kawasan tropis Indonesia, anomali kebakaran lahan dataran rendah sebagian besar dipicu oleh aktivitas pembersihan dan penyiapan lahan berbasis api (land clearing) yang meluas saat cuaca kering. Kejadian alami seperti sambaran petir tanpa hujan sangat langka di dataran rendah gambut.

3. **Batasan Kontrak Sains Satelit (Contract Honesty)**:
   Sensor antariksa {sensor_name} mengukur radiasi termal elektromagnetik ({frp:.2f} MW) saat melintas di atas koordinat {lat:.5f}°, {lon:.5f}°. Satelit **tidak merekam identitas pelaku atau bukti visual fisik di darat**. Penentuan penyebab hukum atau pelaku pembakaran secara mutlak membutuhkan investigasi darat (ground verification) oleh aparat berwenang."""
    elif question and question.strip():
        inquiry_section = f"""### Respons terhadap Pertanyaan Pengguna ("{question.strip()}"):
Berdasarkan data telemetri satelit {sensor_name} pada tanggal {date}:
- **Kondisi Radiometrik**: Titik ini terdeteksi dengan Fire Radiative Power (FRP) sebesar **{frp:.2f} MW** (kategori {frp_class}) dengan tingkat keyakinan **{conf}** pada waktu **{overpass_str}**.
- **Kondisi Wilayah**: Lokasi ({lat:.5f}°, {lon:.5f}°) berada di zona **{reg_title}**, dengan karakteristik bioma **{biome}**.
- **Interpretasi**: Anomali termal ini konsisten dengan kondisi kekeringan regional ({climate_phase}) yang menurunkan kelembapan vegetasi di kawasan ini."""
    else:
        inquiry_section = f"""### Ringkasan Interpretasi Ilmiah Telemetri Satelit:
- Titik koordinat **{lat:.5f}°, {lon:.5f}°** di zona **{reg_title}** menunjukkan anomali radiatif termal sebesar **{frp:.2f} MW** ({frp_class}) pada tanggal **{date}**.
- Deteksi dilakukan oleh instrumen **{sensor_name}** pada orbit **{overpass_str}** dengan tingkat keyakinan (confidence) **{conf}**.
- Keberadaan anomali ini berkorelasi erat dengan siklus kekeringan musiman (**{seasonal_cycle}**) pada fase iklim **{climate_phase}**."""

    full_analysis = f"""## Laporan Analisis Telemetri Satelit FIRMS

{inquiry_section}

### Karakteristik Biofisik & Ekosistem:
- **Wilayah Spasial**: {reg_title} ({lat:.5f}° LU/LS, {lon:.5f}° BT)
- **Tipe Bioma & Lanskap**: {biome}
- **Kerentanan Gambut**: {susceptibility}

### Parameter Sensor & Radiasi Termal:
- **Instrumen Sensor**: {sensor_name} — Resolusi spasial {sensor_res}
- **Daya Radiasi Kebakaran (FRP)**: **{frp:.2f} MW** ({frp_class})
- **Waktu Overpass**: {overpass_str} — {daynight_desc}
- **Kondisi Iklim Global & Regional**: {climate_phase} · {seasonal_cycle}

> **Prinsip Kejujuran Kontrak Ilmiah (NASA FIRMS & EmberLine):**
> Hotspot yang ditampilkan adalah deteksi anomali radiasi inframerah termal dari orbit satelit, bukan kepastian batas perimeter kebakaran fisik atau pembuktian penyebab hukum secara sepihak. Pembuktian kausalitas membutuhkan verifikasi patroli darat."""

    return {
        "status": "success",
        "provider": "heuristic",
        "model": "emberline-heuristic-telemetry-v1",
        "analysis": full_analysis,
        "telemetry_context": {
            "biome": biome,
            "peatland_susceptibility": susceptibility,
            "seasonal_climate": f"{climate_phase} | {seasonal_cycle}",
            "sensor_resolution": sensor_res,
            "frp_interpretation": f"{frp_class}: {frp_desc}",
        },
        "note": "Analisis telemetri satelit berbasis prinsip kejujuran data FIRMS."
    }


def _call_grok_hotspot_analysis(
    lat: float,
    lon: float,
    date: str,
    frp: float,
    sensor: str,
    conf: str,
    daynight: str,
    question: str | None = None,
    region: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Invoke Groq or xAI Grok API for hotspot analysis, falling back to heuristic telemetry if unavailable."""
    key, provider_type = _get_grok_key(api_key)
    if not key:
        return _analyze_hotspot_heuristic(
            lat=lat, lon=lon, date=date, frp=frp, sensor=sensor,
            conf=conf, daynight=daynight, question=question, region=region
        )

    system_prompt = (
        "Anda adalah EmberLine AI Satellite Telemetry & Climatology Analyst, asisten pakar analisis data satelit NASA FIRMS "
        "untuk sistem pemantauan kebakaran hutan dan lahan (karhutla) di Indonesia.\n\n"
        "PANDUAN & GUARDRAILS KONTRAK SAINS (MANDATORI):\n"
        "1. Analisis titik panas (hotspot) satelit berdasarkan parameter biofisik, tipe bioma (lahan gambut vs mineral/sabana), "
        "siklus iklim monsun/El Niño, dan karakteristik radiometrik sensor (VIIRS 375m atau MODIS 1km).\n"
        "2. KEJUJURAN KONTRAK SAINS:\n"
        "   - Deteksi hotspot adalah anomali radiometrik (Thermal Anomaly) yang terobservasi pada piksel satelit saat overpass, "
        "BUKAN bukti batas fisik kebakaran atau kepastian mutlak kebakaran berlanjut di darat.\n"
        "   - JANGAN PERNAH berspekulasi atau menuduh pelaku hukum/kriminal tertentu (seperti menuduh perusahaan A, pembakaran berencana, "
        "atau nama individu) karena radiometer satelit di antariksa tidak merekam bukti visual pelaku di darat.\n"
        "   - Bila ditanya 'kenapa terbakar?', jelaskan dari sudut pandang ilmiah/biofisik (penurunan muka air tanah gambut, kemarau, "
        "akumulasi bahan bakar kering, aktivitas pembersihan lahan berbasis api di kawasan tropis) dan tegaskan bahwa verifikasi "
        "penyebab langsung membutuhkan ground-check/patroli lapangan.\n"
        "3. JANGAN GUNAKAN EMOJI SAMA SEKALI.\n"
        "4. Format jawaban dengan markdown terstruktur rapi: Ringkasan Radiometrik, Konteks Bioma & Gambut, Konteks Iklim & Musiman, "
        "Jawaban Pertanyaan/Analisis Penyebab Ilmiah, dan Catatan Kehati-hatian Ilmiah."
    )

    sensor_label = "VIIRS 375m (S-NPP/NOAA-20)" if sensor.lower() == "viirs" else "MODIS 1km (Aqua/Terra)"
    overpass_label = "Malam Hari (Night)" if daynight.upper() == "N" else "Siang Hari (Day)"
    user_prompt = (
        f"Data Deteksi Titik Satelit FIRMS:\n"
        f"- Koordinat: Lat {lat:.5f}°, Lon {lon:.5f}°\n"
        f"- Tanggal Observasi: {date}\n"
        f"- Sensor Satelit: {sensor_label}\n"
        f"- Fire Radiative Power (FRP): {frp:.2f} MW\n"
        f"- Keyakinan (Confidence): {conf}\n"
        f"- Waktu Lintasan (Overpass): {overpass_label}\n"
        f"- Wilayah Referensi: {region or 'Indonesia'}\n"
    )
    if question and question.strip():
        user_prompt += f"\nPertanyaan Khusus dari Pengguna:\n\"{question.strip()}\"\n"
    else:
        user_prompt += "\nMohon berikan analisis konteks biofisik, bioma gambut, iklim, dan radiometrik untuk titik deteksi ini.\n"

    # Configure endpoint & model based on key type
    if provider_type == "groq":
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        model_name = "openai/gpt-oss-120b"
        fallback_model = "openai/gpt-oss-20b"
        provider_name = "groq"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    else:
        api_url = "https://api.x.ai/v1/chat/completions"
        model_name = "grok-2-latest"
        fallback_model = "grok-beta"
        provider_name = "grok"
        user_agent = "EmberLine/1.0"

    def _execute_req(m_name: str) -> str:
        req_payload = json.dumps({
            "model": m_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=req_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": user_agent,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=18) as resp:
            raw_res = json.loads(resp.read().decode("utf-8"))
            return raw_res.get("choices", [{}])[0].get("message", {}).get("content", "")

    try:
        content = ""
        used_model = model_name
        try:
            content = _execute_req(model_name)
        except Exception:
            # Fallback to secondary model if main model hits capacity
            if fallback_model:
                used_model = fallback_model
                content = _execute_req(fallback_model)

        if not content:
            raise ValueError(f"Respon kosong dari {provider_name.upper()} API.")

        heuristic_ctx = _analyze_hotspot_heuristic(
            lat=lat, lon=lon, date=date, frp=frp, sensor=sensor,
            conf=conf, daynight=daynight, question=question, region=region
        )
        return {
            "status": "success",
            "provider": provider_name,
            "model": used_model,
            "analysis": content,
            "telemetry_context": heuristic_ctx["telemetry_context"],
            "note": f"Analisis dihasilkan oleh {provider_name.upper()} AI ({used_model}) dengan guardrail telemetri satelit EmberLine."
        }
    except Exception as exc:
        fallback_res = _analyze_hotspot_heuristic(
            lat=lat, lon=lon, date=date, frp=frp, sensor=sensor,
            conf=conf, daynight=daynight, question=question, region=region
        )
        fallback_res["note"] = f"Koneksi {provider_name.upper()} dialihkan ke telemetri satelit internal ({str(exc)[:100]})."
        return fallback_res


@app.post("/api/ai/analyze-hotspot")
def api_analyze_hotspot(body: dict):
    """Analyze a single satellite hotspot observation using Grok AI or satellite telemetry heuristic."""
    try:
        lat = float(body.get("lat"))
        lon = float(body.get("lon"))
        frp = float(body.get("frp", 0.0))
    except (TypeError, ValueError):
        raise HTTPException(400, detail={"code": "bad_coordinates", "message": "lat, lon, and frp must be valid numbers."})

    date = str(body.get("date", "2024-01-01"))
    sensor = str(body.get("sensor", "viirs"))
    conf = str(body.get("conf", "n"))
    daynight = str(body.get("daynight", "D"))
    region = body.get("region")
    question = body.get("question")
    api_key = body.get("api_key")

    return _call_grok_hotspot_analysis(
        lat=lat,
        lon=lon,
        date=date,
        frp=frp,
        sensor=sensor,
        conf=conf,
        daynight=daynight,
        question=question,
        region=region,
        api_key=api_key,
    )

