"""EmberLine C-07 — derived SQLite serving artifact (DEV-S05 clarification).

Owner: team member C. Contract test: tests/test_serving_db.py.

The CANONICAL artifacts are the CSV/JSON files written by C-02..C-06 (human
readable, provenance-friendly). This module DERIVES a single indexed SQLite
file (`artifacts/<aoi>/serving.db`) from them so the backend — whatever stack
it ends up being (Rust/FastAPI/Go/Node/Python all read SQLite natively) — can
serve indexed date-range and per-position queries without parsing CSVs at
request time.

Rules:
- The .db is a DERIVED artifact: regenerated deterministically by
  `make reproduce`; it is git-ignored (binary derivative) and its sha256 is
  recorded in run_manifest.json.
- Missing upstream artifacts (deferred/insufficient stages) mean MISSING
  tables plus an honest `meta.stage_status` row — the DB never fabricates
  rows to fill gaps, and N/A metrics are stored as NULL + reason, never 0.
- No credentials, no write access granted to the backend (open read-only).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _num(v):
    if v in (None, "", "None"):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_json(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(artifacts_dir: str | Path, aoi_id: str) -> dict:
    """Derive `serving.db` from the canonical artifacts of one AOI."""
    art = Path(artifacts_dir)
    db_path = art / "serving.db"
    if db_path.exists():
        db_path.unlink()  # derived: always rebuilt from canonical sources

    run_manifest = _load_json(art / "run_manifest.json") or {}
    model_manifest = _load_json(art / "model_manifest.json") or {}
    climatology = _load_json(art / "climatology.json") or {}
    windows_manifest = _load_json(art / "windows.json") or {}
    metrics_manifest = _load_json(art / "harmonization_metrics.json") or {}
    stress_files = [("B2", art / "splice_stress_test.json"),
                    ("B1", art / "splice_stress_test_b1.json")]
    baselines_manifest = _load_json(art / "baselines.json") or {}

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # -- meta (provenance + honest stage state) ---------------------------------
    cur.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    meta_rows = [
        ("protocol_version", run_manifest.get("protocol_version", "PROTO-C01-v0.9")),
        ("run_id", run_manifest.get("run_id", "unknown")),
        ("git_sha", run_manifest.get("git_sha", "unknown")),
        ("aoi_id", aoi_id),
        ("bbox", str(run_manifest.get("aoi_bbox_date_range", {}).get("bbox", ""))),
        ("era_start", str(run_manifest.get("aoi_bbox_date_range", {}).get("start", ""))),
        ("era_end", str(run_manifest.get("aoi_bbox_date_range", {}).get("end", ""))),
        ("sources", ",".join(run_manifest.get("sources", []))),
        ("train_years", json.dumps(run_manifest.get("train_years"))),
        ("test_years", json.dumps(run_manifest.get("test_years"))),
        ("index_denominator_mw", str((model_manifest.get("outcome", {})
                                      .get("status") == "ok") and
                                     climatology.get("index", {}).get("denominator_mw"))),
        ("index_note", "idx = log1p(published AOI FRP-sum)/log1p(frozen P95 training "
                       "reference); AOI-specific, not comparable across regions"),
        ("descriptive_note", "historical & descriptive — never a forecast or "
                             "safe-to-burn recommendation"),
        ("reference_note", "MODIS is the reference measurement, not fire ground truth"),
    ]
    stage_statuses = run_manifest.get("stage_statuses", {})
    for stage, info in sorted(stage_statuses.items()):
        meta_rows.append((f"stage_{stage}", str(info.get("status"))))
    cur.executemany("INSERT INTO meta VALUES (?, ?)", meta_rows)

    missing: list[str] = []

    # -- accepted published series (F-14) ----------------------------------------
    accepted = _read_csv(art / "accepted_series.csv")
    if accepted:
        cur.execute("""CREATE TABLE accepted_series (
            date TEXT PRIMARY KEY, year INTEGER, position INTEGER,
            source_flag TEXT, value_mw REAL, index_value REAL,
            harmonized_mw REAL, observed_modis_mw REAL)""")
        cur.executemany("INSERT INTO accepted_series VALUES (?,?,?,?,?,?,?,?)",
                        [(r["date"], int(r["year"]), int(r["position"]), r["source_flag"],
                          _num(r["value_mw"]), _num(r["index"]), _num(r["harmonized_mw"]),
                          _num(r["observed_modis_mw"])) for r in accepted])
        cur.execute("CREATE INDEX idx_series_date ON accepted_series(date)")
        cur.execute("CREATE INDEX idx_series_pos ON accepted_series(position)")
    else:
        missing.append("accepted_series.csv")

    # -- calendar climatology (366 positions) --------------------------------------
    cal = _read_csv(art / "calendar.csv")
    if cal:
        cur.execute("""CREATE TABLE calendar (
            position INTEGER PRIMARY KEY, month INTEGER, day INTEGER,
            index_median_raw REAL, index_median_smoothed REAL,
            index_p10 REAL, index_p25 REAL, index_p75 REAL, index_p90 REAL,
            n_years INTEGER, years TEXT, state TEXT)""")
        cur.executemany("INSERT INTO calendar VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        [(int(r["position"]), int(r["month"]), int(r["day"]),
                          _num(r["index_median_raw"]), _num(r["index_median_smoothed"]),
                          _num(r["index_p10"]), _num(r["index_p25"]), _num(r["index_p75"]),
                          _num(r["index_p90"]), int(r["n_years"]), r["years"], r["state"])
                         for r in cal])
    else:
        missing.append("calendar.csv")

    # -- critical windows -----------------------------------------------------------
    win_rows = windows_manifest.get("windows", [])
    if win_rows:
        cur.execute("""CREATE TABLE windows (
            id INTEGER PRIMARY KEY, start_position INTEGER, end_position INTEGER,
            start_month_day TEXT, end_month_day TEXT, length_days INTEGER,
            wraps_dec_jan INTEGER, median_index_in_window REAL, max_index_in_window REAL)""")
        cur.executemany("INSERT INTO windows VALUES (?,?,?,?,?,?,?,?,?)",
                        [(i, w["start_position"], w["end_position"], w["start_month_day"],
                          w["end_month_day"], w["length_days"], int(w["wraps_dec_jan"]),
                          w["median_index_in_window"], w["max_index_in_window"])
                         for i, w in enumerate(win_rows, start=1)])
        for key in ("threshold", "years_eligible", "activity"):
            value = json.dumps(windows_manifest.get(key), sort_keys=True)
            cur.execute("INSERT INTO meta VALUES (?, ?)", (f"windows_{key}", value))
    else:
        missing.append("windows.json")

    # -- baselines (B0/B1) + harmonized daily (B2) -----------------------------------
    # Schema guard: legacy/foreign-schema artifacts (e.g. from other generators)
    # are NOT converted — recorded as missing with a note, never guessed.
    base_rows = _read_csv(art / "baseline_series.csv")
    base_cols = set(base_rows[0]) if base_rows else set()
    if base_rows and {"date", "daynight", "B0_naive_splice_mw", "B1_ratio_pred_mw"} <= base_cols:
        cur.execute("""CREATE TABLE baselines (
            date TEXT, daynight TEXT, role TEXT,
            modis_frp_sum_mw REAL, viirs_frp_sum_mw REAL,
            B0_naive_splice_mw REAL, B1_ratio_pred_mw REAL,
            PRIMARY KEY (date, daynight))""")
        cur.executemany("INSERT INTO baselines VALUES (?,?,?,?,?,?,?)",
                        [(r["date"], r["daynight"], r["role"],
                          _num(r["modis_frp_sum_mw"]), _num(r["viirs_frp_sum_mw"]),
                          _num(r["B0_naive_splice_mw"]), _num(r["B1_ratio_pred_mw"]))
                         for r in base_rows])
    elif base_rows:
        missing.append("baseline_series.csv:legacy-schema")

    harm_rows = _read_csv(art / "harmonized_daily.csv")
    harm_cols = set(harm_rows[0]) if harm_rows else set()
    if harm_rows and {"date", "daynight", "predicted_b2_mw", "lo_mw", "hi_mw"} <= harm_cols:
        cur.execute("""CREATE TABLE harmonized_daily (
            date TEXT, daynight TEXT, role TEXT, source_flag TEXT,
            n_cells_predicted INTEGER, observed_modis_mw REAL, predicted_b2_mw REAL,
            lo_mw REAL, hi_mw REAL, flags TEXT,
            PRIMARY KEY (date, daynight))""")
        cur.executemany("INSERT INTO harmonized_daily VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [(r["date"], r["daynight"], r["role"], r["source_flag"],
                          int(r.get("n_cells_predicted", 0) or 0), _num(r["observed_modis_mw"]),
                          _num(r["predicted_b2_mw"]), _num(r["lo_mw"]), _num(r["hi_mw"]),
                          r.get("flags", "")) for r in harm_rows])
        cur.execute("CREATE INDEX idx_harm_date ON harmonized_daily(date)")
    elif harm_rows:
        missing.append("harmonized_daily.csv:legacy-schema")
    else:
        missing.append("harmonized_daily.csv")

    # -- evaluation metrics (N/A stored as NULL + reason, never 0) --------------------
    outcome = metrics_manifest.get("outcome", {})
    metric_results = outcome.get("metrics", {})
    if metric_results:
        cur.execute("""CREATE TABLE metrics (
            method TEXT, metric TEXT, value REAL, status TEXT, reason TEXT,
            n INTEGER, n_excluded INTEGER, PRIMARY KEY (method, metric))""")
        rows = []
        for method, metric_map in metric_results.items():
            for metric, result in metric_map.items():
                value = result.get("value")
                rows.append((method, metric,
                             None if value == "N/A" else value,
                             "ok" if value != "N/A" else "N/A",
                             result.get("reason", ""),
                             int(result.get("n", 0)), int(result.get("n_excluded", 0))))
        cur.executemany("INSERT INTO metrics VALUES (?,?,?,?,?,?,?)", rows)
    else:
        missing.append("harmonization_metrics.json")

    # -- splice stress tests (B2 + accepted B1, both visible) --------------------------
    stress_rows = []
    for method, path in stress_files:
        manifest = _load_json(path) or {}
        for t in manifest.get("tests", []):
            stress_rows.append((
                method, t.get("transition_date"), t.get("status"),
                t.get("window", ["", ""])[0], t.get("window", ["", ""])[1],
                t.get("window_fraction"), t.get("shift_naive", {}).get("value"),
                t.get("shift_harmonized", {}).get("value"),
                t.get("shift_truth_continued_modis", {}).get("value"),
                t.get("error_naive"), t.get("error_harmonized"),
                t.get("error_ratio") if isinstance(t.get("error_ratio"), (int, float)) else None,
                t.get("error_ratio_reason", t.get("interpretation", ""))))
    if stress_rows:
        cur.execute("""CREATE TABLE splice_stress (
            method TEXT, transition_date TEXT, status TEXT, window_start TEXT,
            window_end TEXT, window_fraction REAL, shift_naive REAL,
            shift_harmonized REAL, shift_truth REAL, error_naive REAL,
            error_harmonized REAL, error_ratio REAL, note TEXT,
            PRIMARY KEY (method, transition_date))""")
        cur.executemany("INSERT INTO splice_stress VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        stress_rows)
    else:
        missing.append("splice_stress manifests")

    # -- years (eligibility + activity) -------------------------------------------------
    era_days: dict[str, int] = {}
    valid_days: dict[str, int] = {}
    for r in accepted:
        year = r["year"]
        era_days[year] = era_days.get(year, 0) + 1
        if r["index"] not in (None, "", "None"):
            valid_days[year] = valid_days.get(year, 0) + 1
    activity = windows_manifest.get("activity", {})
    active_days = activity.get("active_days_per_year", {})
    if era_days:
        cur.execute("""CREATE TABLE years (
            year TEXT PRIMARY KEY, era_days INTEGER, valid_days INTEGER,
            eligible INTEGER, active INTEGER, active_days INTEGER)""")
        years_eligible = set(climatology.get("years_eligible", []))
        years_active = set(activity.get("years_active", []))
        cur.executemany("INSERT INTO years VALUES (?,?,?,?,?,?)",
                        [(y, era_days.get(y, 0), valid_days.get(y, 0),
                          int(y in years_eligible), int(y in years_active),
                          int(active_days.get(y, 0)))
                         for y in sorted(era_days)])
    else:
        missing.append("years (no accepted series)")

    cur.execute("INSERT INTO meta VALUES (?, ?)",
                ("missing_sources", json.dumps(missing)))
    con.commit()
    con.close()

    stats = {
        "db": str(db_path),
        "sha256": _sha256(db_path),
        "tables": {
            "accepted_series": len(accepted), "calendar": len(cal),
            "windows": len(win_rows), "baselines": len(base_rows),
            "harmonized_daily": len(harm_rows),
            "metrics": len(metric_results) * len(next(iter(metric_results.values()), {})),
            "splice_stress": len(stress_rows), "years": len(era_days),
        },
        "missing_sources": missing,
    }
    return stats


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-07 derived SQLite serving artifact")
    parser.add_argument("--artifacts", required=True, help="artifacts/<aoi> directory")
    parser.add_argument("--aoi-id", required=True)
    args = parser.parse_args(argv)
    stats = build(args.artifacts, args.aoi_id)
    print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
