"""C-03 contract test — EmberLine PROTO-C01-v0.9 (pipeline/baselines.py).

Core question: does B1 fit on TRAINING years only, with the frozen split, honest
support gating and N/A policies? Synthetic pairs have known answers; the real
Riau fixture must return an explicit insufficient_data (its overlap is 15 days).

Run standalone:  python tests/test_baseline_leakage.py
Run under pytest: python -m pytest tests/test_baseline_leakage.py -q
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import baselines  # noqa: E402

R_TRUE = 1.25  # the "true" MODIS/VIIRS ratio planted in the synthetic world

MONTH_DAYS = [(f"{m:02d}", f"{d:02d}") for m, d in
              [(1, 5), (1, 20), (2, 9), (2, 23), (3, 7), (3, 21), (4, 3), (4, 17),
               (5, 6), (5, 26), (6, 4), (6, 24), (7, 8), (7, 28), (8, 11), (8, 31),
               (9, 9), (9, 25), (10, 3), (10, 23), (11, 6), (11, 26), (12, 10), (12, 30)]]

REAL_PAIRS = Path(__file__).resolve().parents[1] / "data/processed/riau/c02/matched_pairs.csv"


def pair(year: str, month: str, day: str, modis: float, viirs: float,
         state: str = "matched_signal", eligible: str = "true", daynight: str = "day"):
    return {
        "aoi_id": "synthetic", "cell_id": "R0C1000", "date": f"{year}-{month}-{day}",
        "daynight": daynight, "modis_status": "retrieved", "viirs_status": "retrieved",
        "modis_frp_sum_mw": modis, "viirs_frp_sum_mw": viirs,
        "state": state, "fitting_eligible": eligible,
    }


def year_rows(year: str, modis_scale: float = 1.0) -> list[dict]:
    """FIXTURE_SYNTHETIC: 24 days/year — 16 signal days + 8 zero days, all
    both-retrieved and fitting-eligible. Test years get inflated MODIS so an
    all-data ratio would differ from the training-only ratio (leakage detector)."""
    rows = []
    for i, (m, d) in enumerate(MONTH_DAYS):
        if i % 3 == 2:  # 8 zero days: real zeros, still eligible pairs
            rows.append(pair(year, m, d, 0.0, 0.0, state="matched_zero"))
        else:  # 16 signal days
            modis = (10.0 + i * 3.7) * modis_scale
            rows.append(pair(year, m, d, round(modis, 4), round(modis / R_TRUE, 4)))
    return rows


def write_pairs(rows: list[dict]) -> str:
    tmp = Path(tempfile.mkdtemp(prefix="c03_test_")) / "matched_pairs.csv"
    import csv
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return str(tmp)


def run_all_checks() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # -- 1. B1 recovers the planted ratio from TRAINING years only -------------
    rows = []
    for year in ("2018", "2019", "2020"):                 # train years (<= 2020-10-08)
        rows += year_rows(year)
    for year in ("2021", "2022", "2023", "2024", "2025"):  # test years, MODIS +50%
        rows += year_rows(year, modis_scale=1.5)
    result = baselines.run(write_pairs(rows), tempfile.mkdtemp(prefix="c03_out_"), "synthetic")
    manifest = result["manifest"]
    outcome = manifest["outcome"]
    check("B1 fit succeeded on synthetic multi-year data", outcome.get("status") == "ok",
          f"got {outcome}")
    check("B1 ratio recovers the planted training-only ratio",
          outcome.get("B1_ratio") == round(R_TRUE, 8),
          f"got {outcome.get('B1_ratio')} (leakage would distort it)")
    fit_inputs = outcome.get("B1_fit_inputs", {})
    check("frozen split applied: train years exactly 2018-2020",
          fit_inputs.get("train_years") == ["2018", "2019", "2020"],
          f"got {fit_inputs.get('train_years')}")
    # The split is DATE-based (train <= 2020-10-08): 2020 dates after that line
    # belong to the held-out era — exactly why "years" never move after fitting.
    check("held-out era is date-based: includes late-2020 dates, never fitted",
          fit_inputs.get("test_years") == ["2020", "2021", "2022", "2023", "2024", "2025"]
          and fit_inputs.get("train_dates_eligible_pairs_only") is True)
    # independent recomputation of r from the recorded training inputs:
    recomputed = round(fit_inputs["train_sum_modis_mw"] / fit_inputs["train_sum_viirs_mw"], 8)
    check("recorded fit inputs recompute to the published ratio (audit trail)",
          recomputed == outcome["B1_ratio"])

    # -- 2. one-sided signal excluded from fitting (F-6) -----------------------
    rows_leak = rows + [pair("2019", "7", "15", 999999.0, 1.0, state="one_sided", eligible="false")]
    result2 = baselines.run(write_pairs(rows_leak), tempfile.mkdtemp(), "synthetic")
    check("one-sided rows (ineligible) do not move B1",
          result2["manifest"]["outcome"]["B1_ratio"] == outcome["B1_ratio"])
    check("one-sided rows still retained in the AOI-day record",
          any(b["modis_frp_sum_mw"] > 900000 for b in result2["aoi_days"]))

    # -- 3. honest insufficient support (F-9b) ---------------------------------
    result3 = baselines.run(write_pairs(year_rows("2019")), tempfile.mkdtemp(), "synthetic")
    check("single eligible year -> explicit insufficient_data, no model",
          result3["manifest"]["outcome"]["status"] == "insufficient_data"
          and "B1_ratio" not in result3["manifest"]["outcome"])

    # -- 4. zero-denominator N/A policy (F-15), via the defensive guard --------
    # Natural pair states can never produce a positive MODIS sum with a zero
    # VIIRS sum (matched_signal needs both > 0) — so the guard is exercised
    # directly on fit_and_predict with a pathological upstream table.
    degenerate = [
        {"date": "2018-01-05", "daynight": "day", "modis_frp_sum_mw": 5.0,
         "viirs_frp_sum_mw": 0.0, "both_retrieved": True, "any_fitting_eligible": True},
        {"date": "2019-01-05", "daynight": "day", "modis_frp_sum_mw": 5.0,
         "viirs_frp_sum_mw": 0.0, "both_retrieved": True, "any_fitting_eligible": True},
        {"date": "2021-01-05", "daynight": "day", "modis_frp_sum_mw": 5.0,
         "viirs_frp_sum_mw": 0.0, "both_retrieved": True, "any_fitting_eligible": True},
    ]
    outcome4 = baselines.fit_and_predict(degenerate, {"2018", "2019", "2021"})
    check("zero VIIRS training sum -> N/A reason, never infinity or fabricated zero",
          outcome4["status"] == "insufficient_data" and "N/A" in outcome4["reason"],
          f"got {outcome4}")

    # -- 5. B0 naive splice on overlap days = raw VIIRS (F-12) -----------------
    sample = next(b for b in result["aoi_days"] if b["both_retrieved"])
    check("B0 value equals raw VIIRS on post-transition overlap days",
          sample["B0_naive_splice_mw"] == sample["viirs_frp_sum_mw"]
          and sample["source_flag"] == "overlap_raw_viirs")

    # -- 6. eligibility report is inspectable ----------------------------------
    check("year eligibility report exposes fraction + signal days",
          all({"retrieval_fraction", "signal_days", "eligible"} <= set(y)
              for y in manifest["year_eligibility"]))

    # -- 7. REAL Riau file: status consistent with F-9b support (either era) -----
    # The real file evolved: compact fixture (15-day overlap) -> insufficient_data;
    # full era (14.5 y) -> ok. The INVARIANT is what matters: a fit exists iff
    # the support gate passes — a fake fit on thin support is forbidden both ways.
    if REAL_PAIRS.exists():
        result5 = baselines.run(str(REAL_PAIRS), tempfile.mkdtemp(), "riau")
        m5 = result5["manifest"]
        eligible = set(m5["eligible_years"])
        n_train = len({y for y in eligible if y <= baselines.TRAIN_END})
        n_test = len({y for y in eligible if y >= baselines.TEST_START[:4]})
        supported = (n_train >= baselines.MIN_TRAIN_YEARS and n_test >= baselines.MIN_TEST_YEARS)
        status = m5["outcome"]["status"]
        check("real Riau file: status ok iff F-9b support passes (no fake fit either way)",
              (status == "ok") == supported,
              f"status={status}, train_years={n_train}, test_years={n_test}")
    else:
        check("real Riau file present for the honesty check", False,
              f"{REAL_PAIRS} missing — run the C-02 swap-in first")

    # -- 8. schema drift hard-fails ---------------------------------------------
    try:
        bad = pair("2018", "1", "5", 1.0, 1.0)
        del bad["fitting_eligible"]
        baselines.run(write_pairs([bad]), tempfile.mkdtemp(), "synthetic")
        check("pairs schema drift hard-fails with actionable message", False)
    except baselines.BaselineError as exc:
        check("pairs schema drift hard-fails with actionable message",
              "missing" in str(exc) and "fitting_eligible" in str(exc))

    return checks


def _report(checks: list[tuple[str, bool, str]]) -> int:
    failed = [(n, d) for n, ok, d in checks if not ok]
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("CONTRACT VIOLATION — C-03 diverges from PROTO-C01-v0.9.")
        return 1
    print("C-03 scaffold holds: B0/B1 frozen-split + leakage discipline verified.")
    return 0


def test_baseline_leakage():  # pytest entry point
    failed = [(n, d) for n, ok, d in run_all_checks() if not ok]
    assert not failed, f"C-03 contract violations: {failed}"


if __name__ == "__main__":
    sys.exit(_report(run_all_checks()))
