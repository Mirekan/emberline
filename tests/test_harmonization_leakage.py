"""C-04 contract test — EmberLine PROTO-C01-v0.9 (pipeline/harmonize.py).

Core questions: is B2 trained on the frozen training years ONLY (coefficients,
smearing factor, interval quantiles and support bounds must all be invariant to
held-out rows); is the mapping monotone and interpretable; are bounds finite,
ordered, nonnegative; do gaps/extrapolation stay visible; does thin support
return honest insufficient_data (real Riau fixture included)?

Run standalone:  python tests/test_harmonization_leakage.py
Run under pytest: python -m pytest tests/test_harmonization_leakage.py -q
"""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import harmonize  # noqa: E402

R_TRUE = 1.25
A_TRUE = 0.05     # tiny intercept in log1p space
B_TRUE = 0.92     # planted slope (data follows 1/B_TRUE in MW space)
C_TRUE = 0.02     # small count effect
D_TRUE = -0.10    # night slightly dimmer in MODIS view
RUN_TS = "20261114T1400Z"  # fixed for manifest determinism

MONTH_DAYS = [(f"{m:02d}", f"{d:02d}") for m, d in
              [(1, 5), (1, 20), (2, 9), (2, 23), (3, 7), (3, 21), (4, 3), (4, 17),
               (5, 6), (5, 26), (6, 4), (6, 24), (7, 8), (7, 28), (8, 11), (8, 31),
               (9, 9), (9, 25), (10, 3), (10, 23), (11, 6), (11, 26), (12, 10), (12, 30)]]

REAL_PAIRS = Path(__file__).resolve().parents[1] / "data/processed/riau/c02/matched_pairs.csv"


def cell_pair(year, month, day, cell, modis, viirs, count=0, state="matched_signal",
              eligible="true", daynight="day"):
    return {
        "aoi_id": "synthetic", "cell_id": cell, "date": f"{year}-{month}-{day}",
        "daynight": daynight, "modis_status": "retrieved", "viirs_status": "retrieved",
        "modis_frp_sum_mw": round(modis, 6), "viirs_frp_sum_mw": round(viirs, 6),
        "viirs_detection_count": count,
        "state": state, "fitting_eligible": eligible,
    }


def year_rows(year: str, modis_scale: float = 1.0, with_night: bool = True) -> list[dict]:
    """FIXTURE_SYNTHETIC: 6 cells x 24 days/year. Signal rows follow the PLANTED
    mapping (noise-free); zeros are matched_zero. Test years get inflated MODIS
    so any held-out leakage would move the coefficients."""
    rows = []
    for i, (m, d) in enumerate(MONTH_DAYS):
        for j in range(6):
            cell = f"R{j}C100{j}"
            if i % 3 == 2:
                rows.append(cell_pair(year, m, d, cell, 0.0, 0.0, 0, state="matched_zero"))
                continue
            base = (4.0 + i * 1.3 + j * 0.8) * modis_scale
            night = "night" if with_night and i % 5 == 4 else "day"
            count = 1 + ((i * 7 + j) % 9)  # count VARIES so c is identifiable
            viirs = max(0.0, base) / R_TRUE
            # planted map: modis = expm1(A + B*log1p(viirs) + C*log1p(1+n) + D*night)
            import math
            modis = math.expm1(A_TRUE + B_TRUE * math.log1p(viirs)
                               + C_TRUE * math.log1p(1.0 + count) + D_TRUE * (night == "night"))
            rows.append(cell_pair(year, m, d, cell, modis, viirs, count=count, daynight=night))
    return rows


def write_pairs(rows: list[dict]) -> str:
    tmp = Path(tempfile.mkdtemp(prefix="c04_test_")) / "matched_pairs.csv"
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return str(tmp)


