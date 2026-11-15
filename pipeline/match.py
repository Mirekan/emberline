"""EmberLine C-02 — matched overlap aggregates (PROTO-C01-v0.9, F-5/F-6/F-7/F-9).

Owner: team member C. Contract test: tests/test_grid_match.py.

Produces the cell x UTC-day x day/night comparison units that C-03/C-04 fit on.
Per-sensor aggregates stay separate everywhere: detection count, FRP-sum (MW),
FRP-max and mean scan are computed per (cell, UTC day, day/night, source,
satellite) and are NEVER summed across sensors into a physical-fire count.

Integration seam with B-04/B-05 (the swap-in point for real data):

  detections rows (csv today, parquet once pyarrow is pinned) — expected columns:
    source, satellite, latitude, longitude, daynight, frp_mw   (required)
    acq_datetime_utc (ISO-8601 timezone-aware UTC)             (preferred time)
    acq_date + acq_time (HHMM, zero-padded)                    (accepted fallback,
      emits a disclosure warning — day comes from acq_date)
    version, confidence, confidence_class, scan, track         (kept when present)

  retrieval mask rows — expected columns: aoi_id, source, date (YYYY-MM-DD),
  status in {retrieved_rows, retrieved_empty, failed, unavailable, not_requested}.
  The mask is what separates "zero returned detections" from "missing retrieval".

Schema deviations HARD-FAIL with the exact missing/unknown fields (schema-blocked
state to resolve with B) — field meanings are never guessed (guide C-02 "If
blocked": do not broaden the source or alter fields to make rows fit).
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import date as _date, datetime, timezone
from pathlib import Path

from pipeline.grid import GridError, aoi_cell_ids, assign_cell, validate_bbox

PROTOCOL_VERSION = "PROTO-C01-v0.9"

# Unit-level states (F-6). fitting_eligible mirrors the frozen text: matched pairs
# include zero-detection retrievals; one-sided signal is retained but excluded.
ST_MATCHED_SIGNAL = "matched_signal"
ST_MATCHED_ZERO = "matched_zero"
ST_ONE_SIDED = "one_sided"
ST_MISSING_RETRIEVAL = "missing_retrieval"
ST_NOT_RETRIEVED = "not_retrieved"
FITTING_ELIGIBLE_STATES = {ST_MATCHED_SIGNAL, ST_MATCHED_ZERO}

RETRIEVAL_STATUSES = {"retrieved_rows", "retrieved_empty", "failed", "unavailable", "not_requested"}
RETRIEVED_STATUSES = {"retrieved_rows", "retrieved_empty"}

REQUIRED_DETECTION_COLUMNS = {"source", "satellite", "latitude", "longitude", "daynight", "frp_mw"}
TIME_COLUMNS_PREFERRED = {"acq_datetime_utc"}
TIME_COLUMNS_FALLBACK = {"acq_date", "acq_time"}
OPTIONAL_COLUMNS = {"version", "confidence", "confidence_class", "scan", "track"}

REQUIRED_MASK_COLUMNS = {"aoi_id", "source", "date", "status"}

# Provisional platform selection per params.yaml (DEC-1: exact FIRMS source
# strings pending B-01). Matching pairs only the reference vs target platform;
# other platforms are counted and disclosed as excluded_in_v1 — never blended.
_REFERENCE_SENSOR = "aqua_modis"   # from config/params.yaml sensors.reference_sensor
_TARGET_SENSOR = "snpp_viirs"      # from config/params.yaml sensors.viirs_platform

# DEC-1 RESOLVED (B-01 keyed probe + B-05 fetch): the exact FIRMS source strings
# are MODIS_SP and VIIRS_SNPP_SP. Platform acceptance is therefore SOURCE-based:
#   reference family = source contains 'modis' AND satellite == 'Aqua'
#     (Terra rows are counted and excluded — S-01, never blended);
#   target family    = source contains 'viirs' AND source contains 'snpp'.
# B-04 normalized VIIRS rows carry satellite='N' (FIRMS convention) — satellite
# stays a pass-through field and is NOT the platform discriminator for VIIRS.


class MatchError(ValueError):
    """Contract/protocol violation: hard-fail, resolve upstream — never guess."""


# --------------------------------------------------------------------------- io
def read_table(path: str | Path) -> list[dict]:
    """CSV today; parquet when pyarrow is pinned (D-01). Returns list[dict]."""
    path = Path(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        try:
            import pandas  # noqa: PLC0415
            dataframe = pandas.read_parquet(path)
        except ImportError as exc:
            raise MatchError(
                f"{path.name} is parquet but pyarrow is not installed; "
                "pip install pyarrow (D-01 pins dependencies) or ask B for a csv"
            ) from exc
        return dataframe.to_dict("records")
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _num(value, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise MatchError(f"non-numeric {field}: {value!r}") from exc
    if not math.isfinite(out):
        raise MatchError(f"non-finite {field}: {value!r}")
    return out


def validate_input_columns(rows: list[dict], label: str) -> set[str]:
    """Structural schema check — hard-fail on drift (protocol B-04 contract)."""
    if not rows:
        raise MatchError(f"{label}: no rows received")
    present = set(rows[0])
    missing = REQUIRED_DETECTION_COLUMNS - present
    has_preferred = TIME_COLUMNS_PREFERRED <= present
    has_fallback = TIME_COLUMNS_FALLBACK <= present
    if missing or not (has_preferred or has_fallback):
        problems = []
        if missing:
            problems.append(f"missing required columns: {sorted(missing)}")
        if not (has_preferred or has_fallback):
            problems.append(
                "no time columns: provide acq_datetime_utc (preferred) or acq_date + acq_time"
            )
        raise MatchError(f"{label}: schema mismatch — {'; '.join(problems)}")
    return present


# ------------------------------------------------------------------- row intake
def _norm_daynight(raw: str) -> str | None:
    value = str(raw).strip().lower()
    if value in {"d", "day"}:
        return "day"
    if value in {"n", "night"}:
        return "night"
    return None


def _norm_conf_class(raw) -> str | None:
    if raw is None or str(raw).strip() == "":
        return None
    value = str(raw).strip().lower()
    if value in {"l", "low"}:
        return "low"
    if value in {"n", "nominal"}:
        return "nominal"
    if value in {"h", "high"}:
        return "high"
    try:
        numeric = float(value)
    except ValueError:
        return "unknown"
    if numeric >= 80.0:
        return "high"
    if numeric >= 30.0:
        return "nominal"
    return "low"


def _utc_day(row: dict, warnings: set[str]) -> tuple[str, str] | None:
    """Return (utc_date 'YYYY-MM-DD', utc_time 'HHMM') or None when rejected."""
    if "acq_datetime_utc" in row and str(row.get("acq_datetime_utc", "")).strip():
        raw = str(row["acq_datetime_utc"]).strip()
        try:
            moment = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            warnings.add("invalid_acq_datetime_utc")
            return None
        if moment.tzinfo is None:
            warnings.add("naive_timestamp_rejected")
            return None
        moment = moment.astimezone(timezone.utc)
        return moment.strftime("%Y-%m-%d"), moment.strftime("%H%M")
    # Documented fallback: acq_date + zero-padded HHMM acq_time (B-04 semantics).
    raw_date, raw_time = str(row.get("acq_date", "")).strip(), str(row.get("acq_time", "")).strip()
    warnings.add("fallback_time_columns_used")
    try:
        day = _date.fromisoformat(raw_date)
    except ValueError:
        warnings.add("invalid_acq_date")
        return None
    padded = raw_time.zfill(4)
    if not (len(padded) == 4 and padded.isdigit() and int(padded[:2]) < 24 and int(padded[2:]) < 60):
        warnings.add("invalid_acq_time")
        return None
    return day.isoformat(), padded


def _family(source: str) -> str | None:
    value = str(source).strip().lower()
    if "modis" in value:
        return "modis"
    if "viirs" in value:
        return "viirs"
    return None


def _dedupe_key(row: dict, day: str, time: str, lat: float, lon: float) -> tuple:
    return (
        str(row.get("source")), str(row.get("satellite")), str(row.get("version")),
        day, time, lat, lon, str(row.get("daynight")).strip().lower(),
    )


def aggregate_units(
    detections: list[dict],
    bbox_west: float, bbox_south: float, bbox_east: float, bbox_north: float,
    aoi_id: str,
) -> tuple[list[dict], dict]:
    """Row-level intake -> per-sensor units. Returns (units, summary)."""
    bbox = validate_bbox(bbox_west, bbox_south, bbox_east, bbox_north)
    validate_input_columns(detections, "detections")
    warnings: set[str] = set()
    counts = defaultdict(int)
    units: dict[tuple, dict] = {}

    rows = sorted(
        detections,
        key=lambda r: (
            str(r.get("source")), str(r.get("satellite")),
            str(r.get("latitude")), str(r.get("longitude")),
        ),
    )  # canonical order -> float summation is deterministic (F-19)
    seen: set[tuple] = set()

    for row in rows:
        counts["rows_in"] += 1
        day_time = _utc_day(row, warnings)
        if day_time is None:
            counts["rejected_invalid_time"] += 1
            continue
        day, hhmm = day_time
        fam = _family(str(row.get("source", "")))
        if fam is None:
            counts["rejected_unknown_source"] += 1
            continue
        counts[f"rows_in_{fam}"] += 1
        sat = str(row.get("satellite", "")).strip()
        src_l = str(row.get("source", "")).strip().lower()
        accepted = (fam == "modis" and sat.lower() == "aqua") or (
            fam == "viirs" and "snpp" in src_l
        )
        if not accepted:
            counts["excluded_platform_v1"] += 1  # e.g. Terra / NOAA-20 — disclosed, not blended
            continue
        try:
            lat = _num(row.get("latitude"), "latitude")
            lon = _num(row.get("longitude"), "longitude")
            frp = _num(row.get("frp_mw"), "frp_mw")
        except MatchError:
            counts["rejected_bad_numeric"] += 1
            continue
        if frp < 0:
            counts["rejected_negative_frp"] += 1
            continue
        daynight = _norm_daynight(row.get("daynight", ""))
        if daynight is None:
            counts["rejected_unknown_daynight"] += 1
            continue
        key = _dedupe_key(row, day, hhmm, lat, lon)
        if key in seen:
            raise MatchError(
                "exact duplicate observation reached C-02 (B-04 guarantees dedupe; "
                f"resolve upstream): {key}"
            )
        seen.add(key)
        cell = assign_cell(lon, lat, bbox)
        if cell is None:
            counts["outside_aoi_cells"] += 1  # cell centroid outside bbox (F-4) — disclosed
            continue

        unit_key = (cell, day, daynight, fam, sat)
        unit = units.setdefault(unit_key, {
            "aoi_id": aoi_id, "cell_id": cell, "date": day, "daynight": daynight,
            "family": fam, "source": str(row.get("source")).strip(),
            "satellite": str(row.get("satellite")).strip(),
            "version": str(row.get("version", "")).strip(),
            "detection_count": 0, "frp_sum_mw": 0.0, "frp_max_mw": 0.0,
            "scan_values": [], "conf_low": 0, "conf_nominal": 0, "conf_high": 0,
            "conf_unknown": 0,
        })
        unit["detection_count"] += 1
        unit["frp_sum_mw"] += frp
        unit["frp_max_mw"] = max(unit["frp_max_mw"], frp)
        scan = row.get("scan")
        if scan not in (None, ""):
            try:
                unit["scan_values"].append(float(scan))
            except (TypeError, ValueError):
                warnings.add("nonnumeric_scan_ignored")
        conf = _norm_conf_class(
            row.get("confidence_class", row.get("confidence_raw", row.get("confidence")))
        )
        if conf:
            unit[f"conf_{conf}"] += 1
        counts["rows_aggregated"] += 1

    out_units = []
    for unit in sorted(units.values(), key=lambda u: (u["date"], u["cell_id"], u["daynight"], u["family"])):
        scans = unit.pop("scan_values")
        unit["mean_scan"] = round(sum(scans) / len(scans), 6) if scans else None
        unit["frp_sum_mw"] = round(unit["frp_sum_mw"], 6)
        unit["frp_max_mw"] = round(unit["frp_max_mw"], 6)
        out_units.append(unit)

    summary = {
        "protocol_version": PROTOCOL_VERSION, "aoi_id": aoi_id, "bbox": bbox,
        "counts": dict(counts), "units_per_sensor": len(out_units),
        "reference_sensor": _REFERENCE_SENSOR, "target_sensor": _TARGET_SENSOR,
        "warnings": sorted(warnings),
        "note": "FRP-sum = aggregate of sampled radiative-power observations (MW); "
                "not energy, not burned area, not a fire count",
    }
    return out_units, summary


# ------------------------------------------------------------------ mask + pairs
def load_retrieval_mask(mask_rows: list[dict], aoi_id: str) -> tuple[dict, dict]:
    """(family, date) -> status map for this AOI. Schema violations hard-fail."""
    if not mask_rows:
        raise MatchError("retrieval mask: no rows received (needed to tell gaps from zeros)")
    present = set(mask_rows[0])
    missing = REQUIRED_MASK_COLUMNS - present
    if missing:
        raise MatchError(f"retrieval mask: missing columns {sorted(missing)}")
    statuses: dict[tuple[str, str], set[str]] = defaultdict(set)
    dropped = 0
    for row in mask_rows:
        if str(row.get("aoi_id", "")).strip() != aoi_id:
            dropped += 1
            continue
        status = str(row.get("status", "")).strip().lower()
        if status not in RETRIEVAL_STATUSES:
            raise MatchError(f"retrieval mask: unknown status {status!r} — contract violation")
        fam = _family(str(row.get("source", "")))
        if fam is None:
            raise MatchError(f"retrieval mask: unrecognized source {row.get('source')!r}")
        try:
            day = _date.fromisoformat(str(row.get("date", "")).strip())
        except ValueError as exc:
            raise MatchError(f"retrieval mask: bad date {row.get('date')!r}") from exc
        statuses[(fam, day.isoformat())].add(status)
    conflicts = {k: v for k, v in statuses.items() if len(v & RETRIEVED_STATUSES) and (v - RETRIEVED_STATUSES)}
    if conflicts:
        raise MatchError(f"retrieval mask: ambiguous mixed statuses per family/date — {conflicts}")
    family_status = {
        k: ("retrieved" if v & RETRIEVED_STATUSES else next(iter(v)))
        for k, v in statuses.items()
    }
    return family_status, {"mask_rows_for_aoi": len(mask_rows) - dropped, "mask_rows_other_aoi": dropped}


def build_matched_pairs(
    units: list[dict], family_status: dict, aoi_id: str, aoi_cells: list[str]
) -> tuple[list[dict], list[dict], dict]:
    """Pair per-sensor units into (cell, date, daynight) comparison rows (F-6).

    MEMORY CONTRACT (scale guard, full-era safe): only SIGNAL-BEARING rows are
    materialized (matched_signal / one_sided / missing_retrieval). Zero-filled
    cells-days are represented COMPACTLY as one row per (date, daynight) with
    n_zero_cells — every zero-fill row is identical (0,0) except cell_id, so
    this is a lossless representation (full era: ~16M rows -> ~5.3k rows;
    materializing them as dicts was the 10 GB memory blow-up). Consumers:
    baselines/harmonize ingest the compact table and expand it as WEIGHTS, which
    is mathematically identical to duplicated rows in weighted OLS.

    Coverage semantics:
    - Dates where BOTH families were retrieved: every (cell, day/night) in the
      AOI counts; cell-days without detections are TRUE ZEROS (F-6) — counted,
      not dropped (survivorship bias avoided), not materialized per cell.
    - Dates where only ONE family was retrieved: rows exist only where the
      retrieved side has signal (state missing_retrieval, reason recorded).
    - One-sided signal is retained with a flag and excluded from fitting.
    """
    grouped: dict[tuple, dict] = defaultdict(dict)
    for unit in units:
        grouped[(unit["cell_id"], unit["date"], unit["daynight"])][unit["family"]] = unit

    dates_both, dates_partial = [], []
    dates_both_set = set()
    for day in sorted({day_ for (_fam, day_) in family_status}):
        modis_status = family_status.get(("modis", day), "not_requested")
        viirs_status = family_status.get(("viirs", day), "not_requested")
        if modis_status == "retrieved" and viirs_status == "retrieved":
            dates_both.append(day)
            dates_both_set.add(day)
        elif modis_status == "retrieved" or viirs_status == "retrieved":
            dates_partial.append((day, modis_status, viirs_status))

    def pair_row(cell: str, day: str, daynight: str) -> dict:
        sides = grouped.get((cell, day, daynight), {})
        row: dict = {"aoi_id": aoi_id, "cell_id": cell, "date": day, "daynight": daynight}
        present, signal = {}, {}
        for fam in ("modis", "viirs"):
            # aggregate_units already filtered to the v1 platforms (Aqua MODIS,
            # S-NPP VIIRS), so units keyed by family are exactly those sensors.
            status = family_status.get((fam, day), "not_requested")
            unit = sides.get(fam)
            present[fam] = status == "retrieved"  # collapsed value from load_retrieval_mask
            value = unit["frp_sum_mw"] if unit else (0.0 if present[fam] else None)
            signal[fam] = bool(value)  # > 0
            row[f"{fam}_status"] = status
            row[f"{fam}_frp_sum_mw"] = value
            row[f"{fam}_detection_count"] = unit["detection_count"] if unit else (0 if present[fam] else None)
            row[f"{fam}_frp_max_mw"] = unit["frp_max_mw"] if unit else (0.0 if present[fam] else None)
            row[f"{fam}_mean_scan"] = unit["mean_scan"] if unit else None
            row[f"{fam}_satellite"] = unit["satellite"] if unit else None
        if present["modis"] and present["viirs"]:
            if signal["modis"] and signal["viirs"]:
                row["state"], row["fitting_eligible"], row["flags"] = ST_MATCHED_SIGNAL, True, []
            elif signal["modis"] != signal["viirs"]:
                side = "modis" if signal["modis"] else "viirs"
                row["state"], row["fitting_eligible"] = ST_ONE_SIDED, False
                row["flags"] = [f"one_sided:{side}"]  # retained, excluded from fitting (F-6)
            else:
                row["state"], row["fitting_eligible"], row["flags"] = ST_MATCHED_ZERO, True, []
        elif present["modis"] or present["viirs"]:
            missing = "viirs" if present["modis"] else "modis"
            reason = family_status.get((missing, day), "not_requested")
            row["state"], row["fitting_eligible"] = ST_MISSING_RETRIEVAL, False
            row["flags"] = [f"missing_retrieval:{missing}:{reason}"]
        else:
            row["state"], row["fitting_eligible"], row["flags"] = ST_NOT_RETRIEVED, False, []
        return row

    pairs: list[dict] = []
    zero_fill: list[dict] = []
    zero_cells_total = 0
    stray_rows = 0  # detections on dates the mask says failed/unavailable — data/mask inconsistency
    for day in dates_both:
        for daynight in ("day", "night"):
            n_signal_cells = 0
            for cell in aoi_cells:  # deterministic (south->north, west->east) order
                sides = grouped.get((cell, day, daynight), {})
                has_signal = any(
                    (fam in sides and sides[fam]["frp_sum_mw"] > 0)
                    for fam in ("modis", "viirs")
                )
                if has_signal:
                    n_signal_cells += 1
                    pairs.append(pair_row(cell, day, daynight))
            n_zero_cells = len(aoi_cells) - n_signal_cells
            if n_zero_cells:
                zero_fill.append({"date": day, "daynight": daynight, "n_zero_cells": n_zero_cells})
                zero_cells_total += n_zero_cells
    for day, modis_status, viirs_status in dates_partial:
        retrieved_fam = "modis" if modis_status == "retrieved" else "viirs"
        for (cell, unit_day, daynight), sides in sorted(grouped.items()):
            if unit_day != day or day in dates_both_set:
                continue
            if set(sides) - {retrieved_fam}:
                stray_rows += 1  # detections exist for a side the mask says failed
                continue
            unit = sides[retrieved_fam]
            if unit["frp_sum_mw"] <= 0:
                continue  # no signal: the gap lives in the mask, not a pair row
            pairs.append(pair_row(cell, day, daynight))

    stats = {
        "zero_filled_cells": zero_cells_total,
        "zero_fill_days": len(zero_fill),
        "stray_rows_on_nonretrieved_date": stray_rows,
        "memory_note": "zero-fill represented compactly (one count per date/daynight) — "
                       "lossless: every zero-fill row is (0,0) except cell_id",
    }
    return pairs, zero_fill, stats


def run(
    detections: list[dict],
    mask_rows: list[dict],
    aoi_id: str,
    bbox_west: float, bbox_south: float, bbox_east: float, bbox_north: float,
    delivered_ranges: dict | None = None,
) -> dict:
    """Full C-02 step: units + matched pairs + summary (the C-03/C-04 input).

    delivered_ranges (optional): {family: (min_date, max_date)} actually covered
    by the delivered rows. Mask dates outside a delivered range are dropped with
    an explicit disclosure — otherwise a full-era mask over a compact fixture
    would fabricate matched_zero pairs for dates whose detections were never
    delivered (F-9: zeros may only come from verified retrievals).
    """
    units, summary = aggregate_units(detections, bbox_west, bbox_south, bbox_east, bbox_north, aoi_id)
    family_status, mask_info = load_retrieval_mask(mask_rows, aoi_id)
    summary["mask"] = mask_info
    if delivered_ranges:
        clipped = 0
        for fam, (lo, hi) in delivered_ranges.items():
            for key in [k for k in family_status if k[0] == fam]:
                day = key[1]
                if (lo and day < lo) or (hi and day > hi):
                    family_status.pop(key)
                    clipped += 1
        if clipped:
            summary["warnings"] = sorted(set(summary["warnings"]) | {"mask_clipped_to_delivered_window"})
            summary["mask"]["mask_dates_clipped_to_delivered"] = clipped
    aoi_cells = aoi_cell_ids(validate_bbox(bbox_west, bbox_south, bbox_east, bbox_north))
    pairs, zero_fill, pair_stats = build_matched_pairs(units, family_status, aoi_id, aoi_cells)
    states = defaultdict(int)
    for pair in pairs:
        states[pair["state"]] += 1
    states["matched_zero"] = pair_stats["zero_filled_cells"]  # compact, not materialized
    summary["matched_pairs"] = len(pairs) + pair_stats["zero_filled_cells"]
    summary["pair_states"] = dict(sorted(states.items()))
    summary["fitting_eligible_pairs"] = sum(1 for p in pairs if p["fitting_eligible"]) \
        + pair_stats["zero_filled_cells"]
    summary.update(pair_stats)
    return {"units": units, "pairs": pairs, "zero_fill": zero_fill, "summary": summary}


def write_outputs(result: dict, out_dir: str | Path) -> dict:
    """CSV primary (parquet when pyarrow is pinned). Returns written paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, rows in (("units_per_sensor", result["units"]),
                       ("matched_pairs", result["pairs"]),
                       ("zero_fill_days", result.get("zero_fill", []))):
        path = out_dir / f"{name}.csv"
        if rows:
            columns = list(rows[0])
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        else:
            path.write_text("")
        paths[name] = str(path)
    summary_path = out_dir / "match_summary.json"
    summary_path.write_text(json.dumps(result["summary"], indent=2, sort_keys=True))
    paths["summary"] = str(summary_path)
    return paths


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI for B-05 swap-in
    """python3 -m pipeline.match --input detections.csv --mask mask.csv
       --aoi-id riau --bbox 100.8,-1.9,103.4,0.2 --out data/processed/riau"""
    import argparse

    parser = argparse.ArgumentParser(description="C-02 matched overlap aggregates")
    parser.add_argument("--input", required=True, nargs="+",
                        help="B-04 normalized detections (csv/parquet); one path per source")
    parser.add_argument("--mask", required=True, help="retrieval mask csv (aoi_id,source,date,status)")
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--bbox", required=True, help="west,south,east,north")
    parser.add_argument("--out", default=None, help="output dir (default data/processed/<aoi-id>)")
    args = parser.parse_args(argv)
    west, south, east, north = (float(part) for part in args.bbox.split(","))
    detections: list[dict] = []
    for path in args.input:
        detections.extend(read_table(path))
    delivered_ranges = {}
    for fam in ("modis", "viirs"):
        days = sorted(
            str(r.get("acq_date") or str(r.get("acq_datetime_utc", ""))[:10]).strip()
            for r in detections
            if _family(str(r.get("source", ""))) == fam
        )
        days = [d for d in days if len(d) == 10 and d[4] == "-"]
        if days:
            delivered_ranges[fam] = (days[0], days[-1])
    mask_rows = read_table(args.mask)
    result = run(detections, mask_rows, args.aoi_id, west, south, east, north,
                 delivered_ranges=delivered_ranges or None)
    out_dir = args.out or f"data/processed/{args.aoi_id}"
    paths = write_outputs(result, out_dir)
    print(json.dumps({"summary": result["summary"], "outputs": paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
