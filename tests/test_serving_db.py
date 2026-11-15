"""C-07 contract test — derived SQLite serving artifact (pipeline/serving_db.py).

Verifies the serving.db built from the REAL artifacts of an AOI: provenance
meta present, table row counts match the canonical CSVs, bounds stay ordered,
N/A metrics stored as NULL+reason (never 0), indexed date queries correct,
deterministic content across rebuilds, and honest meta-only DB for missing
sources (no fabricated tables).

Run standalone:  python tests/test_serving_db.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import serving_db  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "artifacts/riau"


def _rows(db: str, query: str, params=()):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    out = [dict(r) for r in con.execute(query, params).fetchall()]
    con.close()
    return out


def _content_dump(db: str) -> str:
    con = sqlite3.connect(db)
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    dump = []
    for t in tables:
        rows = con.execute(f"SELECT * FROM {t} ORDER BY 1, 2").fetchall()
        dump.append(f"{t}:{rows}")
    con.close()
    return "\n".join(dump)


def check_list():
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    if not REAL.exists():
        check("real Riau artifacts present", False, f"{REAL} missing — run make reproduce first")
        return checks

    # -- build from real artifacts --------------------------------------------------
    stats = serving_db.build(REAL, "riau")
    db = stats["db"]
    con = sqlite3.connect(db)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    check("serving.db created with all expected tables",
          {"meta", "accepted_series", "calendar", "windows", "baselines",
           "harmonized_daily", "metrics", "splice_stress", "years"} <= tables,
          f"got {sorted(tables)}")

    # -- row counts match canonical CSVs ----------------------------------------------
    def csv_lines(p: Path) -> int:
        return max(sum(1 for _ in open(p, encoding="utf-8")) - 1, 0)

    n_series = csv_lines(REAL / "accepted_series.csv")
    n_cal = csv_lines(REAL / "calendar.csv")
    n_harm = csv_lines(REAL / "harmonized_daily.csv")
    n_base = csv_lines(REAL / "baseline_series.csv")
    check("accepted_series rows == canonical CSV rows",
          _rows(db, "SELECT COUNT(*) c FROM accepted_series")[0]["c"] == n_series)
    check("calendar has exactly 366 positions",
          _rows(db, "SELECT COUNT(*) c FROM calendar")[0]["c"] == 366)
    check("harmonized_daily rows == canonical CSV rows",
          _rows(db, "SELECT COUNT(*) c FROM harmonized_daily")[0]["c"] == n_harm)
    check("baselines rows == canonical CSV rows",
          _rows(db, "SELECT COUNT(*) c FROM baselines")[0]["c"] == n_base)

    # -- meta provenance -----------------------------------------------------------------
    meta = {r["key"]: r["value"] for r in _rows(db, "SELECT * FROM meta")}
    check("meta carries run_id/protocol/aoi/era/descriptive+reference notes",
          meta.get("run_id", "").startswith("PROTO-C01-v0.9")
          and meta.get("aoi_id") == "riau"
          and "never a forecast" in meta.get("descriptive_note", "")
          and "ground truth" in meta.get("reference_note", ""))
    check("missing_sources honest (empty when artifacts complete)",
          isinstance(json.loads(meta.get("missing_sources", "[]")), list))

    # -- bounds ordered; N/A stored as NULL+reason ---------------------------------------
    bad_bounds = _rows(db, """SELECT date FROM harmonized_daily
        WHERE predicted_b2_mw IS NOT NULL AND
              NOT (lo_mw <= predicted_b2_mw AND predicted_b2_mw <= hi_mw)""")
    check("harmonized bounds finite & ordered (lo <= est <= hi)", not bad_bounds,
          f"violations: {bad_bounds[:3]}")
    na_rows = _rows(db, "SELECT * FROM metrics WHERE status = 'N/A'")
    ok_rows = _rows(db, "SELECT * FROM metrics WHERE status = 'ok'")
    check("N/A metrics stored as NULL value + reason (never fabricated 0)",
          all(r["value"] is None and r["reason"] for r in na_rows)
          and len(na_rows) >= 1 and len(ok_rows) >= 20,
          f"na={len(na_rows)} ok={len(ok_rows)}")

    # -- indexed date-range query (what D serves) ------------------------------------------
    rows = _rows(db, """SELECT date, value_mw, index_value, source_flag FROM accepted_series
        WHERE date >= '2024-01-01' AND date < '2024-03-01' ORDER BY date""")
    check("indexed date-range query returns correct subset",
          len(rows) == 60 and all("2024-01-01" <= r["date"] < "2024-03-01" for r in rows)
          and all(r["source_flag"] == "harmonized_viirs" for r in rows),
          f"got {len(rows)}")

    # -- splice stress: both methods visible incl. negative result -------------------------
    stress = _rows(db, "SELECT * FROM splice_stress")
    methods = {r["method"] for r in stress}
    check("splice_stress carries B2 AND B1 (negative results stay visible)",
          any(m.startswith("B1") for m in methods) and "B2" in methods
          and len(stress) >= 5,
          f"got {methods}, {len(stress)} rows")
    check("no fabricated p-values anywhere",
          "p_value" not in json.dumps(_rows(db, "SELECT * FROM meta")).lower())

    # -- determinism: same sources -> identical content -------------------------------------
    db2 = Path(tempfile.mkdtemp(prefix="sdb_")) / "serving.db"
    stats2 = serving_db.build(REAL, "riau")
    check("rebuild produces identical content (deterministic derivation)",
          _content_dump(db) == _content_dump(str(stats2["db"])))
    check("sha256 recorded for deployment integrity",
          stats["sha256"] == stats2["sha256"] and len(stats["sha256"]) == 64)

    # -- honest meta-only DB when sources absent ---------------------------------------------
    empty = Path(tempfile.mkdtemp(prefix="sdb_empty_"))
    stats_empty = serving_db.build(empty, "ghost")
    con = sqlite3.connect(empty / "serving.db")
    tables2 = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    check("missing sources -> honest meta-only DB, no fabricated tables",
          "accepted_series" not in tables2
          and "missing_sources" in {r[0] for r in
                                    sqlite3.connect(str(empty / "serving.db"))
                                    .execute("SELECT key FROM meta")})

    return checks


def _report(checks):
    failed = [(n, d) for n, ok_, d in checks if not ok_]
    for name, okv, detail in checks:
        print(f"[{'PASS' if okv else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not okv else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def test_serving_db():
    failed = [(n, d) for n, ok_, d in check_list() if not ok_]
    assert not failed, f"serving-db violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(check_list()))