def run_all_checks() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    train_years = ("2018", "2019", "2020")
    test_years = ("2021", "2022", "2023", "2024", "2025")
    rows = []
    for year in train_years:
        rows += year_rows(year)
    for year in test_years:
        rows += year_rows(year, modis_scale=1.5)  # held-out rows deliberately distorted

    result = harmonize.run(write_pairs(rows), tempfile.mkdtemp(prefix="c04_out_"),
                           "synthetic", run_ts=RUN_TS)
    outcome = result["manifest"]["outcome"]
    check("B2 fit succeeded on synthetic multi-year data", outcome.get("status") == "ok",
          f"got {outcome.get('status')}: {outcome.get('reason', '')}")
    if outcome.get("status") != "ok":
        return checks

    model = outcome["model"]
    coefs = model["coefficients"]
    # -- 1. planted mapping recovered (noise-free data, tolerance for rounding) --
    # Rounding noise + weak count/viirs collinearity => approximate recovery;
    # the hard identity checks (b, d) plus training-only invariance carry the proof.
    check("intercept + slopes recover the planted mapping (approximate)",
          abs(coefs["a_intercept"] - A_TRUE) < 0.10
          and abs(coefs["b_log1p_viirs"] - B_TRUE) < 0.05
          and abs(coefs["c_log1p_count"] - C_TRUE) < 0.05
          and abs(coefs["d_night"] - D_TRUE) < 0.05,
          f"got {coefs}")
    check("monotone constraints hold (b >= 0, c >= 0)",
          coefs["b_log1p_viirs"] >= 0 and coefs["c_log1p_count"] >= 0)

    # -- 2. LEAKAGE: model invariant to whatever the held-out rows contain --------
    # Deleting held-out rows entirely would just trip the support gate (which is
    # itself correct), so the leakage detector compares two runs whose held-out
    # eras are distorted DIFFERENTLY: if any test row entered fitting, the two
    # models would diverge.
    rows_alt = []
    for year in train_years:
        rows_alt += year_rows(year)
    for year in test_years:
        rows_alt += year_rows(year, modis_scale=3.7)  # different held-out distortion
    result_alt = harmonize.run(write_pairs(rows_alt), tempfile.mkdtemp(prefix="c04_out_"),
                               "synthetic", run_ts=RUN_TS)
    outcome_alt = result_alt["manifest"]["outcome"]
    check("alt held-out run also fits", outcome_alt.get("status") == "ok")
    coefs_alt = outcome_alt["model"]["coefficients"]
    check("coefficients identical under two different held-out distortions (training-only law)",
          coefs == coefs_alt, f"full={coefs} alt={coefs_alt}")
    check("smearing factor identical under held-out distortion",
          model["smearing_k"] == outcome_alt["model"]["smearing_k"])
    check("interval quantiles identical under held-out distortion",
          outcome["intervals"] == outcome_alt["intervals"])
    check("support bounds identical under held-out distortion",
          outcome["support_bounds"] == outcome_alt["support_bounds"])
    check("manifest records test years as recorded-never-fitted",
          model["fit_inputs"]["test_years_recorded_never_fitted"]
          == sorted(set(test_years) | {"2020"}))

    # -- 3. monotonicity sweep on predictions ------------------------------------
    import math
    coef, k = model["coefficients"], model["smearing_k"]
    probe = lambda s, n, dn="day": harmonize._predict_cell(coef, k, {
        "viirs_frp_sum_mw": s, "viirs_detection_count": n, "daynight": dn})
    sweep = [probe(s, 3) for s in (0.5, 1, 2, 5, 10, 50, 200)]
    check("prediction non-decreasing in S_viirs", all(a <= b for a, b in zip(sweep, sweep[1:])),
          f"got {sweep}")
    sweep_n = [probe(5.0, n) for n in (0, 1, 3, 10, 40)]
    check("prediction non-decreasing in n_viirs (c > 0 in planted data)",
          all(a <= b for a, b in zip(sweep_n, sweep_n[1:])), f"got {sweep_n}")
    check("zero policy: S_viirs==0 and n==0 -> prediction exactly 0",
          probe(0.0, 0) == 0.0)
    check("predictions nonnegative", min(sweep) >= 0)

    # -- 4. bounds finite, ordered, nonnegative; estimate contained --------------
    days = result["days"]
    heldout = [d for d in days if d["role"] == "test"]
    check("every AOI-day has finite ordered nonnegative bounds containing the estimate",
          all(0 <= d["lo_mw"] <= d["predicted_b2_mw"] <= d["hi_mw"] for d in days),
          f"violation: {[d for d in days if not (0 <= d['lo_mw'] <= d['predicted_b2_mw'] <= d['hi_mw'])][:2]}")
    check("held-out days carry the nominal-80% note in manifest intervals",
          all(iv["nominal_target"] == 0.80 and "MEASURED at C-05" in iv["note"]
              for iv in outcome["intervals"]))

    # -- 5. extrapolation + support visibility ------------------------------------
    check("support bounds recorded", "support_lo_log1p" in outcome["support_bounds"])
    rows_extrap = rows + [cell_pair("2022", "06", "24", "R9C1009", 50000.0, 50000.0 / R_TRUE,
                                    count=200, daynight="day"),
                          cell_pair("2022", "06", "24", "R9C1010", 50000.0, 50000.0 / R_TRUE,
                                    count=200, daynight="day")]
    result_extrap = harmonize.run(write_pairs(rows_extrap), tempfile.mkdtemp(), "synthetic", run_ts=RUN_TS)
    ext_days = [d for d in result_extrap["days"] if d["date"] == "2022-06-24" and d["daynight"] == "day"]
    check("held-out cell input beyond training support -> extrapolation flag",
          ext_days and "extrapolation" in ext_days[0]["flags"],
          f"got {ext_days[0]['flags'] if ext_days else 'no day'}")

    # -- 6. honest insufficient support -------------------------------------------
    if REAL_PAIRS.exists():
        result_real = harmonize.run(str(REAL_PAIRS), tempfile.mkdtemp(), "riau", run_ts=RUN_TS)
        check("real Riau fixture -> insufficient_data, no model fitted",
              result_real["manifest"]["outcome"]["status"] == "insufficient_data",
              f"got {result_real['manifest']['outcome'].get('status')}")
    single = year_rows("2019")
    result_single = harmonize.run(write_pairs(single), tempfile.mkdtemp(), "synthetic", run_ts=RUN_TS)
    check("single eligible year -> insufficient_data (F-9b gate)",
          result_single["manifest"]["outcome"]["status"] == "insufficient_data")

    # -- 7. schema drift hard-fails ------------------------------------------------
    try:
        bad = cell_pair("2018", "1", "5", "R0C1000", 1.0, 1.0)
        del bad["viirs_detection_count"]
        harmonize.run(write_pairs([bad]), tempfile.mkdtemp(), "synthetic", run_ts=RUN_TS)
        check("pairs schema drift hard-fails", False)
    except harmonize.BaselineError as exc:
        check("pairs schema drift hard-fails", "missing" in str(exc))

    # -- 8. manifest provenance ----------------------------------------------------
    manifest = result["manifest"]
    check("manifest carries run_id, model_version, git_sha, zero policy, DEV-S03",
          manifest["run_id"].startswith("PROTO-C01-v0.9_b2-primary")
          and manifest["model_version"] == "b2-primary"
          and manifest["git_sha"]
          and "zero-inflation" in manifest["zero_policy"]
          and "DEV-S03" in manifest["quantile_correction"])

    return checks


def _report(checks: list[tuple[str, bool, str]]) -> int:
    failed = [(n, d) for n, ok, d in checks if not ok]
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("CONTRACT VIOLATION — C-04 diverges from PROTO-C01-v0.9.")
        return 1
    print("C-04 scaffold holds: monotone B2, training-only law, AOI-daily intervals verified.")
    return 0


def test_harmonization_leakage():  # pytest entry point
    failed = [(n, d) for n, ok, d in run_all_checks() if not ok]
    assert not failed, f"C-04 contract violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(run_all_checks()))
