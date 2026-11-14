"""C-02 contract test — EmberLine PROTO-C01-v0.9 (pipeline/grid.py + pipeline/match.py).

ALL data below is FIXTURE_SYNTHETIC: handcrafted rows with hand-computed expected
values. Per guide C-02/B-06: synthetic fixtures test edge cases ONLY — they never
support demo results and never substitute for B-05 real overlap evidence.

Run standalone:  python tests/test_grid_match.py
Run under pytest: python -m pytest tests/test_grid_match.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import grid, match  # noqa: E402

# FIXTURE_SYNTHETIC — tiny AOI around 0.1°-aligned cells west of Sumatra.
BBOX = {"west": 100.0, "south": 0.0, "east": 100.2, "north": 0.2}


def det(**kw):
    """FIXTURE_SYNTHETIC detection row builder (fallback time columns)."""
    base = {
        "source": "MODIS_SP", "satellite": "Aqua", "version": "6.1",
        "latitude": "0.05", "longitude": "100.05", "daynight": "D",
        "acq_date": "2023-09-12", "acq_time": "1330", "frp_mw": "10.0",
        "confidence_class": "n", "scan": "1.0", "track": "1.0",
    }
    base.update(kw)
    return base


def mask(source="MODIS_SP", date="2023-09-12", status="retrieved_rows", aoi="fixture"):
    return {"aoi_id": aoi, "source": source, "date": date, "status": status}


def build(rows, masks, aoi="fixture"):
    return match.run(rows, masks, aoi, BBOX["west"], BBOX["south"], BBOX["east"], BBOX["north"])


def unit_of(result, cell="R0C1000", date="2023-09-12", daynight="day", family="modis"):
    for unit in result["units"]:
        if (unit["cell_id"], unit["date"], unit["daynight"], unit["family"]) == (cell, date, daynight, family):
            return unit
    return None


def pair_of(result, cell="R0C1000", date="2023-09-12", daynight="day"):
    for pair in result["pairs"]:
        if (pair["cell_id"], pair["date"], pair["daynight"]) == (cell, date, daynight):
            return pair
    return None


def run_all_checks() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # -- F-4 grid geometry ---------------------------------------------------
    try:
        grid.validate_bbox(175.0, 0.0, -175.0, 1.0)
        check("antimeridian-crossing bbox rejected", False)
    except grid.GridError:
        check("antimeridian-crossing bbox rejected", True)
    try:
        grid.validate_bbox(100.0, 0.0, 105.5, 1.0)  # > 5 deg cap
        check("bbox cap 5 deg enforced", False)
    except grid.GridError:
        check("bbox cap 5 deg enforced", True)
    check("half-open cell: lon exactly on east edge belongs east",
          grid.cell_indices(100.1, 0.05)[1] == 1001)
    check("floor handles southern hemisphere (Pantanal/NSW)",
          grid.cell_indices(100.05, -12.34) == (-124, 1000))
    check("cell id deterministic", grid.cell_id(-124, 1000) == "R-124C1000")
    check("AOI cell set: centroid rule keeps 2x2 for a 0.2x0.2 aligned bbox",
          grid.aoi_cell_ids(BBOX) == ["R0C1000", "R0C1001", "R1C1000", "R1C1001"])
    # Non-aligned bbox: the frozen F-4 centroid rule diverges from plain
    # coordinate clipping and that divergence is deliberate, so test it exactly.
    bbox2 = grid.validate_bbox(100.04, -0.06, 100.16, 0.06)
    check("non-aligned bbox: cell set follows centroid rule",
          grid.aoi_cell_ids(bbox2) == ["R-1C1000", "R-1C1001", "R0C1000", "R0C1001"])
    check("F-4 divergence: detection outside bbox but cell centroid inside -> included",
          grid.assign_cell(100.03, 0.01, bbox2) == "R0C1000"
          and grid.assign_cell(100.19, 0.01, bbox2) == "R0C1001")
    check("cell whose centroid lies outside bbox -> excluded",
          grid.assign_cell(100.21, 0.01, bbox2) is None)
    check("centroid clipping includes interior cell",
          grid.assign_cell(100.04, 0.04, BBOX) == "R0C1000")

    # -- aggregation + time binning ------------------------------------------
    result = build(
        [
            det(frp_mw="30.5", scan="1.2", confidence_class="h"),
            det(frp_mw="9.5", acq_time="1345", scan="2.0", longitude="100.06"),
            det(satellite="Aqua", source="MODIS_SP", daynight="N", frp_mw="5.0",
                acq_time="0130", latitude="0.05", longitude="100.05"),
            det(satellite="N", source="VIIRS_SNPP_SP", frp_mw="20.0",
                longitude="100.05", confidence_class="h"),
        ],
        [mask("MODIS_SP"), mask("VIIRS_SNPP_SP")],
    )
    modis_day = unit_of(result)
    check("same UTC day aggregates together (13:30 + 13:45)",
          modis_day and modis_day["detection_count"] == 2
          and abs(modis_day["frp_sum_mw"] - 40.0) < 1e-9
          and abs(modis_day["frp_max_mw"] - 30.5) < 1e-9,
          f"got {modis_day}")
    check("mean_scan averages present scans only",
          modis_day and abs((modis_day["mean_scan"] or 0) - 1.6) < 1e-9)
    check("day/night classes stay separate (F-5)",
          unit_of(result, daynight="night") is not None
          and unit_of(result, daynight="night")["detection_count"] == 1)
    viirs_unit = unit_of(result, family="viirs")
    check("VIIRS aggregated separately from MODIS (F-6)",
          viirs_unit and viirs_unit["detection_count"] == 1
          and abs(viirs_unit["frp_sum_mw"] - 20.0) < 1e-9)
    check("B-04 reality: VIIRS rows carry satellite='N', accepted via source string (DEC-1)",
          viirs_unit and viirs_unit["satellite"] == "N")
    pair = pair_of(result)
    check("matched pair: both signal -> fitting-eligible",
          pair and pair["state"] == match.ST_MATCHED_SIGNAL and pair["fitting_eligible"])

    # -- states: one-sided vs zero vs missing retrieval (F-6/F-9) -------------
    result2 = build(
        [
            # date A: MODIS signal, VIIRS retrieved-empty -> one_sided (excluded)
            det(acq_date="2023-09-12"),
            det(satellite="N", source="VIIRS_SNPP_SP", acq_date="2023-09-12",
                latitude="0.15", longitude="100.15", frp_mw="3.0"),
            # date B: MODIS signal, VIIRS failed that date -> missing_retrieval
            det(acq_date="2024-02-29", acq_time="1330"),
            # date C: both retrieved-empty at a cell -> matched_zero pair
        ],
        [
            mask("MODIS_SP", "2023-09-12"), mask("VIIRS_SNPP_SP", "2023-09-12"),
            mask("MODIS_SP", "2024-02-29"), mask("VIIRS_SNPP_SP", "2024-02-29", "failed"),
            mask("MODIS_SP", "2023-06-01", "retrieved_empty"),
            mask("VIIRS_SNPP_SP", "2023-06-01", "retrieved_empty"),
        ],
    )
    p_a = pair_of(result2, date="2023-09-12")  # R0C1000: MODIS signal, VIIRS retrieved-empty
    check("one-sided signal retained but excluded from fitting",
          p_a and p_a["state"] == match.ST_ONE_SIDED and not p_a["fitting_eligible"]
          and "one_sided:modis" in p_a["flags"],
          f"got {p_a}")
    p_a2 = pair_of(result2, cell="R1C1001", date="2023-09-12")  # VIIRS signal, MODIS zero
    check("one-sided viirs side flagged likewise",
          p_a2 and p_a2["state"] == match.ST_ONE_SIDED and "one_sided:viirs" in p_a2["flags"],
          f"got {p_a2}")
    p_b = pair_of(result2, date="2024-02-29")
    check("failed retrieval -> missing_retrieval, not zero",
          p_b and p_b["state"] == match.ST_MISSING_RETRIEVAL
          and not p_b["fitting_eligible"]
          and p_b["viirs_frp_sum_mw"] is None and "missing_retrieval:viirs:failed" in p_b["flags"],
          f"got {p_b}")
    p_c = pair_of(result2, date="2023-06-01")
    zf = {(r["date"], r["daynight"]): int(r["n_zero_cells"]) for r in result2["zero_fill"]}
    check("both retrieved-empty -> COMPACT zero-fill (lossless), counted fitting-eligible",
          "matched_zero" in result2["summary"]["pair_states"]
          and result2["summary"]["pair_states"]["matched_zero"] == 14
          and zf.get(("2023-06-01", "day")) == 4 and zf.get(("2023-06-01", "night")) == 4
          and zf.get(("2023-09-12", "day")) == 2 and zf.get(("2023-09-12", "night")) == 4,
          f"got zf={zf} states={result2['summary']['pair_states']}")
    check("leap day 2024-02-29 groups as a normal UTC day",
          p_b is not None and p_b["date"] == "2024-02-29")

    # -- platform discipline (S-01) ------------------------------------------
    result3 = build(
        [
            det(),  # Aqua
            det(satellite="Terra", source="MODIS_SP"),  # excluded in v1, disclosed
            det(satellite="N", source="VIIRS_SNPP_SP", frp_mw="4.0"),  # SNPP
            det(satellite="NOAA-20", source="VIIRS_NOAA20_SP", frp_mw="4.0"),  # excluded
        ],
        [mask("MODIS_SP"), mask("VIIRS_SNPP_SP")],
    )
    excluded = result3["summary"]["counts"].get("excluded_platform_v1", 0)
    check("Terra/NOAA-20 counted as excluded_in_v1, never blended",
          excluded == 2
          and unit_of(result3, family="modis")["detection_count"] == 1
          and unit_of(result3, family="viirs")["detection_count"] == 1)

    # -- defensive validation -------------------------------------------------
    try:
        build([det(), det()], [mask()])  # exact duplicate rows
        check("exact duplicate reaching C-02 hard-fails (B-04 contract)", False)
    except match.MatchError:
        check("exact duplicate reaching C-02 hard-fails (B-04 contract)", True)
    result4 = build([det(frp_mw="-3.0"), det(acq_time="2400")], [mask()])
    counts = result4["summary"]["counts"]
    check("negative FRP and invalid time rejected and counted, not silently dropped",
          counts.get("rejected_negative_frp") == 1 and counts.get("rejected_invalid_time") == 1)
    try:
        match.run([det()], [], "fixture", 100.0, 0.0, 100.2, 0.2)  # no mask
        check("missing retrieval mask hard-fails (cannot tell gaps from zeros)", False)
    except match.MatchError:
        check("missing retrieval mask hard-fails (cannot tell gaps from zeros)", True)
    try:
        match.validate_input_columns([{"latitude": "0", "longitude": "1"}], "x")
        check("schema drift hard-fails with actionable message", False)
    except match.MatchError as exc:
        check("schema drift hard-fails with actionable message",
              "missing required columns" in str(exc))

    # -- determinism (F-19) ----------------------------------------------------
    rows = []
    for i in range(5):
        lat_i = str(0.01 + i * 0.02)  # distinct coordinates -> distinct observations,
        rows.append(det(frp_mw=str(1.0 + i / 7), latitude=lat_i))  # all inside cell R0
        rows.append(det(satellite="N", source="VIIRS_SNPP_SP",
                        frp_mw=str(2.0 + i / 11), latitude=lat_i))
    masks = [mask("MODIS_SP"), mask("VIIRS_SNPP_SP")]
    first = build([dict(r) for r in rows], [dict(m) for m in masks])
    second = build([dict(r) for r in reversed(rows)], [dict(m) for m in masks])
    check("same input in any order -> identical units + compact zero-fill (deterministic)",
          first["units"] == second["units"] and first["pairs"] == second["pairs"]
          and first["zero_fill"] == second["zero_fill"])

    # -- honest bookkeeping ----------------------------------------------------
    result5 = build([det(latitude="0.5", longitude="100.05")], [mask()])
    check("drops disclosed in summary (outside-AOI counted, not hidden)",
          result5["summary"]["counts"].get("outside_aoi_cells") == 1
          and result5["summary"]["counts"].get("rows_aggregated", 0) == 0)
    check("summary carries FRP label discipline",
          "not a fire count" in result5["summary"]["note"])

    return checks


def _report(checks: list[tuple[str, bool, str]]) -> int:
    failed = [(n, d) for n, ok, d in checks if not ok]
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("CONTRACT VIOLATION — C-02 scaffold diverges from PROTO-C01-v0.9.")
        return 1
    print("C-02 scaffold holds: grid/matching match the frozen protocol (fixtures only).")
    return 0


def test_grid_match():  # pytest entry point
    failed = [(n, d) for n, ok, d in run_all_checks() if not ok]
    assert not failed, f"C-02 contract violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(run_all_checks()))
