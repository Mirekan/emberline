"""C-01 protocol contract test — EmberLine PROTO-C01-v0.9.

Verifies that the frozen protocol configs actually enforce the decisions written
in docs/method.md. A failure means the protocol documents and the machine
contract have diverged BEFORE any fitting — fix the config or the doc, never
silently relax the check.

Run standalone:  python tests/test_protocol_contract.py
Run under pytest: python -m pytest tests/test_protocol_contract.py -q
(no pytest in this environment yet — D-01 pins dependencies)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
GRID_PATH = ROOT / "config" / "grid.yaml"
PARAMS_PATH = ROOT / "config" / "params.yaml"

REQUIRED_METRICS = [
    "mean_log_ratio_bias", "smape", "mape_zero_actual_excluded",
    "pearson_daily", "spearman_daily", "pearson_weekly", "spearman_weekly",
    "log_space_r2", "ks_statistic", "wasserstein_distance",
    "calendar_pattern_correlation", "interval_coverage_empirical",
]

REQUIRED_MANIFEST_FIELDS = [
    "run_id", "git_sha", "created_utc", "aoi_bbox_date_range", "sources",
    "input_sha256", "params_hash", "train_years", "test_years",
    "metrics_path", "library_versions", "seeds",
]


def _load(path: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text())


def load_contracts() -> tuple[dict, dict]:
    return _load(GRID_PATH), _load(PARAMS_PATH)


def run_all_checks(grid: dict, p: dict) -> list[tuple[str, bool, str]]:
    """Return list of (check_name, passed, detail)."""
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        checks.append((name, bool(cond), detail))

    # -- identity / status --------------------------------------------------
    check("protocol version consistent across configs",
          grid.get("protocol_version") == p.get("protocol_version"),
          f"grid={grid.get('protocol_version')} params={p.get('protocol_version')}")
    check("status is DRAFT_FOR_REVIEW or FROZEN",
          p.get("status") in {"DRAFT_FOR_REVIEW", "FROZEN"}, p.get("status", ""))

    # -- sensors (F-1, F-2, F-3) --------------------------------------------
    s = p["sensors"]
    check("reference sensor is Aqua MODIS", s["reference_sensor"] == "aqua_modis")
    check("VIIRS platform S-NPP carries explicit PROVISIONAL marker",
          s["viirs_platform"] == "snpp_viirs" and s["viirs_platform_status"] == "PROVISIONAL_DEC1")
    check("exact source strings are a decision-needed marker, not invented",
          "PENDING" in str(s["exact_source_strings"]))
    check("Terra and NOAA-20/21 excluded in v1",
          set(s["excluded_in_v1"]) == {"terra_modis", "noaa20_viirs", "noaa21_viirs"})
    m = p["metric_policy"]
    check("FRP-sum is the only target metric",
          m["target_metric"] == "frp_sum" and m["frp_units"] == "MW")
    check("FRP-sum label discipline enforced",
          "aggregate_of_sampled" in m["frp_sum_meaning"]
          and "fire_count" in m["forbidden_claims"][0])

    # -- grid & time (F-4, F-5) ----------------------------------------------
    g = grid["grid"]
    check("grid cell size frozen at 0.1 deg", g["cell_size_deg"] == 0.1)
    check("assignment by centroid, no rounding", "centroid" in g["assignment"]
          and "forbidden" in g["assignment"])
    check("antimeridian-crossing boxes rejected",
          grid["aoi_limits"]["antimeridian_crossing"].startswith("rejected"))
    check("bbox cap 5 deg", grid["aoi_limits"]["bbox_cap_deg"] == 5.0)
    check("no area correction in v1", g["area_correction_v1"] == "none")
    t = grid["time_policy"]
    check("UTC daily bins, no timezone conversion",
          "UTC" in t["daily_bin"] and t["timezone_conversions"] == "none")
    check("day/night preserved; overpass class defined",
          t["daynight_preserved"] is True and "daynight" in t["overpass_class"])

    # -- confidence & dedupe (F-7, F-8) --------------------------------------
    c = p["confidence_filters"]
    check("MODIS confidence >= 30 (nominal+high)", c["modis"]["keep_min_numeric"] == 30)
    check("VIIRS low-confidence excluded",
          c["viirs"]["keep_classes"] == ["n", "h"])
    check("unknown confidence excluded & counted, never promoted",
          "exclude_and_count" in c["unknown_policy"] and c["original_values_retained"] is True)
    d = p["dedupe"]
    check("dedupe is exact-row identity per source key",
          d["method"] == "exact_row_identity_per_source_key")
    check("coordinate rounding to dedupe forbidden",
          d["coordinate_rounding"] == "forbidden")
    check("both sensor keys defined with required fields",
          all(k in d["keys"][s2] for s2 in ("modis", "viirs")
              for k in ("source", "satellite", "version", "acq_date_utc",
                        "acq_time_utc", "latitude", "longitude", "daynight")))

    # -- missingness & support (F-9, F-9b) ------------------------------------
    miss = p["missingness"]
    check("four missingness states defined",
          len(miss["four_states"]) == 4 and miss["zero_fill_failures"] == "forbidden")
    sup = p["support"]
    check("minimum support carries PROVISIONAL marker (DEC-2)",
          sup["status"] == "PROVISIONAL_DEC2")
    check("support thresholds written (0.90 coverage, 10 signal days)",
          sup["training_year_min_paired_retrieval_fraction"] == 0.90
          and sup["training_year_min_modis_signal_days"] == 10)
    check("fitting requires >=2 training years and >=1 test year",
          sup["fitting_requires"] == {"min_training_years": 2, "min_test_years": 1})
    check("one-sided signal retained, excluded from fitting, never deleted",
          "retained_with_flag" in sup["one_sided_signal"]
          and "excluded_from_fitting" in sup["one_sided_signal"])

    # -- split & training-only law (F-10, F-11) -------------------------------
    sp = p["split"]
    check("split is contiguous earliest ~60% of eligible years",
          sp["method"].startswith("contiguous_earliest") and sp["train_fraction"] == 0.6
          and sp["shuffle"] is False)
    to = p["training_only"]
    check("training-only law lists every learned step",
          len(to["learned_steps"]) == 9)
    check("held-out use for fitting/calibration/selection/tuning forbidden",
          to["heldout_use_for_fitting_calibration_selection_tuning"] == "forbidden")

    # -- methods (F-12) --------------------------------------------------------
    mth = p["methods"]
    check("B0 naive splice defined without correction",
          mth["b0_naive_splice"]["correction"] == "none")
    check("B1 ratio fit on training matched cell-days only",
          "training" in mth["b1_global_ratio"]["definition"])
    b2 = mth["b2_primary"]
    check("B2 is the monotone log-space form from the guide",
          "log1p(S_modis)" in b2["form"] and "log1p(S_viirs)" in b2["form"]
          and "n_viirs" in b2["form"])
    check("B2 monotonicity constraints b>=0, c>=0",
          b2["monotone_constraints"] == {"b": ">=0", "c": ">=0"})
    check("B2 back-transform uses training-only smearing",
          "smearing" in b2["back_transform"])
    check("method variant selection via training folds only",
          b2["variant_selection"] == "training_internal_folds_only")
    check("quantile correction omitted in v1 with recorded deviation",
          mth["quantile_correction"]["v1"] == "omitted"
          and mth["quantile_correction"]["deviation_id"] == "DEV-S03")
    check("all methods evaluated on identical held-out rows",
          mth["identical_heldout_rows_all_methods"] is True)

    # -- uncertainty (F-13) -----------------------------------------------------
    u = p["uncertainty"]
    check("nominal 80% interval target", u["nominal_target"] == 0.8)
    check("AOI intervals calibrated at AOI-daily level (no summed cell bounds)",
          u["calibration_level"] == "aoi_daily"
          and u["sum_of_cell_bounds_for_aoi_interval"] == "forbidden")
    check("bounds finite, ordered, nonnegative",
          u["bounds"] == {"finite": True, "ordered": True, "nonnegative": True})
    check("extrapolation flag defined; held-out coverage measured",
          "extrapolation_flag" in u and u["held_out_coverage_measured_and_reported"] is True)

    # -- source policy (F-14) ----------------------------------------------------
    spol = p["source_policy"]
    check("pre-VIIRS era = observed Aqua reference; VIIRS era = mapped estimate",
          spol["pre_viirs_era"] == "observed_aqua_reference"
          and spol["viirs_era"].startswith("mapped_viirs_estimate"))
    check("no sensor blending; explicit gaps otherwise",
          spol["blending_or_day_by_day_switching"] == "forbidden"
          and spol["otherwise"] == "explicit_gap_with_reason")
    check("no Terra/worldwide claims from Aqua-only model",
          "forbidden" in spol["terra_or_worldwide_claims_from_aqua_model"])

    # -- metrics (F-15) -----------------------------------------------------------
    met = p["metrics"]
    check("all required metrics configured",
          set(REQUIRED_METRICS).issubset(set(met["required"])),
          f"missing: {set(REQUIRED_METRICS) - set(met['required'])}")
    check("N/A policy: never infinity, never fabricated zero",
          "N/A" in met["na_policy"] and "never infinity" in met["na_policy"]
          and "never fabricated zero" in met["na_policy"])
    check("daily-vs-weekly primary rule pre-registered",
          "pre-registered" in met["daily_vs_weekly_primary_rule"])
    check("LOYO summary required; MODIS = reference not truth",
          met["leave_one_year_out"] == "training_internal_summary_required"
          and met["modis_role"] == "reference_measurement_not_ground_truth")

    # -- stress tests (F-16) -------------------------------------------------------
    st = p["stress_tests"]
    check("at least 3 predetermined pseudo-transitions per AOI",
          st["count_min_per_aoi"] >= 3 and "predetermined" in st["selection_rule"])
    check("±14-day window fully inside held-out with >=70% paired retrieval",
          st["window_days"] == {"before": 14, "after": 14}
          and st["window_requirements"]["fully_inside_heldout"] is True
          and st["window_requirements"]["min_paired_retrieval_fraction"] == 0.7)
    check("continued MODIS is the truth reference",
          "truth" in st["comparison"] and "continued MODIS" in st["comparison"]["truth"])
    check("no manufactured p-values; failures stay visible",
          "no manufactured p-values" in st["changepoint_significance"]
          and "failed_or_deferred" in st["invalid_or_short_windows"])

    # -- index & calendar (F-17, F-18) ----------------------------------------------
    ix = p["index"]
    check("index = log1p(harmonized)/log1p(training P95 reference denominator)",
          "log1p" in ix["formula"] and "p95_training" in ix["formula"]
          and ix["denominator"] == "frozen_from_training")
    check("non-positive denominator -> index unavailable, raw units shown",
          "unavailable" in ix["denominator_nonpositive_or_missing"])
    cal = p["calendar"]
    check("366-position month/day template; true dates preserved",
          cal["positions"] == 366 and cal["true_dates_in_exports"] is True)
    check("non-leap Feb 29 = N/A, never missing data",
          cal["feb29_non_leap"].startswith("not_applicable"))
    check("critical windows at 75th percentile, >=3-day runs, Dec-Jan wrap",
          cal["critical_windows"]["threshold_percentile_of_smoothed_curve"] == 75
          and cal["critical_windows"]["min_run_days"] == 3
          and cal["critical_windows"]["dec_jan_wrapping"] is True)
    check("eligible-year rule (>=60% coverage) and provisional active-year rule",
          "60%" in cal["eligible_year_rule"]
          and cal["active_year_rule"]["status"] == "PROVISIONAL_DEC3")
    check("missing years never inactive; sparse records labeled insufficient",
          cal["missing_years"] == "never_counted_as_inactive"
          and cal["sparse_records_label"].startswith("insufficient"))

    # -- provenance & secrets (F-19) --------------------------------------------------
    pr = p["provenance"]
    check("run manifest carries all required provenance fields",
          set(REQUIRED_MANIFEST_FIELDS).issubset(set(pr["run_manifest_fields"])),
          f"missing: {set(REQUIRED_MANIFEST_FIELDS) - set(pr['run_manifest_fields'])}")
    check("deterministic seeds required", pr["seeds_deterministic"] is True)
    check("no MAP_KEY or credentials anywhere in config",
          "forbidden" in pr["map_key_or_credentials_in_code_configs_logs_manifests_docs"]
          and "MAP_KEY" not in PARAMS_PATH.read_text().replace(
              "map_key_or_credentials", ""))

    # -- deviations & decisions --------------------------------------------------------
    devs = {dv["id"] for dv in p["deviations"]}
    check("scope deviations S-01/S-02/S-03/S-06 recorded, pending A-02",
          {"DEV-S01", "DEV-S02", "DEV-S03", "DEV-S06"}.issubset(devs)
          and all(dv["approval"] == "PENDING_A02" for dv in p["deviations"]))
    decs = {dc["id"] for dc in p["decisions_pending"]}
    check("decision markers DEC-1..DEC-5 recorded",
          decs == {"DEC-1", "DEC-2", "DEC-3", "DEC-4", "DEC-5"})

    return checks


def _report(checks: list[tuple[str, bool, str]]) -> int:
    failed = [(n, d) for n, ok, d in checks if not ok]
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        line = f"[{mark}] {name}"
        if detail and not ok:
            line += f"  ({detail})"
        print(line)
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("CONTRACT VIOLATION — fix configs/docs before any fitting.")
        return 1
    print("Protocol contract holds: configs match PROTO-C01-v0.9 frozen decisions.")
    return 0


def test_protocol_contract():  # pytest entry point
    if yaml is None:
        import pytest
        pytest.skip("PyYAML not installed")
    grid, params = load_contracts()
    failed = [(n, d) for n, ok, d in run_all_checks(grid, params) if not ok]
    assert not failed, f"protocol contract violations: {failed}"


if __name__ == "__main__":
    grid, params = load_contracts()
    sys.exit(_report(run_all_checks(grid, params)))
